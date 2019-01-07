from django.test import TestCase
from django.contrib.auth import get_user_model
from app.core import models


def sample_user(email='test@test.com', password='testPast'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_normalised_successful(self):
        """
        Test creating a new user with an email normalises the email address and is successful
        """
        email = "test@STEvE.cOm"
        password = "Testpass123"
        user = get_user_model().objects.create_user(
                email=email,
                password=password
        )
        self.assertEqual(user.email, email.lower())
        self.assertTrue(user.check_password(password))

    def test_new_user_invalid_email(self):
        """
        Test creating user with no email raises error
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email=None, password="123")

    def test_create_new_superuser(self):
        """
        Test creating a new superuser with normalised email
        """
        email = "super@uSEer.com"
        password = "TestPass123"
        user = get_user_model().objects.create_superuser(
                email=email,
                password=password
        )
        self.assertEqual(user.email, email.lower())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_tag_str(self):
        """Test tag string representation"""
        tag = models.Tag.objects.create(user=sample_user(), name='bork')
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(user=sample_user(), name='fish')
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe str representation"""
        recipe = models.Recipe.objects.create(user=sample_user(), title="Beef Stew", time_minutes=5, price=5.00)
        self.assertEqual(str(recipe),recipe.title)
