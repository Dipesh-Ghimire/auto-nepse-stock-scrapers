from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_normal_user = models.BooleanField(default=True)  # normal user by default
    is_admin_user = models.BooleanField(default=False)
    # Add any extra fields here (e.g., phone_number = models.CharField(...))
    

