import httpx
import xmltodict
from . import CCM15DeviceState

BASE_URL = "http://{0}:{1}/{2}"
CONF_URL_STATUS = "status.xml"
DEFAULT_TIMEOUT = 10

class CCM15Device:
    def __init__(self, host: str, port: int, timeout = DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._ac_devices = {}

    async def _fetch_xml_data(self) -> str:
        url = BASE_URL.format(self.host, self.port, CONF_URL_STATUS)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, self.timeout)
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
        if len(self._ac_devices) == 0:
            for ac_index in ac_data.devices:
                self._ac_devices[ac_index] = CCM15Climate(self.host, ac_index, self)
        return ac_data

    async def get_status_async(self) -> CCM15DeviceState:
        return await self._fetch_data()


