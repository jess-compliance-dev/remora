class StoryAIService:
    """
    AI service for enriching life stories.
    """

    def generate_title(self, text: str) -> str:
        """
        Generate a short title for the story.
        """
        sentences = text.split(".")
        first = sentences[0][:60]

        return first.strip().title()

    def generate_summary(self, text: str) -> str:
        """
        Generate a short summary.
        """
        return text[:200]

    def detect_emotion(self, text: str) -> str:
        """
        Basic emotion detection.
        """
        text = text.lower()

        if "miss" in text or "sad" in text or "loss" in text:
            return "nostalgic"

        if "laugh" in text or "funny" in text:
            return "joyful"

        if "love" in text:
            return "warm"

        if "calm" in text:
            return "peaceful"

        return "reflective"

    def detect_theme(self, text: str) -> str:
        """
        Detect story theme.
        """
        text = text.lower()

        if "grandma" in text or "mother" in text or "father" in text:
            return "family"

        if "school" in text:
            return "education"

        if "travel" in text or "trip" in text:
            return "travel"

        if "laugh" in text:
            return "humor"

        return "memory"