# -*- coding: utf-8 -*-
from setuptools import setup

from setuptools import setup, find_packages

long_description = open("README.md").read()

setup(
    name="expipe-plugin-cinpla",
    packages=find_packages(),
    version='0.1',
    include_package_data=True,
    author="CINPLA",
    author_email="",
    maintainer="Mikkel Elle Lepperød",
    maintainer_email="m.e.lepperod@medisin.uio.no",
    platforms=['Linux', "Windows"],
    description="Plugins for the CINPLA lab",
    long_description=long_description
)
