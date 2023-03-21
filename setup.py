#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="pinnable",
    version="0.0.1",
    description=("Pinnable"),
    url="https://pinnable.xyz",
    author="Pinnable Dev Team",
    author_email="dev@planetable.xyz",
    install_requires=["pytest", "tornado", "requests", "rq"],
)
