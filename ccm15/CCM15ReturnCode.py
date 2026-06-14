"""Return codes for CCM15 control writes."""
from enum import IntEnum


class CCM15ReturnCode(IntEnum):
    """Outcome of a ``ctrl.xml`` control write.

    Non-negative values are the controller's own ``<ret>`` codes, as decoded by
    its web UI (``midea.js``). Negative values are synthetic: they cover
    outcomes the controller never assigns a code to (for example, the request
    not completing at the HTTP layer).
    """

    OK = 0
    """The controller accepted the command."""

    WRONG_PASSWORD = 250
    """The controller rejected the command: the ``pwd`` parameter was missing or
    did not match the configured device password."""

    CONNECTION_ERROR = -1
    """The request failed or returned a non-OK HTTP status; no ``<ret>`` code
    was received from the controller."""
