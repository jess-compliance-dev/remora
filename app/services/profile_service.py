from app.database.profile_database import ProfileDatabase


class ProfileService:
    """
    Service layer for memorial profile business logic.
    """

    def __init__(self):
        self.profile_db = ProfileDatabase()

    def get_profiles(self):
        """Get all memorial profiles."""
        return self.profile_db.get_all()

    def get_profile_by_id(self, profile_id: int):
        """Get memorial profile by ID."""
        return self.profile_db.get_by_id(profile_id)

    def create_profile(self, data: dict):
        """Create a new memorial profile."""
        return self.profile_db.create(data)

    def update_profile(self, profile_id: int, data: dict):
        """Update a memorial profile."""
        profile = self.profile_db.get_by_id(profile_id)

        if not profile:
            return None

        return self.profile_db.update(profile, data)

    def delete_profile(self, profile_id: int):
        """Delete a memorial profile."""
        profile = self.profile_db.get_by_id(profile_id)

        if not profile:
            return False

        self.profile_db.delete(profile)
        return True

    def get_profiles_by_owner_id(self, owner_id: int):
        return self.profile_db.get_by_owner_id(owner_id)
