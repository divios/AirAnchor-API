import os
import subprocess

from setuptools import setup, find_packages


data_files = []

if os.path.exists("/etc/default"):
    data_files.append(
        ('/etc/default', ['packaging/systemd/air-anchor-api']))

if os.path.exists("/lib/systemd/system"):
    data_files.append(
        ('/lib/systemd/system',
         ['packaging/systemd/air-anchor-api.service']))

setup(
    name='air_anchor_api',
    version='1.0',
    description='AirAnchorApi to interact with the blockchain',
    author='divios',
    url='',
    packages=find_packages(),
    install_requires=[
        "sawtooth-sdk",
        "requests",
        "uvicorn",
        "fastapi",
        "cbor",
        "colorlog",
        "pika",
        "pyrate_limiter",
        "protobuf==3.20.*"
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'air-anchor-api= air_anchor_api.app:main_wrapper'
        ]
    })