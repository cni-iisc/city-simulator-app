"""
models.py: provides the defintions for the database tables used in the application
"""
import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import UserManager

class userModel(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    works_at = models.CharField(null=True, blank=True, max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    USERNAME_FIELD = 'email'
    objects = UserManager()

    def get_staff(self):
        return self.is_staff

    def get_full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email


## contains the generated token when a new user registers
class UserRegisterToken(models.Model):
    user = models.OneToOneField(userModel, on_delete=models.CASCADE)
    token = models.CharField(unique=True, max_length=100)

## contains the most-recent generated token set for a user to reset their password
class UserPasswordResetToken(models.Model):
    user = models.OneToOneField(userModel, on_delete=models.CASCADE)
    token = models.CharField(unique=True, max_length=100)

## used for activating a new user.
## Users are being redirect to 'redirect_url' after getting 'name' from a GET parameter.
class RegisterOrigin(models.Model):
    name = models.SlugField()
    redirect_url = models.URLField()
