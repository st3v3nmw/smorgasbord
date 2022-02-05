"""
CSC411
Kerberos Assignment
P15/1198/2018
"""

# Fernet uses AES under the hood
# AES in CBC mode with a 128-bit key for encryption; using PKCS7 padding.
from cryptography.fernet import Fernet, InvalidToken
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from typing import Tuple
from hashlib import md5
from base64 import urlsafe_b64encode
from dateutil.parser import parse


MAX_TTL = 600  # in seconds


def encrypt(message: str, secret_key: bytes) -> str:
    f = Fernet(secret_key)
    encrypted = f.encrypt(message.encode("utf-8")).decode("utf-8")
    return encrypted


def decrypt(message: str, secret_key: bytes) -> str:
    f = Fernet(secret_key)
    decrypted = f.decrypt(message.encode("utf-8")).decode("utf-8")
    return decrypted


class KeyDitributionCenter:
    class AuthenticationServer:
        def __init__(self, tgs_id: str, tgs_secret_key: bytes):
            print("Setting up Authentication Service...", end="\n\n")
            self.tgs_id = tgs_id
            self.__tgs_secret_key = tgs_secret_key
            self.__users = {}

        def register_user(self, username: str, secret_key: bytes):
            self.__users[username] = secret_key

        def process_request(self, message: str) -> Tuple[bool, list[str]]:
            username, user_ip, _, requested_ttl = message.split(",")
            requested_ttl = int(requested_ttl)

            if username not in self.__users:
                return False, [f"{username} is not a known user"]

            client_secret_key = self.__users[username]
            timestamp = datetime.now(ZoneInfo("Africa/Nairobi"))
            print(f"Message receipt timestamp = {timestamp}")
            ttl = min(requested_ttl, MAX_TTL)

            tgs_session_key = Fernet.generate_key()
            print(f"TGS Session Key = {tgs_session_key}")

            messageA = (
                f"{self.tgs_id},{timestamp},{ttl},{tgs_session_key.decode('utf-8')}"
            )
            print(f"Message A = {messageA}")
            encrypted_msg_a = encrypt(messageA, client_secret_key)
            print(f"Encrypted message A = {encrypted_msg_a}")

            tgt = f"{username},{self.tgs_id},{timestamp},{user_ip},{ttl},{tgs_session_key.decode('utf-8')}"
            print(f"Ticket Granting Ticket: {tgt}")
            encrpted_tgt = encrypt(tgt, self.__tgs_secret_key)
            print(f"Encrypted TGT: {encrpted_tgt}", end="\n\n")

            return True, [encrypted_msg_a, encrpted_tgt]

    class TicketGrantingServer:
        def __init__(self, tgs_id: str):
            print("Setting up Ticket Granting Service...")
            self.tgs_id = tgs_id
            self.__secret_key = Fernet.generate_key()
            print(f"TGS Secret Key = {self.__secret_key}")
            self.__services = {}

        def register_service(self, service_id: str, secret_key: bytes):
            self.__services[service_id] = secret_key
            print(f"{service_id} registered with TGS", end="\n\n")

        def secret_key(self):
            return self.__secret_key

        def process_request(
            self, tgt: str, service_request_msg: str, user_authenticator: str
        ):
            service_id, _ = service_request_msg.split(",")
            if service_id not in self.__services:
                return False, [f"{service_id} is not a known service"]

            service_secret_key = self.__services[service_id]
            decrypted_tgt = decrypt(tgt, self.secret_key())
            (
                tgt_username,
                _,
                tgt_timestamp,
                user_ip,
                ttl,
                tgs_session_key,
            ) = decrypted_tgt.split(",")
            decrypted_user_authenticator = decrypt(user_authenticator, tgs_session_key)
            ua_username, ua_timestamp = decrypted_user_authenticator.split(",")

            # Validate Ticket Granting Ticket and User Authenticator
            assert ua_username == tgt_username
            assert ua_timestamp == tgt_timestamp
            now = datetime.now(ZoneInfo("Africa/Nairobi"))
            token_expiry = parse(tgt_timestamp) + timedelta(seconds=int(ttl))
            if now > token_expiry:
                return False, ["Token is expired"]

            service_session_key = Fernet.generate_key()
            print(f"Service Session Key = {service_session_key}")

            msg_a = f"{service_id},{now},{ttl},{service_session_key.decode('utf-8')}"
            print(f"Message A = {msg_a}")
            encrypted_msg_a = encrypt(msg_a, tgs_session_key)
            print(f"Encrypted message A = {encrypted_msg_a}")

            service_ticket = f"{tgt_username},{service_id},{now},{user_ip},{ttl},{service_session_key.decode('utf-8')}"
            print(f"Service Ticket = {service_ticket}")
            encryped_service_ticket = encrypt(service_ticket, service_secret_key)
            print(f"Encryped service ticket = {encryped_service_ticket}", end="\n\n")

            return True, [encrypted_msg_a, encryped_service_ticket]

    def __init__(self, realm: str):
        print(f"Setting up KDC..., Realm = {realm}")
        self.realm = realm
        self.tgs = self.TicketGrantingServer("TGS01")
        self.auth = self.AuthenticationServer("TGS01", self.tgs.secret_key())


