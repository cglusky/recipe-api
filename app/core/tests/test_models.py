from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email(self):
        """"Create a new user with an email"""
        email = "test@test.com"
        password = "TestPass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normailzed(self):
        """Email for new user is normalized"""
        email = 'test@TEST.com'
        user = get_user_model().objects.create_user(email, 'test123"')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Create new user with no email raises error"""
        with self.assertRaises(ValueError):
            email = ''
            get_user_model().objects.create_user(email, 'test123')

    def test_create_superuser(self):
        """Create a superuser with privs"""
        user = get_user_model().objects.create_superuser(
            "test@test.com",
            "test123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
