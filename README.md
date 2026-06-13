# py-ccm15

Python Library to access a Midea CCM15 data converter

This package provides an asynchronous interface to communicate with Midea CCM15 data converter modules. It allows you to control and monitor air conditioning units via the CCM15 gateway using Python.

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
from py_ccm15 import CCM15Client

async def main():
    client = CCM15Client(host="192.168.1.100", token="your_token_here")
    status = await client.get_status()
    print(status)

    await client.set_state(ac_mode="cool", fan_mode="auto", temperature=24)

asyncio.run(main())
```

## Requirements

- Python 3.7+
- httpx>=0.24.1
- xmltodict>=0.13.0

## Documentation

For full API reference and advanced usage, visit the [GitHub repository](https://github.com/ocalvo/py-ccm15).

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

