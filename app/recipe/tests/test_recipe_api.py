'''
Test for recipe APIs.
'''
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

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

def create_user(**parms):
    '''Create and return user.'''
    return get_user_model().objects.create_user(**parms)


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
        self.user = create_user(email='user@example.com', password='test123')
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
        other_user = create_user(email='other@example.com', password='other123')
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

    def test_create_recipe(self):
        payloads = {
            'title' : 'recipe title',
            'time_minutes' : 40,
            'price' : Decimal('5.99'),
        }

        res = self.client.post(RECIPE_URL, payloads)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payloads.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        orginal_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user = self.user,
            title = 'recipe title',
            link = orginal_link,
        )
        payload = {'title' : 'new recipe title'}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.link, orginal_link)

    def test_full_recipe_update(self):
        recipe = create_recipe(self.user)
        payloads = {
            'title' : 'new title',
            'time_minutes' : 30,
            'price' : Decimal('3'),
            'description' : 'New description',
            'link' : 'http://example.com/new_recipe.com',
        }
        url = detail_url(recipe_id=recipe.id)
        res = self.client.put(url, payloads)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payloads.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        new_user = create_user(
            email='new_user@example.com', password='test123'
        )
        recipe = create_recipe(self.user)
        payload = {'user' : new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe =create_recipe(self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        new_user = create_user(email='new_user@example.com', password='test123')
        recipe = create_recipe(new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tag(self):
        payloads = {
            'title' : 'Thai Prawn Carry',
            'time_minutes' : 30,
            'price' : Decimal('2.50'),
            'tags' : [{'name' : 'Thai'}, {'name' : 'Dinner'}]
        }

        res = self.client.post(RECIPE_URL, payloads, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]

        for tag in payloads['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_creat_recipe_with_existing_tag(self):
        tad_indian = Tag.objects.create(user=self.user, name='Indian')
        payloads = {
            'title' : 'Thai Prawn Carry',
            'time_minutes' : 30,
            'price' : Decimal('2.50'),
            'tags' : [{'name' : 'Indian'}, {'name' : 'Breakfast'}]
        }

        res = self.client.post(RECIPE_URL, payloads, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tad_indian, recipe.tags.all())

        for tag in payloads['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {'tags' : [{'name' : 'Lunch'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(name='Lunch', user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags' : [{'name' : 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag_dessert = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_dessert)

        payload = {'tags' : []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_ingredient(self):
        payload = {
            'title' : 'Pie',
            'time_minutes' : 20,
            'price' : Decimal('40.0'),
            'ingredients' : [{'name' : 'Pie'}, {'name', 'Salt'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ings in payload('ingredients'):
            exists = recipe.objects.filter(
                name=ings['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)
