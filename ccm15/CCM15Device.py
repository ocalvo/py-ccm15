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
        """Get the current status of all AC devices."""
        str_data = await self._fetch_xml_data()
        doc = xmltodict.parse(str_data)
        data = doc["response"]
        ac_data = CCM15DeviceState(devices={})
        ac_index = 0
        for ac_name, ac_binary in data.items():
            if ac_binary == "-":
                break
            bytesarr = bytes.fromhex(ac_binary.strip(","))
            ac_slave = CCM15SlaveDevice(bytesarr)
            ac_data.devices[ac_index] = ac_slave
            ac_index += 1
        return ac_data

    async def get_status_async(self) -> CCM15DeviceState:
        return await self._fetch_data()

    async def async_test_connection(self):  # pragma: no cover
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

    async def async_send_state(self, url: str) -> bool:  # pragma: no cover
        """Send the url to set state to the ccm15 slave."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout = self.timeout)
            return response.status_code in (httpx.codes.OK, httpx.codes.FOUND)

    async def async_set_state(self, ac_index: int, data) -> bool:
        """Set new target states."""
        ac_id: int = 2**ac_index
        url = BASE_URL.format(
            self.host,
            self.port,
            CONF_URL_CTRL
            + "?ac0="
            + str(ac_id)
            + "&ac1=0"
            + "&mode=" + str(data.ac_mode)
            +  "&fan=" + str(data.fan_mode)
            + "&temp=" + str(data.temperature_setpoint)
        )

        return await self.async_send_state(url)

