from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(password="testPass", email="steve@test.com"):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(password=password, email=email)


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test login required to retrieve ingredients"""
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test ingredients tags"""
        Ingredient.objects.create(user=self.user, name='Beef')
        Ingredient.objects.create(user=self.user, name='Salt')
        response = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test ingredients for authenticated user only"""
        user1 = create_user("123", "bob@mail.com")
        Ingredient.objects.create(user=user1, name="Fruit")
        ingredient = Ingredient.objects.create(user=self.user, name="Bollox")
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # check only one element returned
        self.assertEqual(response.data[0]['name'], ingredient.name)  # check it's the right one

    # def test_create_tag_successful(self):
    #     """Test creating a new ingredient"""
    #     payload = {'name': 'Test tag'}
    #     self.client.post(TAGS_URL, payload)
    #     self.assertTrue(Tag.objects.filter(user=self.user, name=payload['name']).exists())
    #
    # def tes_create_tag_invalid(self):
    #     """Test creating a new tag with invalid payload"""
    #     payload = {'name': ''}
    #     response = self.client.post(TAGS_URL, payload)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
