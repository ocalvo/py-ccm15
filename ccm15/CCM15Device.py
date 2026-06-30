from __future__ import annotations

import time
import httpx
import xmltodict
from .CCM15DeviceState import CCM15DeviceState
from .CCM15ReturnCode import CCM15ReturnCode
from .CCM15SlaveDevice import CCM15SlaveDevice
from .TriState import TriState
from .const import (
    AC_MODE_OFF,
    BASE_URL,
    CONF_URL_CTRL,
    CONF_URL_STATUS,
    DEFAULT_STATE_TTL,
    DEFAULT_TIMEOUT,
    FAN_MODE_AUTO,
    FAN_MODE_OFF,
    PASSWORD_MASK,
    PASSWORD_XOR_KEY,
    RET_PATTERN,
    UTSXXX_MODULO,
)


class CCM15Device:
    def __init__(self, host: str, port: int, timeout = DEFAULT_TIMEOUT,
                 state_ttl = DEFAULT_STATE_TTL,
                 client: "httpx.AsyncClient | None" = None,
                 password: "str | None" = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        # Some CCM15 firmwares reject control commands unless the device
        # password is supplied. Pass the *configured* numeric password exactly
        # as shown on the controller's settings page (factory default
        # "123456"). The library applies the same obfuscation the controller's
        # web UI does (XOR with PASSWORD_XOR_KEY + utsxxx nonce) before putting
        # it on the wire, so callers never deal with the obfuscated value. When
        # None, no pwd parameter is sent.
        self.password = password
        # The CCM15 is a flaky embedded bridge: status.xml periodically times
        # out or returns a degraded body (empty, or every slot "-") for up to a
        # minute at a time, even while every AC is online. Cache the last read
        # that actually decoded devices and serve it for up to `state_ttl`
        # seconds so a transient dropout does not flap every entity to
        # unavailable. Set state_ttl to 0 to disable caching.
        self.state_ttl = state_ttl
        self._last_state = None
        self._last_good_monotonic = None
        # An httpx.AsyncClient can be passed in to avoid the library
        # constructing one inside an asyncio loop. Constructing an
        # AsyncClient synchronously loads the certifi CA bundle, which
        # asyncio detects as a blocking I/O call. Callers running on an
        # event loop (such as Home Assistant) should pass in a client that
        # was built off the loop.
        self._client = client
        # Only a client we build ourselves is ours to close. An injected
        # client is owned by the caller and must outlive this object, so
        # aclose() must never touch it.
        self._owns_client = client is None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def aclose(self) -> None:
        """Close the httpx client, but only if this object created it.

        An injected client is left untouched; its owner is responsible for
        closing it. Safe to call more than once.
        """
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "CCM15Device":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.aclose()

    async def _fetch_xml_data(self) -> str:
        url = BASE_URL.format(self.host, self.port, CONF_URL_STATUS)
        response = await self._get_client().get(url, timeout=self.timeout)
        return response.text

    async def _fetch_data(self) -> CCM15DeviceState:
        """Get the current status of all AC devices.

        Slots in the status.xml response are not guaranteed to be contiguous
        or to start at 0: a CCM15 can report empty ("-") slots before and
        between active units (e.g. a0-a3 empty, a4-a21 populated). Skip empty
        slots with `continue` instead of breaking on the first one, and derive
        the device index from the XML key so the true slot number is preserved
        end-to-end and `async_set_state` builds the correct slave bitmask.
        """
        str_data = await self._fetch_xml_data()
        doc = xmltodict.parse(str_data)
        data = doc["response"]
        ac_data = CCM15DeviceState(devices={})
        for ac_name, ac_binary in data.items():
            if ac_binary == "-":
                continue
            try:
                ac_index = int(str(ac_name).lstrip("aA"))
            except ValueError:
                continue
            try:
                bytesarr = bytes.fromhex(str(ac_binary).strip(","))
            except ValueError:
                continue
            ac_data.devices[ac_index] = CCM15SlaveDevice(bytesarr)
        return ac_data

    def _fresh_cached_state(self) -> CCM15DeviceState | None:
        """Return the last good state if it is still within the TTL, else None.

        Stamps every cached device's `age` with how many seconds old the data
        is, so a consumer can tell a cached read from a live one per device.
        """
        if (
            self.state_ttl
            and self._last_state is not None
            and self._last_good_monotonic is not None
        ):
            age = time.monotonic() - self._last_good_monotonic
            if age < self.state_ttl:
                for device in self._last_state.devices.values():
                    device.age = age
                return self._last_state
        return None

    async def get_status_async(self) -> CCM15DeviceState:
        """Return the current device state, tolerating transient dropouts.

        A poll that raises (timeout/connection error) or decodes to zero
        devices is treated as a transient dropout: the last state that did
        decode devices is returned instead, as long as it is younger than
        `state_ttl`. Once the cache ages past the TTL the real failure surfaces
        (the exception propagates, or an empty state is returned) so a device
        that is genuinely offline does eventually go unavailable.
        """
        try:
            state = await self._fetch_data()
        except Exception:
            cached = self._fresh_cached_state()
            if cached is not None:
                return cached
            raise

        if state.devices:
            self._last_state = state
            self._last_good_monotonic = time.monotonic()
            return state

        cached = self._fresh_cached_state()
        return cached if cached is not None else state

    async def async_test_connection(self) -> bool:
        """Test the connection to the CCM15 device."""
        url = BASE_URL.format(self.host, self.port, CONF_URL_STATUS)
        try:
            response = await self._get_client().get(url, timeout=self.timeout)
        except httpx.RequestError:
            return False
        return response.status_code == 200

    async def async_send_state(self, url: str) -> CCM15ReturnCode:
        """Send the url to set state to the ccm15 slave.

        Returns a :class:`CCM15ReturnCode`: ``OK`` when the controller accepted
        the command, ``WRONG_PASSWORD`` when it rejected the ``pwd`` parameter
        (``<ret>250</ret>``), or ``CONNECTION_ERROR`` on a non-OK HTTP status.
        """
        response = await self._get_client().get(url, timeout=self.timeout)
        if response.status_code not in (httpx.codes.OK, httpx.codes.FOUND):
            return CCM15ReturnCode.CONNECTION_ERROR
        return self._parse_return_code(response.text)

    @staticmethod
    def _parse_return_code(text: str) -> CCM15ReturnCode:
        """Map a ctrl.xml response body to a CCM15ReturnCode.

        The controller's web UI only treats ``<ret>250</ret>`` as an error
        (wrong password); any other code, or no ``<ret>`` at all, is an accepted
        command, so everything else maps to ``OK``.
        """
        match = RET_PATTERN.search(text or "")
        if match is None:
            return CCM15ReturnCode.OK
        try:
            return CCM15ReturnCode(int(match.group(1)))
        except ValueError:
            return CCM15ReturnCode.OK

    def _password_query(self) -> str:
        """Build the obfuscated `pwd`/`utsxxx` query prefix, or "" if no password.

        Mirrors the controller's pwdstr(): the configured numeric password is
        XORed with PASSWORD_XOR_KEY, cast to unsigned 32-bit, and paired with a
        utsxxx nonce (milliseconds modulo UTSXXX_MODULO).
        """
        if not self.password:
            return ""
        pwd = (int(self.password) ^ PASSWORD_XOR_KEY) & PASSWORD_MASK
        utsxxx = int(time.time() * 1000) % UTSXXX_MODULO
        return f"pwd={pwd}&utsxxx={utsxxx}&"

    @staticmethod
    def _fan_mode_for_command(ac_mode: int, fan_mode: int) -> int:
        """Return a runnable fan mode for the target HVAC command."""
        if ac_mode != AC_MODE_OFF and fan_mode == FAN_MODE_OFF:
            return FAN_MODE_AUTO
        return fan_mode

    async def async_set_state(self, ac_index: int, data) -> CCM15ReturnCode:
        """Set new target states.

        The controller addresses slaves with a 64-bit mask split across two
        parameters: ac0 for slots 0-31 and ac1 for slots 32-63 (matching the
        controller's own cmd_aclist() in midea.js). Previously the whole mask
        was written to ac0, which silently overflowed for slave indices >= 32
        and targeted the wrong unit (or nothing).

        Returns a :class:`CCM15ReturnCode` describing how the controller
        responded (see :meth:`async_send_state`).
        """
        if ac_index < 32:
            ac0 = 2 ** ac_index
            ac1 = 0
        else:
            ac0 = 0
            ac1 = 2 ** (ac_index - 32)
        pwd_part = self._password_query()
        fan_mode = self._fan_mode_for_command(data.ac_mode, data.fan_mode)
        url = BASE_URL.format(
            self.host,
            self.port,
            CONF_URL_CTRL
            + "?" + pwd_part
            + "ac0="
            + str(ac0)
            + "&ac1="
            + str(ac1)
            + "&mode=" + str(data.ac_mode)
            + "&fan=" + str(fan_mode)
            + "&temp=" + str(data.temperature_setpoint)
        )
        # Opt-in swing: only emit `sw` when the caller set a desired value.
        # UNSET (the default) leaves the command byte-for-byte unchanged, so
        # firmware that does not accept `sw` is unaffected.
        desired_swing = getattr(data, "desired_swing", TriState.UNSET)
        if isinstance(desired_swing, TriState) and desired_swing.is_set:
            url += "&sw=" + str(desired_swing.value)
        # Opt-in electric heater: same contract as swing. UNSET omits `ht`, so
        # firmware that does not accept the electric-heater parameter is
        # unaffected and polling never causes `ht` to start being sent.
        desired_heater = getattr(data, "desired_heater", TriState.UNSET)
        if isinstance(desired_heater, TriState) and desired_heater.is_set:
            url += "&ht=" + str(desired_heater.value)

        return await self.async_send_state(url)
