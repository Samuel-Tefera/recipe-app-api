'''
Tests for tags API.
'''
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializers

TAGS_URL = reverse('recipe:tag-list')

def deatil_url(tag_id):
    '''Create and return a tag deatil url.'''
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='user@gmail.com', password='testpass'):
    '''Create and return a user.'''
    return get_user_model().objects.create_user(email, password)


class PublicTagsAPITest(TestCase):
    '''API test for unauthenticated user.'''
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):
    '''API test for authenticated user.'''
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_tags_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializers(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        other_user = create_user(email='other@example.com', password='123test')

        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Cake')
        Tag.objects.create(user=other_user, name='Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().filter(user=self.user).order_by('-name')
        serializer = TagSerializers(tags, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 2)

    def test_update_tag(self):
        tag = Tag.objects.create(user=self.user, name='After Dinner')
        payload = {'name' : 'Update Tag name'}

        url = deatil_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        url = deatil_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
        