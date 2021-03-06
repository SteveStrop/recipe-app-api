from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings
import uuid
import os


def recipe_image_file_path(instance, filename): # todo move this into Recipe
    """Generate file path for new recipe image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('uploads/recipe',filename)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # from the settings file best practice

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient for a recipe"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # from the settings file best practice

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe objects"""
    title = models.CharField(max_length=255)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    link = models.CharField(max_length=255, blank=True)
    ingredients = models.ManyToManyField(Ingredient)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(null=True,upload_to=recipe_image_file_path)

    def __str__(self):
        return self.title
