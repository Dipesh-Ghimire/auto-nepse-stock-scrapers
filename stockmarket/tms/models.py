from django.db import models
from django.conf import settings
from meroshare.utils import encrypt, decrypt
from django.db.models import UniqueConstraint
import hashlib

class TMSAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    broker_number = models.CharField(max_length=5)
    _username = models.CharField(max_length=100)
    _password = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    
    username_hash = models.CharField(max_length=64, editable=False)
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['broker_number', 'username_hash'],
                name='unique_broker_username'
            ),
            # Ensure only one primary account per user
            UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_account'
            )
        ]
    def save(self, *args, **kwargs):
        # If this is the first account for the user, make it primary
        if not self.pk and not TMSAccount.objects.filter(user=self.user).exists():
            self.is_primary = True
        super().save(*args, **kwargs)
        
    @property
    def username(self):
        return decrypt(self._username)

    @username.setter
    def username(self, value):
        self._username = encrypt(value)
        self.username_hash = hashlib.sha256(value.encode()).hexdigest()
        
    @property
    def password(self):
        return decrypt(self._password)

    @password.setter
    def password(self, value):
        self._password = encrypt(value)
    

class Trade(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    quantity = models.IntegerField()
    buy_price = models.FloatField()
    stop_loss_percent = models.FloatField(null=True, blank=True)
    take_profit_percent = models.FloatField(null=True, blank=True)
    trailing_stop_loss_percent = models.FloatField(null=True, blank=True)
    auto_execute = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_executed = models.BooleanField(default=False)

    highest_price_seen = models.FloatField(null=True, blank=True)
