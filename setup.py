import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="deluge-distributr",
    version="0.0.1",
    author="Andrew Cole",
    author_email="andrew.cole@illallangi.com",
    description="TODO: SET DESCRIPTION",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/illallangi/DelugeDistributr",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["deluge-distributr=deluge_distributr:__main__.main"],
    },
    install_requires=[
        "bencoding",
        "Click",
        "deluge-client",
        "loguru",
        "notifiers",
    ],
)
