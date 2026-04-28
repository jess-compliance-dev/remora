from flask import current_app
from flask_mail import Message

from app.extensions.mail import mail


def send_confirmation_email(user_email, confirm_url):
    """
    Sends an account confirmation email.

    In local/dev mode, if MAIL_SUPPRESS_SEND=true, the confirmation URL is logged
    instead of being sent via SMTP.
    """
    suppress_send = current_app.config.get("MAIL_SUPPRESS_SEND", False)

    if suppress_send:
        current_app.logger.warning(
            "DEV confirmation link for %s: %s",
            user_email,
            confirm_url,
        )
        return

    msg = Message(
        subject="Confirm your Remora account",
        recipients=[user_email],
        body=f"""Welcome to Remora.

Please confirm your account by opening this link:

{confirm_url}

If you did not create this account, you can ignore this email.
""",
    )

    mail.send(msg)