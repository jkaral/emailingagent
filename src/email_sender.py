import os
import smtplib
import ssl

from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid


class EmailSendError(Exception):
    """Raised when an email cannot be sent."""


def _get_required_environment_variable(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise EmailSendError(
            f"Required environment variable {name} is missing."
        )

    return value.strip()


def send_email(
    to_email: str,
    subject: str,
    body: str
) -> str:
    """
    Send one plain-text email.

    Returns the generated Message-ID if successful.
    """
    sender_email = _get_required_environment_variable(
        "EMAIL_ADDRESS"
    )

    email_password = _get_required_environment_variable(
        "EMAIL_PASSWORD"
    )

    smtp_host = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "465"
        )
    )

    sender_name = os.getenv(
        "SENDER_NAME",
        ""
    ).strip()

    use_ssl = (
        os.getenv("SMTP_USE_SSL", "true")
        .strip()
        .lower()
        in {"true", "1", "yes"}
    )

    if "\n" in to_email or "\r" in to_email:
        raise EmailSendError(
            "Recipient address contains invalid characters."
        )

    if "\n" in subject or "\r" in subject:
        raise EmailSendError(
            "Subject contains invalid newline characters."
        )

    message = EmailMessage()

    if sender_name:
        message["From"] = formataddr(
            (sender_name, sender_email)
        )
    else:
        message["From"] = sender_email

    message["To"] = to_email
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=False)

    message_id = make_msgid()

    message["Message-ID"] = message_id

    message.set_content(body)

    ssl_context = ssl.create_default_context()

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port,
                context=ssl_context,
                timeout=30
            ) as smtp:
                smtp.login(
                    sender_email,
                    email_password
                )

                smtp.send_message(message)

        else:
            with smtplib.SMTP(
                smtp_host,
                smtp_port,
                timeout=30
            ) as smtp:
                smtp.ehlo()

                smtp.starttls(
                    context=ssl_context
                )

                smtp.ehlo()

                smtp.login(
                    sender_email,
                    email_password
                )

                smtp.send_message(message)

    except (
        smtplib.SMTPException,
        OSError
    ) as exc:
        raise EmailSendError(
            f"Failed to send email to {to_email}: {exc}"
        ) from exc

    return message_id