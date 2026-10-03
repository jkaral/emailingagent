import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from src.email_sender import send_email
from src.email_writer import generate_email
from src.state import (
    count_sent_today,
    load_state,
    record_failure,
    record_run,
    record_sent,
    save_state,
    was_sent
)
from src.validator import (
    validate_contact,
    validate_generated_email
)


ROOT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_CONTACTS_PATH = (
    ROOT_DIR
    / "data"
    / "contacts.csv"
)


def environment_flag(
    name: str,
    default: bool = False
) -> bool:
    raw_value = os.getenv(
        name
    )

    if raw_value is None:
        return default

    return (
        raw_value.strip().lower()
        in {
            "true",
            "1",
            "yes",
            "on"
        }
    )


def load_contacts() -> list[dict]:
    path = Path(
        os.getenv(
            "CONTACTS_PATH",
            str(DEFAULT_CONTACTS_PATH)
        )
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Contacts file not found: {path}"
        )

    contacts = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        if reader.fieldnames is None:
            raise ValueError(
                "Contacts CSV does not contain column headings."
            )

        for row in reader:
            cleaned_row = {}

            for key, value in row.items():
                if key is None:
                    continue

                cleaned_key = key.strip()

                if isinstance(
                    value,
                    str
                ):
                    cleaned_value = value.strip()
                else:
                    cleaned_value = value

                cleaned_row[
                    cleaned_key
                ] = cleaned_value

            if any(
                cleaned_row.values()
            ):
                contacts.append(
                    cleaned_row
                )

    return contacts


def display_email_preview(
    contact: dict,
    email: dict
) -> None:

    print()
    print("=" * 70)
    print(
        f"PREVIEW FOR: "
        f"{contact.get('name', '')} "
        f"<{contact.get('email', '')}>"
    )
    print("-" * 70)
    print(
        f"Subject: {email['subject']}"
    )
    print()
    print(
        email["body"]
    )
    print("=" * 70)
    print()


def write_github_summary(
    statistics: dict,
    auto_send: bool
) -> None:

    summary_path = os.getenv(
        "GITHUB_STEP_SUMMARY"
    )

    if not summary_path:
        return

    mode = (
        "Automatic sending"
        if auto_send
        else "Preview only"
    )

    summary = f"""# AI Outreach Agent

**Mode:** {mode}

| Result | Count |
|---|---:|
| Contacts considered | {statistics["considered"]} |
| Emails generated | {statistics["generated"]} |
| Emails previewed | {statistics["previewed"]} |
| Emails sent | {statistics["sent"]} |
| Contacts skipped | {statistics["skipped"]} |
| Failures | {statistics["failed"]} |
"""

    with open(
        summary_path,
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            summary
        )


def main() -> None:
    load_dotenv(
        ROOT_DIR / ".env"
    )

    auto_send = environment_flag(
        "AUTO_SEND",
        default=False
    )

    max_emails_per_day = int(
        os.getenv(
            "MAX_EMAILS_PER_DAY",
            "5"
        )
    )

    contacts = load_contacts()

    state = load_state()

    statistics = {
        "considered": 0,
        "generated": 0,
        "previewed": 0,
        "sent": 0,
        "skipped": 0,
        "failed": 0
    }

    emails_sent_today = count_sent_today(
        state
    )

    print()
    print("AI Outreach Agent")
    print("-----------------")

    if auto_send:
        print("Mode: AUTOMATIC SENDING")
    else:
        print("Mode: PREVIEW ONLY")

    print(
        f"Daily sending limit: "
        f"{max_emails_per_day}"
    )

    print(
        f"Already sent today: "
        f"{emails_sent_today}"
    )

    print()

    for contact in contacts:

        statistics[
            "considered"
        ] += 1

        contact_name = contact.get(
            "name",
            "Unknown"
        )

        contact_email = contact.get(
            "email",
            ""
        )

        print(
            f"Processing: "
            f"{contact_name} "
            f"<{contact_email}>"
        )

        if (
            auto_send
            and emails_sent_today
            >= max_emails_per_day
        ):
            print(
                "Daily sending limit reached."
            )

            break

        contact_errors = validate_contact(
            contact
        )

        if contact_errors:
            statistics[
                "skipped"
            ] += 1

            print("Skipped:")

            for error in contact_errors:
                print(
                    f"  - {error}"
                )

            continue

        if was_sent(
            state,
            contact_email
        ):
            statistics[
                "skipped"
            ] += 1

            print(
                "Skipped: this recipient "
                "has already been emailed."
            )

            continue

        try:
            generated_email = generate_email(
                contact
            )

            statistics[
                "generated"
            ] += 1

        except Exception as exc:
            statistics[
                "failed"
            ] += 1

            print(
                f"Generation failed: {exc}"
            )

            record_failure(
                state,
                contact,
                str(exc)
            )

            save_state(
                state
            )

            continue

        email_errors = (
            validate_generated_email(
                contact,
                generated_email[
                    "subject"
                ],
                generated_email[
                    "body"
                ]
            )
        )

        if email_errors:
            statistics[
                "failed"
            ] += 1

            print(
                "Generated email failed validation:"
            )

            for error in email_errors:
                print(
                    f"  - {error}"
                )

            record_failure(
                state,
                contact,
                "; ".join(email_errors)
            )

            save_state(
                state
            )

            continue

        if not auto_send:
            display_email_preview(
                contact,
                generated_email
            )

            statistics[
                "previewed"
            ] += 1

            continue

        try:
            message_id = send_email(
                contact_email,
                generated_email[
                    "subject"
                ],
                generated_email[
                    "body"
                ]
            )

            record_sent(
                state,
                contact,
                generated_email[
                    "subject"
                ],
                message_id
            )

            # Save immediately after every successful send.
            # This reduces the chance of duplicate emails
            # if the program crashes later.
            save_state(
                state
            )

            emails_sent_today += 1

            statistics[
                "sent"
            ] += 1

            print(
                "Email sent successfully."
            )

        except Exception as exc:
            statistics[
                "failed"
            ] += 1

            print(
                f"Sending failed: {exc}"
            )

            record_failure(
                state,
                contact,
                str(exc)
            )

            save_state(
                state
            )

    record_run(
        state,
        statistics,
        auto_send
    )

    save_state(
        state
    )

    write_github_summary(
        statistics,
        auto_send
    )

    print()
    print("Run complete")
    print("------")

    for key, value in statistics.items():
        print(
            f"{key.capitalize()}: {value}"
        )

#Main Block for testings
if __name__ == "__main__":
    main()