from flask import Blueprint, request, jsonify
from app.services.chatbot_prompt_service import ChatbotPromptService

chatbot_prompt_bp = Blueprint("prompts", __name__)
chatbot_prompt_service = ChatbotPromptService()


def serialize_prompt(prompt):
    """
    Convert a ChatbotPrompt object into a JSON-serializable dictionary.
    Returns:
        dict: Serialized prompt data.
    """
    return {
        "prompt_id": prompt.prompt_id,
        "category": prompt.category,
        "question_text": prompt.question_text,
        "life_period": prompt.life_period,
        "is_active": prompt.is_active,
        "sort_order": prompt.sort_order,
        "created_at": prompt.created_at.isoformat(),
    }


@chatbot_prompt_bp.route("", methods=["GET"])
def get_prompts():
    """
    Retrieve all chatbot prompts.
    Returns:
        JSON: List of prompts.
        HTTP 200: Success.
    """
    prompts = chatbot_prompt_service.get_prompts()
    return jsonify([serialize_prompt(prompt) for prompt in prompts]), 200


@chatbot_prompt_bp.route("/active", methods=["GET"])
def get_active_prompts():
    """
    Retrieve all active chatbot prompts.
    Returns:
        JSON: List of active prompts.
        HTTP 200: Success.
    """
    prompts = chatbot_prompt_service.get_active_prompts()
    return jsonify([serialize_prompt(prompt) for prompt in prompts]), 200


@chatbot_prompt_bp.route("/<int:prompt_id>", methods=["GET"])
def get_prompt(prompt_id):
    """
    Retrieve a single chatbot prompt by ID.
    Returns:
        JSON: Prompt object.
        HTTP 200: Success.
        HTTP 404: Prompt not found.
    """
    prompt = chatbot_prompt_service.get_prompt_by_id(prompt_id)

    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404

    return jsonify(serialize_prompt(prompt)), 200


@chatbot_prompt_bp.route("/category/<string:category>", methods=["GET"])
def get_prompts_by_category(category):
    """
    Retrieve prompts by category.
    Returns:
        JSON: List of prompts for a category.
        HTTP 200: Success.
    """
    prompts = chatbot_prompt_service.get_prompts_by_category(category)
    return jsonify([serialize_prompt(prompt) for prompt in prompts]), 200


@chatbot_prompt_bp.route("", methods=["POST"])
def create_prompt():
    """
    Create a new chatbot prompt.
    Request Body:
        category (str): Prompt category.
        question_text (str): Prompt text.
        life_period (str): Related life period.
        is_active (bool): Whether prompt is active.
        sort_order (int): Prompt order.
    Returns:
        JSON: Created prompt.
        HTTP 201: Created.
    """
    data = request.get_json()
    prompt = chatbot_prompt_service.create_prompt(data)
    return jsonify(serialize_prompt(prompt)), 201


@chatbot_prompt_bp.route("/<int:prompt_id>", methods=["PUT"])
def update_prompt(prompt_id):
    """
    Update a chatbot prompt.
    Returns:
        JSON: Updated prompt.
        HTTP 200: Success.
        HTTP 404: Prompt not found.
    """
    data = request.get_json()
    prompt = chatbot_prompt_service.update_prompt(prompt_id, data)

    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404

    return jsonify(serialize_prompt(prompt)), 200


@chatbot_prompt_bp.route("/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    """
    Delete a chatbot prompt.
    Returns:
        JSON: Confirmation message.
        HTTP 200: Success.
        HTTP 404: Prompt not found.
    """
    deleted = chatbot_prompt_service.delete_prompt(prompt_id)

    if not deleted:
        return jsonify({"error": "Prompt not found"}), 404

    return jsonify({"message": "Prompt deleted successfully"}), 200
