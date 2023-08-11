import unittest
from unittest.mock import patch, MagicMock
from ccm15 import CCM15Device, CCM15DeviceState, CCM15SlaveDevice

class TestCCM15(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ccm = CCM15Device("localhost", 8000)

    @patch("httpx.AsyncClient.get")
    async def test_get_status_async(self, mock_get) -> None:
        # Set up mock response
        mock_response = MagicMock()
        mock_response.text = """
        <response>
            <ac1>00000001020304</ac1>
            <ac2>00000005060708</ac2>
        </response>
        """
        mock_get.return_value = mock_response

        # Call method and check result
        state = await self.ccm.get_status_async()
        self.assertIsInstance(state, CCM15DeviceState)
        self.assertEqual(len(state.devices), 2)
        self.assertIsInstance(state.devices[0], CCM15SlaveDevice)
        self.assertIsInstance(state.devices[1], CCM15SlaveDevice)

    @patch("httpx.AsyncClient.get")
    async def test_async_set_state(self, mock_get):
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call method and check result
        result = await self.ccm.async_set_state(0, "state", 1)
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
