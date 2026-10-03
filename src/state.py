import json
import os

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = ROOT_DIR / "state" / "sent.json"


EMPTY_STATE = {
    "contacts": {},
    "runs": []
}


def _state_path() -> Path:
    return Path(
        os.getenv(
            "STATE_PATH",
            str(DEFAULT_STATE_PATH)
        )
    )


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_state() -> dict:
    """Load the agent's persistent state."""
    path = _state_path()

    if not path.exists():
        return deepcopy(EMPTY_STATE)

    raw = path.read_text(
        encoding="utf-8"
    ).strip()

    if not raw:
        return deepcopy(EMPTY_STATE)

    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"State file contains invalid JSON: {path}"
        ) from exc

    if not isinstance(state, dict):
        raise ValueError(
            "State file must contain a JSON object."
        )

    state.setdefault(
        "contacts",
        {}
    )

    state.setdefault(
        "runs",
        []
    )

    return state


def save_state(state: dict) -> None:
    """
    Save state using an atomic replacement.

    This helps reduce the chance of corrupting the file
    if execution stops while writing.
    """
    path = _state_path()

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False
        )
        + "\n",
        encoding="utf-8"
    )

    temporary_path.replace(path)


def get_contact_record(
    state: dict,
    email: str
) -> dict | None:
    return state.get(
        "contacts",
        {}
    ).get(
        _normalize_email(email)
    )


def was_sent(
    state: dict,
    email: str
) -> bool:
    record = get_contact_record(
        state,
        email
    )

    if record is None:
        return False

    return record.get("status") == "sent"


def count_sent_today(state: dict) -> int:
    """
    Count successful emails sent during the current local day.
    """
    timezone_name = os.getenv(
        "AGENT_TIMEZONE",
        "America/Toronto"
    )

    local_timezone = ZoneInfo(
        timezone_name
    )

    today = datetime.now(
        local_timezone
    ).date()

    total = 0

    for record in state.get(
        "contacts",
        {}
    ).values():

        if record.get("status") != "sent":
            continue

        sent_at = record.get(
            "sent_at"
        )

        if not sent_at:
            continue

        try:
            sent_datetime = datetime.fromisoformat(
                sent_at
            )

            local_date = sent_datetime.astimezone(
                local_timezone
            ).date()

        except ValueError:
            continue

        if local_date == today:
            total += 1

    return total


def record_sent(
    state: dict,
    contact: dict,
    subject: str,
    message_id: str
) -> None:
    email = _normalize_email(
        contact["email"]
    )

    state.setdefault(
        "contacts",
        {}
    )

    state["contacts"][email] = {
        "name": contact.get(
            "name",
            ""
        ),
        "email": email,
        "organization": contact.get(
            "organization",
            ""
        ),
        "status": "sent",
        "sent_at": _now_utc().isoformat(),
        "subject": subject,
        "message_id": message_id,
        "followups": 0
    }


def record_failure(
    state: dict,
    contact: dict,
    error: str
) -> None:
    email = _normalize_email(
        contact.get(
            "email",
            ""
        )
    )

    if not email:
        return

    state.setdefault(
        "contacts",
        {}
    )

    existing = state["contacts"].get(
        email,
        {}
    )

    # Never overwrite evidence that an email
    # was successfully sent.
    if existing.get("status") == "sent":
        return

    state["contacts"][email] = {
        "name": contact.get(
            "name",
            ""
        ),
        "email": email,
        "organization": contact.get(
            "organization",
            ""
        ),
        "status": "failed",
        "last_failure_at": _now_utc().isoformat(),
        "error": str(error)
    }


def record_run(
    state: dict,
    statistics: dict,
    auto_send: bool
) -> None:
    state.setdefault(
        "runs",
        []
    )

    state["runs"].append(
        {
            "completed_at": _now_utc().isoformat(),
            "auto_send": auto_send,
            "statistics": statistics
        }
    )

    # Prevent this section of the file
    # from growing forever.
    state["runs"] = state["runs"][-50:]