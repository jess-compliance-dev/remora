from app.database.story_database import StoryDatabase


class StoryService:
    """
    Service layer for life story business logic.
    """

    def __init__(self):
        self.story_db = StoryDatabase()

    def get_stories(self):
        return self.story_db.get_all()

    def get_story_by_id(self, story_id):
        return self.story_db.get_by_id(story_id)

    def get_stories_by_profile_id(self, profile_id):
        return self.story_db.get_by_profile_id(profile_id)

    def create_story(self, data):
        return self.story_db.create(data)

    def update_story(self, story_id, data):
        story = self.story_db.get_by_id(story_id)

        if not story:
            return None

        return self.story_db.update(story, data)

    def delete_story(self, story_id):
        story = self.story_db.get_by_id(story_id)

        if not story:
            return False

        self.story_db.delete(story)
        return True