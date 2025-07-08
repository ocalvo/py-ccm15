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
- aiohttp>=3.8.5

## Documentation

For full API reference and advanced usage, visit the [GitHub repository](https://github.com/ocalvo/py-ccm15).

## Contributing

Pull requests are welcome. If you find a bug or have a feature request, feel free to open an issue.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Made by [Oscar Calvo](https://github.com/ocalvo)

