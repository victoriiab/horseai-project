from django.test import TestCase
from .models import User
from .services import create_user, get_user_profile, update_user, delete_user

class UserCRUDTest(TestCase):
    def test_user_crud(self):
        # Create
        user = create_user("testuser", "password123", "test@example.com", "Test User")
        self.assertIsNotNone(user.user_id)

        # Read
        profile = get_user_profile(user.user_id)
        self.assertEqual(profile.login, "testuser")

        # Update
        updated = update_user(user.user_id, full_name="New Name")
        self.assertEqual(updated.full_name, "New Name")

        # Delete
        admin = create_user("admin", "adminpass", "admin@example.com", "Admin User", role_id="admin")
        delete_user(admin, user.user_id)
        self.assertIsNone(get_user_profile(user.user_id))
