from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="py_ccm15",
    version="0.1.1",
    author="Oscar Calvo",
    author_email="oscar@calvonet.com",
    description="A package to control Midea CCM15 data converter modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ocalvo/py-ccm15",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'httpx>=0.24.1',
        'xmltodict>=0.13.0',
        'aiohttp>=3.8.5'
    ]
)
