
from dataclasses import dataclass, asdict
import cbor
import secrets
from hashlib import sha512
from sawtooth_signing import Signer
import json

@dataclass
class CertificateRequestHeader():
    distinguied_name: str
    sender_public_key: str
    nonce: str
    
    def as_dict(self):
        return asdict(self)
    
    def serialize(self):
        return json.dumps(self.as_dict(), separators=(',', ':'))

@dataclass
class CertificateRequest():
    header: CertificateRequestHeader
    signature: str
    
    def as_dict(self):
        return asdict(self)
    
    @staticmethod
    def create(distinguied_name: str, signer: Signer):
        
        header = CertificateRequestHeader(
            distinguied_name=distinguied_name,
            sender_public_key=signer.get_public_key().as_hex(),
            nonce=secrets.token_hex()
        )
        
        return CertificateRequest(
            header=header,
            signature=signer.sign(header.serialize().encode())
        )
    
@dataclass
class TransactionRequestHeader():
    sender_public_key: str
    certificate_request: CertificateRequest
    nonce: str
    data_sha512: str
    
    def as_dict(self):
        return asdict(self)

    def serialize(self):
        return json.dumps(self.as_dict(), separators=(',', ':'))
    
    @staticmethod
    def create(sender_public_key: str, 
                    certificate_request: CertificateRequest,
                    data_sha515: str
                    ):
        
        return TransactionRequestHeader(
            sender_public_key=sender_public_key,
            certificate_request=certificate_request,
            nonce=secrets.token_hex(),
            data_sha512=data_sha515
        )

@dataclass
class TransactionRequest():
    header: TransactionRequestHeader
    signature: str
    data: str
    
    def as_dict(self):
        return asdict(self)
    
    def serialize(self):
        return json.dumps(self.as_dict(), separators=(',', ':'))
    
    @staticmethod
    def create(signer: Signer,
               certificate_request: CertificateRequest,
               data: str
               ):
        
        header = TransactionRequestHeader.create(
            sender_public_key=signer.get_public_key().as_hex(),
            certificate_request=certificate_request,
            data_sha515=sha512(
                data.encode('utf-8')).hexdigest()
        )
        
        return TransactionRequest(
            header=header,
            signature=signer.sign(header.serialize().encode()),
            data=data
        )