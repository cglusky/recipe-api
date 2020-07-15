from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


class PublicTagsApiTests(TestCase):
    """Test public tag API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Login required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test private Tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "testuser@test.com", "testpass"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Can retrieve tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Desert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_per_user(self):
        """Tags limited to current user"""

        # Create 2nd user and add tag for that user
        user2 = get_user_model().objects.create_user("otheruser@test.com", "testpass")
        Tag.objects.create(user=user2, name="Fruit")

        # Create a single tag for logged in user
        tag = Tag.objects.create(user=self.user, name="Comfort Food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should only be one tag created/returned for user
        self.assertEqual(len(res.data), 1)
        # Make sure it's the right tag for user
        self.assertEqual(res.data[0]["name"], tag.name)

    def test_create_tag_successful(self):
        """Can create a new tag"""
        payload = {"name": "Test tag"}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(user=self.user, name=payload["name"]).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """May not create a tag with invalid payload"""
        payload = {"name": ""}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retreive_tags_assigned_to_recipes(self):
        """Test filtering tags assigned to recipe"""
        tag1 = Tag.objects.create(user=self.user, name="breakfast")
        tag2 = Tag.objects.create(user=self.user, name="lunch")
        recipe = Recipe.objects.create(
            user=self.user, title="Eggs and Toast", time_minutes=10, price=5.00
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        # Create two tags and two recipes
        # Only assign one of the tags to both recipes
        tag = Tag.objects.create(user=self.user, name="breakfast")
        Tag.objects.create(user=self.user, name="lunch")
        recipe1 = Recipe.objects.create(
            user=self.user, title="Eggs and Toast", time_minutes=10, price=5.00
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            user=self.user, title="Oatmeal", time_minutes=10, price=5.00
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        # Two tags exist but only "breakfast" is assigned to recipes
        self.assertEqual(len(res.data), 1)
