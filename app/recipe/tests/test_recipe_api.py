'''
Test for recipe APIs.
'''
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializers,
    RecipeDetailSerializer,
)

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    '''Create and return recipe detail URL.'''
    return reverse(f'recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    '''Create and return a sample recipe'''
    default = {
        'title' : 'Sample recipe title',
        'time_minutes' : 22,
        'price' : Decimal('5.25'),
        'description' : 'Sample description',
        'link' : 'http://example.com/recipe.com',
    }
    default.update(params)

    recipe = Recipe.objects.create(user=user, **default)
    return recipe


class PublicRecipeAPITests(TestCase):
    '''Test unauthenticated API requests.'''
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    '''Test authenticated API requests'''
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testhpass',
        )
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializers(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_user(self):
        other_user = get_user_model().objects.create_user(
            'other@gmail.com',
            'otherpass',
        )
        create_recipe(self.user)
        create_recipe(other_user)

        res = self.client.get(RECIPE_URL)
        recipe = Recipe.objects.all().filter(user=self.user).order_by('-id')
        serializer = RecipeSerializers(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail_api(self):
        recipe = create_recipe(self.user)
        res = self.client.get(detail_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
