from flask import Blueprint, request, jsonify

# definition of story blueprint
story_bp = Blueprint("stories", __name__)


@story_bp.route("", methods=["GET"])
def get_stories():
    """
    Retrieve all life stories.
    Returns:
        JSON: List of life stories
        HTTP 200: Success
    """
    return jsonify([])


@story_bp.route("/<int:story_id>", methods=["GET"])
def get_story(story_id):
    """
    Retrieve a single life story by ID.
    Returns:
        JSON: Story object
        HTTP 200: Success
        HTTP 404: Story not found
    """
    return jsonify({"story_id": story_id})


@story_bp.route("", methods=["POST"])
def create_story():
    """
    Create a new life story.
    Request Body:
        title (str): Story title
        story_text (str): Story content
        profile_id (int): Associated memorial profile
        emotion_tag (str): Emotion classification
        life_period (str): Life phase
    Returns:
        JSON: Created story
        HTTP 201: Created
    """
    data = request.get_json()
    return jsonify(data), 201


@story_bp.route("/<int:story_id>", methods=["PUT"])
def update_story(story_id):
    """
    Update an existing life story.
    Request Body: Fields to update
    Returns:
        JSON: Updated story
        HTTP 200: Success
    """
    data = request.get_json()
    return jsonify({"story_id": story_id, "updated": data})


@story_bp.route("/<int:story_id>", methods=["DELETE"])
def delete_story(story_id):
    """
    Delete a life story.
    Returns:
        JSON: Delete confirmation
        HTTP 200: Success
    """
    return jsonify({"message": f"Story {story_id} deleted"})