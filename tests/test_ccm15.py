import unittest
from unittest.mock import patch, MagicMock
from ccm15 import CCM15Device, CCM15DeviceState, CCM15SlaveDevice

class TestCCM15(unittest.TestCase):
    def setUp(self):
        self.ccm = CCM15Device("localhost", 8000)

    @patch("ccm15.httpx.AsyncClient.get")
    async def test_get_status_async(self, mock_get):
        # Set up mock response
        mock_response = MagicMock()
        mock_response.text = """
        <response>
            <ac1>01020304</ac1>
            <ac2>05060708</ac2>
        </response>
        """
        mock_get.return_value = mock_response

        # Call method and check result
        state = await self.ccm.get_status_async()
        self.assertIsInstance(state, CCM15DeviceState)
        self.assertEqual(len(state.devices), 2)
        self.assertIsInstance(state.devices[0], CCM15SlaveDevice)
        self.assertIsInstance(state.devices[1], CCM15SlaveDevice)

if __name__ == "__main__":
    unittest.main()
