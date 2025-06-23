from cryptography.fernet import Fernet
from django.conf import settings

FERNET_KEY = settings.FERNET_KEY.encode()  # load from settings
fernet = Fernet(FERNET_KEY)

def encrypt(text):
    if text is None:
        return None
    return fernet.encrypt(text.encode()).decode()

def decrypt(token):
    if token is None:
        return None
    return fernet.decrypt(token.encode()).decode()
