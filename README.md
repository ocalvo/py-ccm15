# py-ccm15

Python Library to access a Midea CCM15 data converter

This package provides an asynchronous interface to communicate with Midea CCM15 data converter modules. It allows you to control and monitor air conditioning units via the CCM15 gateway using Python.

The CCM15 — officially the [**Midea CCM-15 Central Controller**](https://mbt.midea.com/global/hvac-goods/midea-products-category/vrfs/vrf-controller/central-controller-ccm-15) — is a data converter that bridges Midea's RS-485 VRF bus to TCP/IP, exposing a small HTTP interface for monitoring and control of up to 64 indoor units.

## Features

- Read and set temperature
- Control fan mode and AC mode
- Async support for non-blocking operations
- Communicate with CCM15 over HTTP

## Installation

```bash
pip install py-ccm15
```

## Usage

```python
import asyncio
from ccm15 import CCM15Device

async def main():
    # host and port of the CCM15 gateway (default HTTP port is 80).
    # Optionally pass password="123456" for firmwares that require it.
    device = CCM15Device("192.168.1.100", 80)

    # Read the state of every AC slave, keyed by its slot index.
    state = await device.get_status_async()
    for index, ac in state.devices.items():
        print(index, ac.ac_mode, ac.fan_mode, ac.temperature, ac.temperature_setpoint)

    # Change a slave: mutate its decoded state and write it back.
    ac = state.devices[0]
    ac.ac_mode = 0                 # mode code (0 = cool — see PROTOCOL.md)
    ac.fan_mode = 0                # fan code (0 = auto)
    ac.temperature_setpoint = 24
    await device.async_set_state(0, ac)

asyncio.run(main())
```

> The importable package is `ccm15` (the PyPI distribution is `py-ccm15`). The
> CCM15 uses no token; the only optional auth is a `password=` for firmwares
> that require it. See [PROTOCOL.md](PROTOCOL.md) for the mode/fan codes.

## Requirements

- Python 3.7+
- httpx>=0.24.1
- xmltodict>=0.13.0

## Documentation

For full API reference and advanced usage, visit the [GitHub repository](https://github.com/ocalvo/py-ccm15).

## Protocol

The CCM15's HTTP interface (`status.xml` / `ctrl.xml`) and the per-slave status
byte layout are documented in detail in **[PROTOCOL.md](PROTOCOL.md)** — a
bit-level reverse-engineering reference for the wire format, including the
`ac0`/`ac1` slave mask, mode/fan codes, and the optional `pwd`/`sw`/`ht`
parameters.

## References

- [Midea CCM-15 Central Controller — official product page](https://mbt.midea.com/global/hvac-goods/midea-products-category/vrfs/vrf-controller/central-controller-ccm-15)
- [Home Assistant `ccm15` integration](https://www.home-assistant.io/integrations/ccm15/) — consumes this library
- **Where to buy:** the CCM15 / CCM-15 data converter is often available cheaply on [AliExpress](https://www.aliexpress.com/wholesale?SearchText=Midea+CCM15) (search "Midea CCM15")

## Contributing

Pull requests are welcome. If you find a bug or have a feature request, feel free to open an issue.

## Acknowledgements

The CCM15 wire protocol implemented here — the `status.xml` byte decoding and the
HVAC/fan mode command mappings — was originally derived from the
[houselabs/home-assistant-mideaccm](https://github.com/houselabs/home-assistant-mideaccm)
Home Assistant custom component (originally authored by Chao Shen). This library
re-implements that protocol as a standalone, async package. Thanks to the original
authors for reverse-engineering the controller protocol.

Thanks also to [daxingplay/home-assistant-midea-ccm15](https://github.com/daxingplay/home-assistant-midea-ccm15),
an independent CCM15 Home Assistant component whose `status.xml` decoding and
`ctrl.xml` command handling were a valuable second reference for validating this
library's wire protocol.

Special thanks to [Alexa (@Alexa-RR)](https://github.com/Alexa-RR), who captured
the controller's own `midea.js` from a live device and traced the protocol to
document the swing (`sw`, status byte 4 bit 1) and electric-heater (`ht`, status
byte 4 bit 0) parameters and their control-URL semantics. That work is the basis
for the opt-in swing/heater support and much of [PROTOCOL.md](PROTOCOL.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Made by [Oscar Calvo](https://github.com/ocalvo)