class Client:
    def __init__(self, username: str, password: str, ip_address: str, kdc):
        print(f"Setting up {username}'s workstation...")
        self.username = username
        self.ip_address = ip_address
        self.kdc = kdc
        self.__password = password
        secret_key = self.__secret_key
        print(f"{username}'s secret key = {secret_key}", end="\n\n")
        self.kdc.auth.register_user(self.username, secret_key)

    def request(self, service, requested_ttl: int):
        service_id = service.service_id
        print(f"[{self.username}] Sending initial request...")
        message = f"{self.username},{self.ip_address},{service_id},{requested_ttl}"
        print(f"Message = {message} (sent unencrypted)", end="\n\n")
        success, messages = self.kdc.auth.process_request(message)

        if not success:
            print(message[0])
            return

        message_a, tgt = messages

        secret_key = self.__secret_key
        try:
            decrypted_message_a = decrypt(message_a, secret_key)
        except InvalidToken:
            print("Failed: Invalid Secret Key")
            return

        print(f"Decrypted message A => {decrypted_message_a}")
        _, timestamp, ttl, tgs_session_key = decrypted_message_a.split(",")
        service_request_msg = f"{service_id},{ttl}"
        print(f"Service request message = {service_request_msg}")
        user_authenticator = f"{self.username},{timestamp}"
        print(f"User authenticator message = {user_authenticator}")
        encrypted_user_authenticator = encrypt(user_authenticator, tgs_session_key)
        print(
            f"Encrypted user authenticator message = {encrypted_user_authenticator}",
            end="\n\n",
        )

        print(f"[{self.username}] Sending request to Ticket Granting Service...")
        success, messages = self.kdc.tgs.process_request(
            tgt, service_request_msg, encrypted_user_authenticator
        )
        if not success:
            print(messages[0])
            return

        message_a, service_ticket = messages
        decrypted_message_a = decrypt(message_a, tgs_session_key)
        _, timestamp, _, service_session_key = decrypted_message_a.split(",")
        user_authenticator = f"{self.username},{timestamp}"
        print(f"User authenticator message = {user_authenticator}")
        encrypted_user_authenticator = encrypt(user_authenticator, service_session_key)
        print(
            f"Encrypted user authenticator = {encrypted_user_authenticator}", end="\n\n"
        )

        print(f"[{self.username}] Sending request to {service_id} service...")
        service.process_request(encrypted_user_authenticator, service_ticket)

    @property
    def __secret_key(self):
        password_hash = md5(
            f"{self.__password}{self.username}@{self.kdc.realm}".encode("utf-8")
        ).hexdigest()
        return urlsafe_b64encode(password_hash.encode("utf-8"))


class Service:
    def __init__(self, service_id: str, kdc):
        print(f"Setting up {service_id}...")
        self.service_id = service_id
        self.kdc = kdc
        self.__secret_key = Fernet.generate_key()
        print(f"{service_id} secret key = {self.__secret_key}")
        self.kdc.tgs.register_service(self.service_id, self.__secret_key)

    def process_request(self, user_authenticator: str, service_ticket: str):
        decrypted_service_ticket = decrypt(service_ticket, self.__secret_key)
        (
            st_username,
            service_id,
            st_timestamp,
            userip,
            ttl,
            service_session_key,
        ) = decrypted_service_ticket.split(",")
        decrypted_ua = decrypt(user_authenticator, service_session_key)
        ua_userid, ua_timestamp = decrypted_ua.split(",")

        assert st_username == ua_userid
        assert st_timestamp == ua_timestamp
        assert service_id == self.service_id
        print(
            f"{st_username}'s messages verified, connection to {service_id} established!"
        )


if __name__ == "__main__":
    kdc = KeyDitributionCenter("kerberos.org")
    ftp_service = Service("FTP_SERVER", kdc)
    smtp_service = Service("SMTP_SERVER", kdc)
    alice = Client("Alice", "@Admin1234", "192.168.0.1", kdc)

    alice.request(smtp_service, 300)


