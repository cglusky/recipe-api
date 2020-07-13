from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")


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
