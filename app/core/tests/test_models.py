from django.test import TestCase
from django.contrib.auth import get_user_model


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
        password = "Testpass123"
        user = get_user_model().objects.create_superuser(
                email=email,
                password=password
        )
        self.assertEqual(user.email, email.lower())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
