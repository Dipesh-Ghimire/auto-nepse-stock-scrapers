from django.db import models
from django.conf import settings
from .utils import encrypt, decrypt
from .capital import CAPITAL_CHOICES

class MeroShareAccount(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alias_name = models.CharField(max_length=100, unique=True)

    dp = models.TextField(db_column='dp', choices=CAPITAL_CHOICES)
    _username = models.TextField(db_column='username', unique=True)
    _password = models.TextField(db_column='password')
    _crn = models.TextField(db_column='crn')
    _pin = models.TextField(db_column='pin')

    auto_ipo_apply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.alias_name} ({self.owner.username})"

    @property
    def username(self):
        return decrypt(self._username)

    @username.setter
    def username(self, value):
        self._username = encrypt(value)

    @property
    def password(self):
        return decrypt(self._password)

    @password.setter
    def password(self, value):
        self._password = encrypt(value)

    @property
    def crn(self):
        return decrypt(self._crn)

    @crn.setter
    def crn(self, value):
        self._crn = encrypt(value)

    @property
    def pin(self):
        return decrypt(self._pin)

    @pin.setter
    def pin(self, value):
        self._pin = encrypt(value)

