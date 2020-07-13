from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


# Helper function to create new user
def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test users public API"""

    def setUp(self):
        self.client = APIClient()
        # User object with valid key/values for API
        self.test_user = {
            "email": "test@test.com",
            "password": "testpass",
            "name": "Test name",
        }

    def test_create_valid_success(self):
        """Test create user with valid payload return success"""

        res = self.client.post(CREATE_USER_URL, self.test_user)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Get user from db based on response data
        user = get_user_model().objects.get(**res.data)
        # Ensure user was created by checking password
        self.assertTrue(user.check_password(self.test_user["password"]))
        # Ensure passsword is not being returned in response
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        """Do not allow creating duplicate user"""

        create_user(**self.test_user)
        # Using same creds as above so user already exists
        res = self.client.post(CREATE_USER_URL, self.test_user)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Password must be more than 5 characters"""

        self.test_user["password"] = "test"

        res = self.client.post(CREATE_USER_URL, self.test_user)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure user did not get added to db
        user_exists = (
            get_user_model().objects.filter(email=self.test_user["email"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Create token for user"""

        create_user(**self.test_user)
        res = self.client.post(TOKEN_URL, self.test_user)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Token not create if invalid creds given"""

        create_user(**self.test_user)
        self.test_user["password"] = "wrong"
        res = self.client.post(TOKEN_URL, self.test_user)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Token not created if user does not exist"""

        res = self.client.post(TOKEN_URL, self.test_user)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """No token without required fields of email and password"""

        self.test_user["password"] = ""

        res = self.client.post(TOKEN_URL, self.test_user)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_unauthorized(self):
        """Test authentication for API"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email="test@londonappdev.com", password="testpass", name="fname",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"name": self.user.name, "email": self.user.email,})

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me URL"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {"name": "new name", "password": "newpassword123"}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
