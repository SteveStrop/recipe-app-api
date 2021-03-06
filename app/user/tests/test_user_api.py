from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status  # HTTP status codes

CREATE_USER_URL = reverse('user:create')  # the endpoint urls
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


# helper function to clean up code below. Creates a user directly without going through the APIClient
def create_user(**kwargs):
    return get_user_model().objects.create_user(**kwargs)


def get_user(**kwargs):  # helper function to clean up code below
    return get_user_model().objects.get(**kwargs)


class PublicUserApiTests(TestCase):  # for non authenticated access i.e. create a new user
    """
    Test the users API (public)
    """

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """
        Test creating user with valid payload is successful
        """
        payload = {'email': 'test@steve.com', 'password': 'testPass', 'name': 'Test Name'}
        response = self.client.post(path=CREATE_USER_URL, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # check a user created
        user = get_user(**response.data)
        self.assertTrue(user.check_password(payload['password']))  # check correct password for user
        self.assertNotIn('password', response.data)  # check password NOT returned to client

    def test_user_exists(self):
        """
        Test trying to create a user with an existing email fails
        """
        payload = {'email': 'test@steve.com', 'password': 'testPass2', 'name': 'Test Name2'}
        # create user with payload credentials
        create_user(**payload)
        # try and create another user with same credentials
        response = self.client.post(path=CREATE_USER_URL, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # check a user NOT created

    def test_password_too_short(self):
        """
        Test password > 5 chars
        """
        payload = {'email': 'test@steve.com', 'password': 'te2', 'name': 'Test Name3'}
        response = self.client.post(path=CREATE_USER_URL, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # check a user NOT created
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test a toek nis created for the user"""

        payload = {'email': 'test@steve.com', 'password': 'testPass2'}
        create_user(**payload)
        response = self.client.post(path=TOKEN_URL, data=payload)
        self.assertIn('token', response.data)  # is a dict key 'token' present in the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """ Test no token if invalid credentials used"""
        # create a valid user
        payload = {'email': 'test@steve.com', 'password': 'testPass2'}
        create_user(**payload)
        # send invalid credentials
        payload_invalid = {'email': 'test@steve.com', 'password': 'wrong'}
        response = self.client.post(path=TOKEN_URL, data=payload_invalid)
        self.assertNotIn('token', response.data)  # make sure no 'token key in response data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """ Test that token is not created if user doesn't exist"""
        payload = {'email': 'test@steve.com', 'password': 'testPass2'}
        response = self.client.post(path=TOKEN_URL, data=payload)
        self.assertNotIn('token', response.data)  # make sure no 'token key in response data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_email(self):
        """ Test email and password are required"""
        payload = {'email': 'test@steve.com', 'password': 'testPass2'}
        create_user(**payload)
        payload_invalid = {'email': '', 'password': 'testPass2'}
        response = self.client.post(path=TOKEN_URL, data=payload_invalid)
        self.assertNotIn('token', response.data)  # make sure no 'token key in response data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_password(self):
        """ Test email and password are required"""
        payload = {'email': 'test@steve.com', 'password': 'testPass2'}
        create_user(**payload)
        payload_invalid = {'email': 'test@steve.com', 'password': ''}
        response = self.client.post(path=TOKEN_URL, data=payload_invalid)
        self.assertNotIn('token', response.data)  # make sure no 'token key in response data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorised(self):
        """Test that authentication is required for users"""
        # try and get a user with no credentials
        response = self.client.get(path=ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Tests for API requests requiring authentication"""

    def setUp(self):
        """Create authenticated user"""
        payload = {'email': 'test@steve.com', 'password': 'testPass2', 'name': 'Steve'}
        self.user = create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)  # authenticate the test user

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged-in used"""
        response = self.client.get(path=ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'email': self.user.email, 'name': self.user.name})

    def test_post_me_not_allowed(self):
        """Test POST not allowed on me url"""
        response = self.client.post(path=ME_URL, data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile for authenticated users"""
        payload = {'name': 'John', 'password': 'newPass'}
        response = self.client.patch(path=ME_URL, data=payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
