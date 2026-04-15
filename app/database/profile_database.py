from app.extensions.db import db
from app.models.memorial_profile import MemorialProfile


class ProfileDatabase:
    """
    Repository layer for memorial profile database operations.
    """

    def get_all(self) -> list[MemorialProfile]:
        """
        Retrieve all memorial profiles.
        Returns:
            list[MemorialProfile]: List of all profiles.
        """
        return MemorialProfile.query.all()

    def get_by_id(self, profile_id: int) -> MemorialProfile | None:
        """
        Retrieve a memorial profile by its ID.
        """
        return MemorialProfile.query.get(profile_id)

    def create(self, data: dict) -> MemorialProfile:
        """
        Create a new memorial profile.
        Returns:
            MemorialProfile: The created profile.
        """
        profile = MemorialProfile(**data)
        db.session.add(profile)
        db.session.commit()
        return profile

    def update(self, profile: MemorialProfile, data: dict) -> MemorialProfile:
        """
        Update an existing memorial profile.
        Returns:
            MemorialProfile: The updated profile.
        """
        for key, value in data.items():
            setattr(profile, key, value)

        db.session.commit()
        return profile

    def delete(self, profile: MemorialProfile) -> None:
        """
        Delete a memorial profile.
        """
        db.session.delete(profile)
        db.session.commit()

    def get_by_owner_id(self, owner_id: int):
        return MemorialProfile.query.filter_by(owner_id=owner_id).all()

