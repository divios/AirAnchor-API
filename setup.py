import os
import subprocess

from setuptools import setup, find_packages


data_files = []

if os.path.exists("/etc/default"):
    data_files.append(
        ('/etc/default', ['packaging/systemd/dron-tp-api']))

if os.path.exists("/lib/systemd/system"):
    data_files.append(
        ('/lib/systemd/system',
         ['packaging/systemd/dron-tp-api.service']))

setup(
    name='dron-tp-api',
    version='1.0',
    description='Sawtooth Dron tp wrapper',
    author='divios',
    url='',
    packages=find_packages(),
    install_requires=[
        "sawtooth-sdk",
        "requests",
        "uvicorn",
        "fastapi",
        "cbor",
        "protobuf"
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'location-tp = dron-tp-api.app:main'
        ]
    })