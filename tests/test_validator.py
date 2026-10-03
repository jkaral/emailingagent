from src.validator import (
    validate_contact,
    validate_generated_email
)


def test_valid_contact():
    contact = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "organization": "Example Lab",
        "role": "Professor",
        "reason": "Her research relates to computer vision.",
        "notes": "",
        "approved": "yes"
    }

    errors = validate_contact(contact)

    assert errors == []


def test_contact_without_approval():
    contact = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "organization": "Example Lab",
        "role": "Professor",
        "reason": "Her research relates to computer vision.",
        "notes": "",
        "approved": "no"
    }

    errors = validate_contact(contact)

    assert "Contact has not been explicitly approved." in errors


def test_contact_without_email():
    contact = {
        "name": "Jane Smith",
        "email": "",
        "reason": "Research outreach.",
        "approved": "yes"
    }

    errors = validate_contact(contact)

    assert "Contact is missing an email address." in errors


def test_invalid_email():
    contact = {
        "name": "Jane Smith",
        "email": "this-is-not-an-email",
        "reason": "Research outreach.",
        "approved": "yes"
    }

    errors = validate_contact(contact)

    assert "Contact has an invalid email address." in errors


def test_generated_email_is_valid():
    contact = {
        "name": "Jane Smith"
    }

    errors = validate_generated_email(
        contact,
        "Question about your research",
        "Hi Jane,\n\nI recently came across your work and wanted to reach out."
    )

    assert errors == []


def test_generated_email_without_name():
    contact = {
        "name": "Jane Smith"
    }

    errors = validate_generated_email(
        contact,
        "Question about your research",
        "Hello,\n\nI recently came across your work."
    )

    assert (
        "Recipient's first name does not appear in the email body."
        in errors
    )


def test_placeholder_is_rejected():
    contact = {
        "name": "Jane Smith"
    }

    errors = validate_generated_email(
        contact,
        "Research at [organization]",
        "Hi Jane,\n\nI was interested in your work at [organization]."
    )

    assert len(errors) > 0