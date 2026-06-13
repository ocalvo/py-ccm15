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

class CCM15Device:
    def __init__(self, host: str, port: int, timeout = DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.timeout = timeout

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

    async def get_status_async(self) -> CCM15DeviceState:
        return await self._fetch_data()

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

