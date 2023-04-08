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
            key_hex = f.read()

        key = Secp256k1PrivateKey.from_hex(key_hex)
        
    else:
        key = context.new_random_private_key()
        
    return crypto_factory.new_signer(key)

class AirAnchorClient:

    def __init__(self, url, ca, priv_path):
        self.url = url
        self.ca = ca
        self._signer = _get_private_key_as_signer(priv_path)

    def location(self, data):

        csr = {
            'distinguished_name': "DRON",
            'public_key': self._signer.get_public_key().as_hex(),
            'optional_params': {}
        }
        
        csr_firm = self._send_ca_request(csr=csr)
    
        payload = {
            'csr': csr,
            'csr_firm': csr_firm,
            'nonce': hex(random.randint(0, 2*+256)),
            'data': data
        }

        payload_encoded = cbor.dumps(payload)

        return self._send_transaction(payload_encoded)
    
    
    def _send_ca_request(self, csr, suffix="api/v1/sign"):
        if self.ca.startswith("http://"):
            ca = "{}/{}".format(self.ca, suffix)
        else:
            ca = "http://{}/{}".format(self.ca, suffix)
            
        ca_response = requests.post(ca, json=csr)
         
        if ca_response.status_code != 200:
            raise Exception("There was an error trying to call ca. Reason: {}".format(ca_response.reason))
    
        return ca_response.json()

    def show(self, key, hash):
        address = make_location_key_address(key, hash)

        result = self._send_request("state/{}".format(address))

        try:
            return cbor.loads(
                base64.b64decode(
                    yaml.safe_load(result)["data"]))[hash]

        except BaseException:
            return None
    
    def list(self, key):
        result = self._send_request(
            "state?address={}".format(
                make_location_key_address(key=key))) 

        try:
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                cbor.loads(base64.b64decode(entry["data"]))
                for entry in encoded_entries
            ]

        except BaseException:
            return None

    def _send_request(self, suffix, data=None, content_type=None, name=None):
        if self.url.startswith("http://"):
            url = "{}/{}".format(self.url, suffix)
        else:
            url = "http://{}/{}".format(self.url, suffix)

        headers = {}

        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if result.status_code == 404:
                raise Exception("No such key: {}".format(name))

            if not result.ok:
                raise Exception("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise Exception(
                'Failed to connect to REST API: {}'.format(err)) from err

        except BaseException as err:
            raise Exception(err) from err

        return result.text


    def _send_transaction(self, payload):
        
        payload_sha512=_sha512(payload)
        key = self._signer.get_public_key().as_hex()

        # Construct the address
        address = make_location_key_address(key, payload_sha512)

        header = TransactionHeader(
            signer_public_key=key,
            family_name=FAMILY_NAME,
            family_version=FAMILY_VERSION,
            inputs=[address],
            outputs=[address],
            dependencies=[],
            payload_sha512=payload_sha512,
            batcher_public_key=key,
            nonce=hex(random.randint(0, 2**64))
        ).SerializeToString()

        signature = self._signer.sign(header)

        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=signature
        )

        batch_list = self._create_batch_list([transaction])

        return self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream',
        )


    def _create_batch_list(self, transactions):
        transaction_signatures = [t.header_signature for t in transactions]

        header = BatchHeader(
            signer_public_key=self._signer.get_public_key().as_hex(),
            transaction_ids=transaction_signatures
        ).SerializeToString()

        signature = self._signer.sign(header)

        batch = Batch(
            header=header,
            transactions=transactions,
            header_signature=signature)

        return BatchList(batches=[batch])