"""
SAMPLE OUTPUT

Setting up KDC..., Realm = kerberos.org
Setting up Ticket Granting Service...
TGS Secret Key = b'onB-KMsOeXw0P76y3azC0BNLgS6y-k0y8cmlSQHcR4k='
Setting up Authentication Service...

Setting up FTP_SERVER...
FTP_SERVER secret key = b'H7L7p7HRlVvOPYggJOf2lxZARvmGLAmbuzaeWY2okRA='
FTP_SERVER registered with TGS

Setting up SMTP_SERVER...
SMTP_SERVER secret key = b'l0lejJptM_nnXmTtbQ1E-0oIRGK6Q7y9rlDuDs9-KLo='
SMTP_SERVER registered with TGS

Setting up Alice's workstation...
Alice's secret key = b'N2M2YmMwZDgwMzJjYTE3YTlkMmMwMDg5MThlZjVmMGI='

[Alice] Sending initial request...
Message = Alice,192.168.0.1,SMTP_SERVER,300 (sent unencrypted)

Message receipt timestamp = 2021-11-29 09:45:36.243102+03:00
TGS Session Key = b'PG0RflzJ1RJ-hsR-nIn8quIIOnuHTuBnI3TJJHnNQoI='
Message A = TGS01,2021-11-29 09:45:36.243102+03:00,300,PG0RflzJ1RJ-hsR-nIn8quIIOnuHTuBnI3TJJHnNQoI=
Encrypted message A = gAAAAABhpHcQQcBdEYrsJU8chxjOXLXus7C6rympKIH-6pKFASBKhJDkeAlBbpxrQIhSLc1rMrzLIdni4HvoEOExI7ggfzwTLwRjSYnVRxjZEupthdWAN0ypJHu0IZf36Psxf0oV8OqIrKqd3Z0WXC_NHG04RmhkjzHb5WqxTH5kWlnnkSsxU9AImWQqgJUNYwOVY6fl-wYw
Ticket Granting Ticket: Alice,TGS01,2021-11-29 09:45:36.243102+03:00,192.168.0.1,300,PG0RflzJ1RJ-hsR-nIn8quIIOnuHTuBnI3TJJHnNQoI=
Encrypted TGT: gAAAAABhpHcQwu3uAOGxFNBHE95AbAKG3NtiRdw0cFpXYDgzLqFnHDy4YAdAXUGl-QPWx37eSRUYtCZGeJMd54AmFYT9n8rGIGbOrVD6WlAmK4syHnPYDdcnuyp6PIw1H572dn5fqovKNyv2cPsHCG0Kbq2g7IBj_o7nL1rs06CYPW9Io7qBD0DdVgsAQNNPO0fkwmpIY1wEuQxNJL1t66A65TE8EIatqQ==

Decrypted message A => TGS01,2021-11-29 09:45:36.243102+03:00,300,PG0RflzJ1RJ-hsR-nIn8quIIOnuHTuBnI3TJJHnNQoI=
Service request message = SMTP_SERVER,300
User authenticator message = Alice,2021-11-29 09:45:36.243102+03:00
Encrypted user authenticator message = gAAAAABhpHcQJbKR7M1RASyFOqIcUJbTnlAQvdE3dGDk_aJrUdJjqkxikyf25FX_KuOVN8hef66kON0SNqLjehmcOiqq8bDHY12YjKvziGhlfQT2sroouVdKfeIb3-F94f_ISfRm9bD8

[Alice] Sending request to Ticket Granting Service...
Service Session Key = b'03AUUBTBEVgtGWb_CZPVTF-agoNSRqIwNmQSki1yWm8='
Message A = SMTP_SERVER,2021-11-29 09:45:36.308602+03:00,300,03AUUBTBEVgtGWb_CZPVTF-agoNSRqIwNmQSki1yWm8=
Encrypted message A = gAAAAABhpHcQc3FvbgrR8lv6OcMlaTMyGtKa3NejFwwU0iAQk36qkW6YKEl8TsOv00W8EUUxI42Ebjt95iMaQ4ipjBlXkUkIh1MHkFHzkhYVdksNZIGlOF_bd9P8tpC8R2qlRFUNZKFqFn4ScXFOhuYCIKTU2jaKtuM8LZr7SO_P9RiNFs5rgiyRueTIEo2f7NXWV4PPimqJ
Service Ticket = Alice,SMTP_SERVER,2021-11-29 09:45:36.308602+03:00,192.168.0.1,300,03AUUBTBEVgtGWb_CZPVTF-agoNSRqIwNmQSki1yWm8=
Encryped service ticket = gAAAAABhpHcQ54XfsQu4WHCHjPaYcYvU88oyvCBTtW5uUV_JQF59vfHdCiLc940NwZDj6rrnyMV5TgBBD-buKfNACajojhbts2I2lY-Qs7zumshBGwUYjA55JtandjoV2sqQWqENsQN7YEFcdtOKApR3xA5TlTegTYtvUGYVgeXqm43hwtiW3ClBTf0DV0dHHakD_IMZfRimb2C3cr2NlFIaFSyxi4BtYg==

User authenticator message = Alice,2021-11-29 09:45:36.308602+03:00
Encrypted user authenticator = gAAAAABhpHcQVIaUMPR-mQ00lxPyk2yoDm-3rmdrkX8Fach-RzkVRMgTcPra7flcm3yUX0n1BsYC4OdDwsZ-PlDtI8pGmLdLyGr4tJHXNDtgvsMYn-kx65Z8T_pQU4QpHkbFRujFDztV

[Alice] Sending request to SMTP_SERVER service...
Alice's messages verified, connection to SMTP_SERVER established!
"""
