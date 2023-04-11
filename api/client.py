import hashlib
import base64
import time
import random
import requests
import yaml
import cbor
import json

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch


def _sha512(data):
    return hashlib.sha512(data).hexdigest()


FAMILY_NAME = 'AirAnchor'
FAMILY_VERSION = '1.0'

LOCATION_KEY_ADDRESS_PREFIX = _sha512(
    FAMILY_NAME.encode('utf-8'))[:6]


def make_location_key_address(key, hash=None):
    prefix = LOCATION_KEY_ADDRESS_PREFIX + key[:6]
    
    if not hash:
        return prefix

    return prefix + hash[-58:]

def _get_private_key_as_signer(priv_path):
    context = create_context('secp256k1')
    crypto_factory = CryptoFactory(context=context)
    
    if priv_path != None:
        with open(priv_path, "r") as f:
            key_hex = f.read().strip()

        key = Secp256k1PrivateKey.from_hex(key_hex)
        
    else:
        key = context.new_random_private_key()
        
    return crypto_factory.new_signer(key)


def _validate_http_url(url: str):
    return 'http://' + url if not url.startswith("http://") else url


class AirAnchorClient:

    def __init__(self, sawtooth_rest_url, gateway_url, priv_path: None):
        self._sawtooth_rest_url = _validate_http_url(sawtooth_rest_url)
        self._gateway_url = _validate_http_url(gateway_url)
        self._signer = _get_private_key_as_signer(priv_path)

    def do_location(self, data):
        pub_key = self._signer.get_public_key().as_hex()

        csr = {
            'distinguished_name': "DRON",
            'public_key': pub_key,
            'optional_params': {}
        }
        
        transactionRequest = {
            'sender_public_key': pub_key,
            'csr': csr,
            'data': data
        }

        url = self._gateway_url + '/api/v1/transaction'

        try:
            res = requests.post(url, json=transactionRequest)
            
            if res.status_code != 200:
                return "Error when calling gateway: Reason: {}, detail: {}".format(res.reason, res.text)
            
            return "Transaction sent sucessfully"
            
        except BaseException as err:
            return str(err)
            


    def do_show(self, key, hash):
        address = make_location_key_address(key, hash)

        result = self._send_request("{}/state/{}".format(self._sawtooth_rest_url, address))

        try:
            cbor.loads(
                base64.b64decode(
                    yaml.safe_load(result)["data"]))[hash]

        except BaseException:
            return None
    
    
    def do_list(self, key):
        address = make_location_key_address(key=key)
        
        result = self._send_request(
            "{}/state?address={}".format(
                self._sawtooth_rest_url, address)) 

        try:
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                cbor.loads(base64.b64decode(entry["data"]))
                for entry in encoded_entries
            ]

        except BaseException:
            return None

    def _send_request(self, url):
        try: 
            result = requests.get(url)

            if result.status_code == 404:
                raise Exception("No such key")

            if not result.ok:
                raise Exception("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise Exception(
                'Failed to connect to REST API: {}'.format(err)) from err

        except BaseException as err:
            raise Exception(err) from err

        return result.text
