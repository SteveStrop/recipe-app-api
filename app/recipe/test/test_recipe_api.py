import tempfile
import os
from PIL import Image
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return url for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """"Return a url that points to a specific recipe by id"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_user(password="testPass", email="steve@test.com"):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(password=password, email=email)


def sample_tag(user, name="main course"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="fish"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **kwargs):
    """Helper function to create a sample recipe"""
    defaults = {
            'title':        'Sample Recipe',
            'time_minutes': 10,
            'price':        5.0
    }
    defaults.update(kwargs)  # can update an existing key or create a new one
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """ Test un authenticated Recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication required to access Recipes"""
        response = self.client.get(RECIPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated Recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe_list(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user, title="Fox broth")
        response = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test recipes for authenticated user only"""
        user1 = create_user(password="123", email="bob@mail.com")
        sample_recipe(user=user1)
        sample_recipe(user=self.user, title="Fox broth")
        response = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # check only one element returned
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        response = self.client.get(detail_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
                'title':        'Chocolate cheesecake',
                'time_minutes': 30,
                'price':        5.00
        }
        response = self.client.post(RECIPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """"Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name="Stew")
        tag2 = sample_tag(user=self.user, name="Dessert")
        payload = {
                'title':        'Avocado cheesecake',
                'tags':         [tag1.id, tag2.id],
                'time_minutes': 30,
                'price':        5.00
        }
        response = self.client.post(RECIPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """"Test creating a recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name="prawns")
        ingredient2 = sample_ingredient(user=self.user, name="ginger")
        payload = {
                'title':        'Thai cheesecake',
                'ingredients':  [ingredient1.id, ingredient2.id],
                'time_minutes': 35,
                'price':        15.00
        }
        response = self.client.post(RECIPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='curry')
        payload = {'title': 'Chicken tikka', 'tags': [new_tag.id]}
        self.client.patch(detail_url(recipe.id), payload)
        recipe.refresh_from_db()  # need to refresh after a patch
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)  # alternative to using .count
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating with put"""  # put will remove any fields not specified
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='curry')
        payload = {'title': 'Fishy love', 'time_minutes': 25, 'price': 5.00}
        self.client.put(detail_url(recipe.id), payload)
        recipe.refresh_from_db()  # need to refresh after a put
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        # tags should have ben cleared as this is a put
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            response = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        response = self.client.post(url, {'image': 'not image'}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""

        recipe1 = sample_recipe(user=self.user, title="Thai")
        recipe2 = sample_recipe(user=self.user, title="Spinach curry")
        tag1 = sample_tag(user=self.user, name="French")
        tag2 = sample_tag(user=self.user, name="Italian")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Fish & Chips')
        response = self.client.get(RECIPE_URL, {'tags': f'{tag1.id},{tag2.id}'})
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""

        recipe1 = sample_recipe(user=self.user, title="Beans")
        recipe2 = sample_recipe(user=self.user, title="Soup")
        ingredient1 = sample_ingredient(user=self.user, name="beans")
        ingredient2 = sample_ingredient(user=self.user, name="stock")
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Steak & onions')
        response = self.client.get(RECIPE_URL, {'ingredients': f'{ingredient1.id},{ingredient2.id}'})
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)
