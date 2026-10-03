import os
import re


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


APPROVED_VALUES = {
    "true",
    "yes",
    "1",
    "approved"
}


PLACEHOLDER_PATTERNS = [
    "[name]",
    "[first name]",
    "[organization]",
    "[company]",
    "[role]",
    "<name>",
    "<organization>",
    "{{name}}",
    "{{organization}}",
    "TODO",
    "INSERT NAME"
]


def validate_contact(
    contact: dict
) -> list[str]:
    """
    Validate contact information before asking
    the AI to generate anything.

    Returns a list of problems.
    An empty list means validation passed.
    """
    errors = []

    name = contact.get(
        "name",
        ""
    ).strip()

    email = contact.get(
        "email",
        ""
    ).strip()

    reason = contact.get(
        "reason",
        ""
    ).strip()

    approved = contact.get(
        "approved",
        ""
    ).strip().lower()

    if not name:
        errors.append(
            "Contact is missing a name."
        )

    if not email:
        errors.append(
            "Contact is missing an email address."
        )

    elif not EMAIL_PATTERN.fullmatch(email):
        errors.append(
            "Contact has an invalid email address."
        )

    if not reason:
        errors.append(
            "Contact is missing a reason for outreach."
        )

    if approved not in APPROVED_VALUES:
        errors.append(
            "Contact has not been explicitly approved."
        )

    if "\n" in email or "\r" in email:
        errors.append(
            "Email address contains newline characters."
        )

    return errors


def validate_generated_email(
    contact: dict,
    subject: str,
    body: str
) -> list[str]:
    """
    Validate an AI-generated message before sending it.
    """
    errors = []

    max_words = int(
        os.getenv(
            "MAX_EMAIL_WORDS",
            "180"
        )
    )

    max_subject_length = int(
        os.getenv(
            "MAX_SUBJECT_LENGTH",
            "120"
        )
    )

    if not subject.strip():
        errors.append(
            "Generated subject is empty."
        )

    if not body.strip():
        errors.append(
            "Generated email body is empty."
        )

    if (
        "\n" in subject
        or "\r" in subject
    ):
        errors.append(
            "Subject contains newline characters."
        )

    if len(subject) > max_subject_length:
        errors.append(
            f"Subject exceeds {max_subject_length} characters."
        )

    word_count = len(
        body.split()
    )

    if word_count > max_words:
        errors.append(
            f"Email exceeds the {max_words}-word limit."
        )

    lower_body = body.lower()
    lower_subject = subject.lower()

    for placeholder in PLACEHOLDER_PATTERNS:
        placeholder_lower = placeholder.lower()

        if (
            placeholder_lower in lower_body
            or placeholder_lower in lower_subject
        ):
            errors.append(
                f"Unresolved placeholder found: {placeholder}"
            )

    name = contact.get(
        "name",
        ""
    ).strip()

    if name:
        first_name = name.split()[0].lower()

        if first_name not in lower_body:
            errors.append(
                "Recipient's first name does not appear in the email body."
            )

    if body.count("http://") + body.count("https://") > 3:
        errors.append(
            "Email contains an unusually large number of links."
        )

    return errors