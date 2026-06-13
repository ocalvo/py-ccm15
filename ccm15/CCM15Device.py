from __future__ import annotations

import time
import httpx
import xmltodict
import aiohttp
import asyncio
from .CCM15DeviceState import CCM15DeviceState
from .CCM15SlaveDevice import CCM15SlaveDevice

BASE_URL = "http://{0}:{1}/{2}"
CONF_URL_STATUS = "status.xml"
CONF_URL_CTRL = "ctrl.xml"
DEFAULT_TIMEOUT = 10
DEFAULT_STATE_TTL = 300

class CCM15Device:
    def __init__(self, host: str, port: int, timeout = DEFAULT_TIMEOUT,
                 state_ttl = DEFAULT_STATE_TTL):
        self.host = host
        self.port = port
        self.timeout = timeout
        # The CCM15 is a flaky embedded bridge: status.xml periodically times
        # out or returns a degraded body (empty, or every slot "-") for up to a
        # minute at a time, even while every AC is online. Cache the last read
        # that actually decoded devices and serve it for up to `state_ttl`
        # seconds so a transient dropout does not flap every entity to
        # unavailable. Set state_ttl to 0 to disable caching.
        self.state_ttl = state_ttl
        self._last_state = None
        self._last_good_monotonic = None

    async def _fetch_xml_data(self) -> str:
        url = BASE_URL.format(self.host, self.port, CONF_URL_STATUS)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=self.timeout)
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
        """Return the last good state if it is still within the TTL, else None."""
        if (
            self.state_ttl
            and self._last_state is not None
            and self._last_good_monotonic is not None
            and (time.monotonic() - self._last_good_monotonic) < self.state_ttl
        ):
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

    async def async_test_connection(self):
        """Test the connection to the CCM15 device."""
        url = f"http://{self.host}:{self.port}/{CONF_URL_STATUS}"
        try:
            async with aiohttp.ClientSession() as session, session.get(
                url, timeout = self.timeout
            ) as response:
                if response.status == 200:
                    return True
                return False
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def async_send_state(self, url: str) -> bool:
        """Send the url to set state to the ccm15 slave."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout = self.timeout)
            return response.status_code in (httpx.codes.OK, httpx.codes.FOUND)

    async def async_set_state(self, ac_index: int, data) -> bool:
        """Set new target states.

        The controller addresses slaves with a 64-bit mask split across two
        parameters: ac0 for slots 0-31 and ac1 for slots 32-63 (matching the
        controller's own cmd_aclist() in midea.js). Previously the whole mask
        was written to ac0, which silently overflowed for slave indices >= 32
        and targeted the wrong unit (or nothing).
        """
        if ac_index < 32:
            ac0 = 2 ** ac_index
            ac1 = 0
        else:
            ac0 = 0
            ac1 = 2 ** (ac_index - 32)
        url = BASE_URL.format(
            self.host,
            self.port,
            CONF_URL_CTRL
            + "?ac0="
            + str(ac0)
            + "&ac1="
            + str(ac1)
            + "&mode=" + str(data.ac_mode)
            +  "&fan=" + str(data.fan_mode)
            + "&temp=" + str(data.temperature_setpoint)
        )

        return await self.async_send_state(url)

