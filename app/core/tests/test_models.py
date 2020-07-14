from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def test_user(email="testuser@test.com", password="testpass"):
    """Create a sample user for testing"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_with_email(self):
        """"Create a new user with an email"""
        email = "test@test.com"
        password = "TestPass123"
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normailzed(self):
        """Email for new user is normalized"""
        email = "test@TEST.com"
        user = get_user_model().objects.create_user(email, 'test123"')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Create new user with no email raises error"""
        with self.assertRaises(ValueError):
            email = ""
            get_user_model().objects.create_user(email, "test123")

    def test_create_superuser(self):
        """Create a superuser with privs"""
        user = get_user_model().objects.create_superuser("test@test.com", "test123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test str representation"""
        tag = models.Tag.objects.create(user=test_user(), name="Vegan")

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient str output"""
        ingredient = models.Ingredient.objects.create(user=test_user(), name="Cucumber")

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test recipe str output"""
        recipe = models.Recipe.objects.create(
            user=test_user(), title="Veggie Stir Fry", time_minutes=5, price=5.00
        )

        self.assertEqual(str(recipe), recipe.title)
