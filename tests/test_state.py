from src.state import (
    was_sent,
    record_sent,
    get_contact_record
)


def test_new_contact_has_not_been_sent():
    state = {
        "contacts": {},
        "runs": []
    }

    assert was_sent(
        state,
        "jane@example.com"
    ) is False


def test_record_sent():
    state = {
        "contacts": {},
        "runs": []
    }

    contact = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "organization": "Example Lab"
    }

    record_sent(
        state,
        contact,
        "Research question",
        "<test-message-id>"
    )

    assert was_sent(
        state,
        "jane@example.com"
    ) is True


def test_email_matching_is_case_insensitive():
    state = {
        "contacts": {},
        "runs": []
    }

    contact = {
        "name": "Jane Smith",
        "email": "Jane@Example.com",
        "organization": "Example Lab"
    }

    record_sent(
        state,
        contact,
        "Research question",
        "<test-message-id>"
    )

    assert was_sent(
        state,
        "jane@example.com"
    ) is True


def test_contact_record_can_be_retrieved():
    state = {
        "contacts": {},
        "runs": []
    }

    contact = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "organization": "Example Lab"
    }

    record_sent(
        state,
        contact,
        "Research question",
        "<test-message-id>"
    )

    record = get_contact_record(
        state,
        "jane@example.com"
    )

    assert record["name"] == "Jane Smith"
    assert record["status"] == "sent"
    assert record["subject"] == "Research question"