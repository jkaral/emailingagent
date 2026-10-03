import os

from dotenv import load_dotenv

from src.email_sender import send_email


load_dotenv()


def main() -> None:
    sender_address = os.getenv("EMAIL_ADDRESS")

    if not sender_address:
        raise ValueError(
            "EMAIL_ADDRESS is missing from your .env file."
        )

    subject = "Email Agent SMTP Test"

    body = """Hello,

This is my first test email sent automatically from my Python email agent.

If I received this message, Gmail SMTP is working correctly.
"""

    print("Preparing test email...")
    print(f"From: {sender_address}")
    print(f"To: {sender_address}")
    print(f"Subject: {subject}")
    print()

    confirmation = input(
        "Type SEND to send this email to yourself: "
    )

    if confirmation != "SEND":
        print("Cancelled. No email was sent.")
        return

    print("Connecting to Gmail...")

    message_id = send_email(
        to_email=sender_address,
        subject=subject,
        body=body
    )

    print("Email sent successfully.")
    print(f"Message ID: {message_id}")


if __name__ == "__main__":
    main()