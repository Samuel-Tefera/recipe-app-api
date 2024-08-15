'''
Test for the ingredients API
'''
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    '''Create and return ingredient detail URL'''
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='testpass123'):
    '''Create and return user.'''
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsAPITest(TestCase):
    '''Test unauthenticated API request.'''
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    '''Test authenticated API request'''
    def setUp(self):
        self.user = create_user()
        self.client  = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Ing1')
        Ingredient.objects.create(user=self.user, name='Ing2')

        res = self.client.get(INGREDIENTS_URL)
        ings = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_ingredients_limited_to_user(self):
        other_user = create_user(email='other@example.com', password='other123')
        Ingredient.objects.create(user=other_user, name='Ing1')
        Ingredient.objects.create(user=self.user, name='Ing2')

        res = self.client.get(INGREDIENTS_URL)
        ings = Ingredient.objects.filter(user=self.user).order_by('-name')
        serializer = IngredientSerializer(ings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.data[0]['name'], 'Ing2')

    def test_update_ingredient(self):
        ingt = Ingredient.objects.create(user=self.user, name='Pea')
        payload = {'name' : 'Tommato'}
        url = detail_url(ingt.id)

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingt.refresh_from_db()
        self.assertEqual(res.data['name'], payload['name'])
