#!/usr/bin/env python3
from setuptools import setup

setup(
    name="arte",
    version="0.0.1",
    packages=[
        "binance_f",
        "binance_f.impl",
        "binance_f.impl.utils",
        "binance_f.exception",
        "binance_f.model",
        "binance_f.base",
        "binance_f.constant",
        "arte",
        "arte.data",
        "arte.indicator",
        "arte.indicator.impl",
        "arte.strategy",
        "arte.strategy.impl",
        "arte.system",
    ],
    install_requires=[
        "requests",
        "python-telegram-bot",
        "apscheduler==3.6.3",
        "websocket-client",
        "urllib3",
        "tzlocal<3.0",
        # "ta-lib",
    ],
)
