#!/usr/bin/env python3
"""Setup script for KosXER - X11 Configuration Editor"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kosxer",
    version="0.1.0",
    author="KosXER Team",
    description="GUI editor for X11 configuration files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "kosxer=main:main",
        ],
    },
)
