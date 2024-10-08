'''
Test for a User API
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**parms):
    return get_user_model().objects.create_user(**parms)

class PublicUserApiTest(TestCase):
    '''Test the public features of the user API'''

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        payloads = {
            'email' : 'test@example.com',
            'password' : 'testpass123',
            'name' : 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payloads)
        self.assertAlmostEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payloads['email'])
        self.assertTrue(user.check_password(payloads['password']))
        self.assertNotIn('password', res.data)

    def test_email_with_email_exist_error(self):
        payloads = {
            'email' : 'test@example.com',
            'password' : 'testpass123',
            'name' : 'Test Name',
        }
        create_user(**payloads)
        res = self.client.post(CREATE_USER_URL, payloads)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        payloads = {
            'email' : 'test@example.com',
            'password' : 'pw',
            'name' : 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payloads)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email = payloads['email']
        ).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        user_detail = {
            'email' : 'test@example.com',
            'password' : 'testpass',
            'name' : 'Test Name',
        }

        create_user(**user_detail)
        payloads = {
            'email' : user_detail['email'],
            'password' : user_detail['password']
        }

        res = self.client.post(TOKEN_URL, payloads)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        create_user(email='test@example.com', password='goodpass')

        payload = {'email' : 'test@example.com', 'password' : 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token' ,res.data)

    def test_create_token_blank_password(self):
        payload = {'email' : 'test@example.com', 'password' : ''}

        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTest(TestCase):
    '''Test API requests that require authentication.'''

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass',
            name='Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrive_profile_success(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name' : self.user.name,
            'email': self.user.email,
            })

    def test_post_method_not_allowed(self):
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'name' : 'Updated Name', 'password' : 'newpass'}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)