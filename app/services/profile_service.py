from app.repositories.profile_repository import ProfileRepository


class ProfileService:
    """
    Service layer for memorial profile business logic.
    """

    def __init__(self):
        self.profile_repository = ProfileRepository()

    def get_profiles(self):
        """
        Get all memorial profiles.
        """
        return self.profile_repository.get_all()

    def get_profile_by_id(self, profile_id: int):
        """
        Get a memorial profile by ID.
        """
        return self.profile_repository.get_by_id(profile_id)

    def create_profile(self, data: dict):
        """
        Create a new memorial profile.
        """
        return self.profile_repository.create(data)

    def update_profile(self, profile_id: int, data: dict):
        """
        Update a memorial profile.
        """
        profile = self.profile_repository.get_by_id(profile_id)
        if not profile:
            return None

        return self.profile_repository.update(profile, data)

    def delete_profile(self, profile_id: int) -> bool:
        """
        Delete a memorial profile.
        """
        profile = self.profile_repository.get_by_id(profile_id)
        if not profile:
            return False

        self.profile_repository.delete(profile)
        return True
