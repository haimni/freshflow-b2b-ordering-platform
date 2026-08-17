"""Set a local development user's password securely."""

from argparse import ArgumentParser
from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def parse_arguments():
    """Read the target email from the command line."""

    parser = ArgumentParser(
        description="Set a FreshFlow development user password."
    )

    parser.add_argument(
        "email",
        help="Email address of the existing user",
    )

    return parser.parse_args()


def main() -> None:
    """Prompt for a password and update its Argon2 hash."""

    arguments = parse_arguments()
    normalized_email = arguments.email.strip().lower()

    password = getpass("New password: ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    if len(password) < 12:
        raise SystemExit(
            "Development passwords must contain at least 12 characters."
        )

    with SessionLocal.begin() as db:
        statement = select(User).where(
            User.email == normalized_email
        )

        user = db.scalar(statement)

        if user is None:
            raise SystemExit(
                f"User not found: {normalized_email}"
            )

        user.password_hash = hash_password(password)

    print(f"Password updated for {normalized_email}")


if __name__ == "__main__":
    main()