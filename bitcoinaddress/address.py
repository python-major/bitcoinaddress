import binascii
import hashlib
import base58
import ecdsa

from . import Key, segwit_addr
from .util import doublehash256


class Address:

    def __init__(self, key: Key):
        self.privkey = key
        self.pubkey = None
        self.pubkey_c = None
        self.pubaddr1 = None
        self.pubaddr3 = None
        self.pubaddrbc1_P2WPKH = None
        self.pubaddrbc1_P2WSH = None

        self.pubaddr1_testnet = None
        self.pubaddr3_testnet = None
        self.pubaddrbc1_P2WPKH_testnet = None
        self.pubaddrbc1_P2WSH_testnet = None

    def hash160(self, v):
        r = hashlib.new('ripemd160')
        r.update(hashlib.sha256(v).digest())
        return r

    def ecdsaSECP256k1(self, digest):
        # SECP256k1 - Bitcoin elliptic curve
        sk = ecdsa.SigningKey.from_string(digest, curve=ecdsa.SECP256k1)
        return sk.get_verifying_key()

    def generate(self) -> {}:

        if self.privkey.hash is None:
            self.privkey.generate()

        self._generate_publicaddress1()
        self._generate_publicaddress3()
        self._generate_publicaddress_bech32()

        self._generate_publicaddress1_testnet()
        self._generate_publicaddress3_testnet()
        self._generate_publicaddress_bech32_testnet()

        return {'pubkey': self.pubkey, 'pubkeyc': self.pubkey_c,
                'pubaddr1': self.pubaddr1, 'pubaddr3': self.pubaddr3,
                'pubaddrbc1_p2wsh': self.pubaddrbc1_P2WSH, 'pubaddrbc1_p2wpkh': self.pubaddrbc1_P2WPKH,
                'testnet': {
                    'pubkey': self.pubkey, 'pubkeyc': self.pubkey_c,
                    'pubaddr1': self.pubaddr1_testnet, 'pubaddr3': self.pubaddr3_testnet,
                    'pubaddrbc1_p2wsh': self.pubaddrbc1_P2WSH_testnet, 'pubaddrbc1_p2wpkh': self.pubaddrbc1_P2WPKH_testnet
                }}

    def _generate_publicaddress1(self):
        prefix_a = b'\x04'
        prefix_b = b'\x00'
        self.pubaddr1 = self.__generate_uncompressed_pubkey(prefix_a, prefix_b)

    def _generate_publicaddress1_testnet(self):
        prefix_a = b'\x04'
        prefix_b = b'\x6F'
        self.pubaddr1_testnet = self.__generate_uncompressed_pubkey(prefix_a, prefix_b)

    def _generate_publicaddress3(self):
        self.pubaddr3 = self.__generate_publicaddress3(b'\x05')

    def _generate_publicaddress3_testnet(self):
        self.pubaddr3_testnet = self.__generate_publicaddress3(b'\xC4')

    def __generate_publicaddress3(self, prefix_b):
        prefix_redeem = b'\x00\x14'

        p = self.__generate_compressed_pubkey(b'\x02', b'\x03')
        redeem_script = self.hash160(prefix_redeem + self.hash160(p).digest()).digest()  # 20 bytes

        m = prefix_b + redeem_script
        checksum = doublehash256(m).digest()[:4]

        return base58.b58encode(m + checksum).decode('utf-8')

    def _generate_publicaddress_bech32(self):
        p = self.__generate_compressed_pubkey(b'\x02', b'\x03')

        redeem_script_P2WPKH = self.hash160(p).digest()  # 20 bytes
        redeem_script_P2WSH = hashlib.sha256(p).digest()

        self.pubaddrbc1_P2WPKH = str(segwit_addr.encode('bc', 0x00, redeem_script_P2WPKH))
        self.pubaddrbc1_P2WSH = str(segwit_addr.encode('bc', 0x00, redeem_script_P2WSH))

    def _generate_publicaddress_bech32_testnet(self):
        p = self.__generate_compressed_pubkey(b'\x02', b'\x14')

        redeem_script_P2WPKH = self.hash160(p).digest()  # 20 bytes
        redeem_script_P2WSH = hashlib.sha256(p).digest()

        self.pubaddrbc1_P2WPKH_testnet = str(segwit_addr.encode('tb', 0x00, redeem_script_P2WPKH))
        self.pubaddrbc1_P2WSH_testnet = str(segwit_addr.encode('tb', 0x00, redeem_script_P2WSH))

    def __generate_uncompressed_pubkey(self, prefix_a, prefix_b):
        digest = self.privkey.hash.digest()

        p = prefix_a + self.ecdsaSECP256k1(digest).to_string()  # 1 + 32 bytes + 32 bytes
        self.pubkey = str(binascii.hexlify(p).decode('utf-8'))

        hash160 = self.hash160(p)

        m = prefix_b + hash160.digest()
        checksum = doublehash256(m).digest()[:4]

        return base58.b58encode(m + checksum).decode('utf-8')

    def __generate_compressed_pubkey(self, prefix_even, prefix_odd):
        prefix_a = prefix_odd

        digest = self.privkey.hash.digest()

        ecdsa_digest = self.ecdsaSECP256k1(digest).to_string()

        x_coord = ecdsa_digest[:int(len(ecdsa_digest) / 2)]
        y_coord = ecdsa_digest[int(len(ecdsa_digest) / 2):]

        if (int(binascii.hexlify(y_coord), 16) % 2 == 0): prefix_a = prefix_even

        p = prefix_a + x_coord

        self.pubkey_c = str(binascii.hexlify(p).decode('utf-8'))

        return p

    def __str__(self):
        return """Public Key: %s 
                  \rPublic Key compressed: %s\n
                  \rPublic Address 1: %s   
                  \rPublic Address 3: %s  
                  \rPublic Address bc1 P2WPKH: %s    
                  \rPublic Address bc1 P2WSH: %s  
                  \rPublic Address 1 (TESTNET): %s   
                  \rPublic Address 3 (TESTNET): %s  
                  \rPublic Address tb1 P2WPKH (TESTNET): %s    
                  \rPublic Address tb1 P2WSH (TESTNET): %s  
                """ % (self.pubkey, self.pubkey_c, self.pubaddr1, self.pubaddr3, self.pubaddrbc1_P2WSH, self.pubaddrbc1_P2WPKH
                                      , self.pubaddr1_testnet, self.pubaddr3_testnet, self.pubaddrbc1_P2WSH_testnet, self.pubaddrbc1_P2WPKH_testnet)
