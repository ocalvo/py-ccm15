"""Constants for the CCM15 library."""
import re

# HTTP endpoints.
BASE_URL = "http://{0}:{1}/{2}"
CONF_URL_STATUS = "status.xml"
CONF_URL_CTRL = "ctrl.xml"

# Defaults.
DEFAULT_TIMEOUT = 10
DEFAULT_STATE_TTL = 300

# Password obfuscation, mirroring the controller's own pwdstr() in midea.js.
# The on-wire `pwd` value is the configured numeric password XORed with a fixed
# magic key and cast to an unsigned 32-bit integer; a per-request `utsxxx`
# nonce (milliseconds modulo UTSXXX_MODULO) is appended. These values are
# otherwise undocumented and come from a midea.js capture (see PROTOCOL.md /
# Credits).
PASSWORD_XOR_KEY = 0x56789
PASSWORD_MASK = 0xFFFFFFFF
UTSXXX_MODULO = 1000

# The controller returns its status in a <ret> element of the ctrl.xml response.
RET_PATTERN = re.compile(r"<ret>\s*(-?\d+)\s*</ret>")
