from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):

    # todo look at using kwargs instead of long list of keywords in EstateAgent

    def create_user(self, email, password=None, **kwargs):
        """
        Creates and saves a new user
        :param email: string
        :param password: string
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)  # if the project uses multiple databases
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a new superuser
        :param email: string
        :param password: string
        """
        if not email:
            raise ValueError('SuperUsers must have an email address')
        user = self.create_user(email=email, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)  # if the project uses multiple databases
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model supporting email for username
    """
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    # todo change Djangojobs status to is_active as this looks like it's built in.(can be used instead of delete I
    #  guess)
    is_active = models.BooleanField(default=True)
    # todo set up staff users for full access and others for viewing only in Djangojobs
    is_staff = models.BooleanField(default=False)

    # todo probably used in admin.py
    objects = UserManager()

    USERNAME_FIELD = 'email'


class Tag(models.Model):
    """Tag for a recipe"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE) # from the seting file best practice

    def __str__(self):
        return self.name
