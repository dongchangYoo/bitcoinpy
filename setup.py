from setuptools import setup, find_packages

setup(
    name="bitcoinpy",
    version="0.1",
    packages=find_packages(),
    install_requires=["base58", "requests", "setuptools", "toml"]
)
