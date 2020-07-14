from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")

# /api/recipe/recipes/<id>


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "sample recipe",
        "time_minutes": 10,
        "price": 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name="Main course"):
    """Create and return a smaple tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Salt"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipeApiTests(TestCase):
    """Test Recipe API access"""

    def setUp(self):
        self.cleint = APIClient()

    def test_auth_required(self):
        """Test required authentication"""
        res = self.client.get(RECIPES_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test Recipe API with authentication"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("testing@tes.com", "testpass")

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Retrieve list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Retrieve recipes for user"""

        user2 = get_user_model().objects.create_user("testing2@test.com", "testpass")
        # Create recipes for each user
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        # Get recipe via API for self.user
        res = self.client.get(RECIPES_URL)
        # Get recipe via db for self.user
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        # Should be valid request
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Only return one recipe created above for self.user
        self.assertEqual(len(res.data), 1)
        # API response and db should match
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test create recipe"""
        payload = {"title": "Brownies", "time_minutes": 30, "price": 5.00}
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload:
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name="vegan")
        tag2 = sample_tag(user=self.user, name="dessert")

        payload = {
            "title": "Cheesecake",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 60,
            "price": 10.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Create recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name="salt")
        ingredient2 = sample_ingredient(user=self.user, name="pepper")
        payload = {
            "title": "Any recipe",
            "ingredients": [ingredient1.id, ingredient2.id],
            "time_minutes": 20,
            "price": 7.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()
        self.assertAlmostEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
