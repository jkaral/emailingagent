import pytest

from src.email_writer import (
    _parse_response,
    EmailGenerationError
)


def test_parse_valid_ai_response():
    response = r'''
    {
        "subject": "Research question",
        "body": "Hi Jane,\\n\\nI wanted to reach out about your research."
    }
    '''

    result = _parse_response(response)

    assert result["subject"] == "Research question"
    assert "Hi Jane" in result["body"]


def test_parse_response_with_code_fence():
    response = '''```json
{
    "subject": "Research question",
    "body": "Hi Jane"
}
```'''

    result = _parse_response(response)

    assert result["subject"] == "Research question"


def test_invalid_json_is_rejected():
    response = "Subject: Research question"

    with pytest.raises(EmailGenerationError):
        _parse_response(response)


def test_missing_subject_is_rejected():
    response = r'''
    {
        "body": "Hi Jane"
    }
    '''

    with pytest.raises(EmailGenerationError):
        _parse_response(response)


def test_missing_body_is_rejected():
    response = '''
    {
        "subject": "Research question"
    }
    '''

    with pytest.raises(EmailGenerationError):
        _parse_response(response)