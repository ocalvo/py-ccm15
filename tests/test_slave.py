import unittest
from ccm15 import CCM15SlaveDevice

class TestCCM15SlaveDevice(unittest.TestCase):
    def test_swing_mode_on(self) -> None:
        """Test that the swing mode is on."""
        data = bytes.fromhex("00000041d2001a")
        device = CCM15SlaveDevice(data)
        self.assertTrue(device.is_swing_on)

    def test_swing_mode_off(self) -> None:
        """Test that the swing mode is off."""
        data = bytes.fromhex("00000041d0001a")
        device = CCM15SlaveDevice(data)
        self.assertFalse(device.is_swing_on)

    def test_temp_fan_mode(self) -> None:
        """Test that the swing mode is on."""
        data = bytes.fromhex("00000041d2001a")
        device = CCM15SlaveDevice(data)
        self.assertEqual(26, device.temperature)
        self.assertEqual(2, device.fan_mode)
        self.assertEqual(0, device.ac_mode)

    def test_fahrenheit(self) -> None:
        """Test that farenheith bit."""

        data = bytearray.fromhex("81000041d2001a")
        device = CCM15SlaveDevice(data)
        self.assertEqual(False, device.is_celsius)
        self.assertEqual(88, device.temperature_setpoint)
        self.assertEqual(0, device.locked_cool_temperature)
        self.assertEqual(0, device.locked_heat_temperature)

if __name__ == '__main__':
    unittest.main()
