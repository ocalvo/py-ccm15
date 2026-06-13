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

    def test_all_fields_locked_and_negative_temp(self) -> None:
        """Decode every field with locks active and a sub-zero room temp.

        Byte layout (celsius): A8 74 16 8E 8A 78 C8
        b5 = 0x78 keeps the locked cool/heat temps and sets the fan/remote
        locks; b6 = 0xC8 (200) decodes as a signed -56.
        """
        device = CCM15SlaveDevice(bytes.fromhex("a874168e8a78c8"))
        self.assertTrue(device.is_celsius)
        self.assertEqual(21, device.locked_cool_temperature)
        self.assertEqual(20, device.locked_heat_temperature)
        self.assertEqual(3, device.locked_wind)
        self.assertEqual(2, device.locked_ac_mode)
        self.assertEqual(5, device.error_code)
        self.assertEqual(3, device.ac_mode)
        self.assertEqual(4, device.fan_mode)
        self.assertTrue(device.is_ac_mode_locked)
        self.assertEqual(17, device.temperature_setpoint)
        self.assertTrue(device.is_swing_on)
        self.assertTrue(device.fan_locked)
        self.assertTrue(device.is_remote_locked)
        self.assertEqual(-56, device.temperature)

    def test_locked_temps_cleared_when_flags_off(self) -> None:
        """b5 = 0x00 clears the locked cool/heat temps and the lock flags."""
        device = CCM15SlaveDevice(bytes.fromhex("a874168e8a0048"))
        self.assertEqual(0, device.locked_cool_temperature)
        self.assertEqual(0, device.locked_heat_temperature)
        self.assertFalse(device.fan_locked)
        self.assertFalse(device.is_remote_locked)
        self.assertEqual(72, device.temperature)

if __name__ == '__main__':
    unittest.main()
