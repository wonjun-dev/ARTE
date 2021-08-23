#!/usr/bin/env python3
from setuptools import setup

from setuptools import setup

setup(
    name="arte-engine",
    version="0.0.1",
    packages=[
        "arte",
        "arte.data",
        "arte.indicator",
        "arte.indicator.impl",
        "arte.strategy",
        "arte.strategy.impl",
        "arte.system",
    ],
    install_requires=["ta-lib", "python-telegram-bot"],
)