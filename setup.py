import setuptools
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setuptools.setup(
    name="fyta_cli",
    version="0.1",
    description="Python library to access the FYTA API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["aiohttp","asyncio","dataclasses","datetime","pytz","requests"],
    py_modules=["client","exceptions","fyta_connector"],
)
