from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="py-ccm15",
    version="0.0.2",
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
    ]
)
