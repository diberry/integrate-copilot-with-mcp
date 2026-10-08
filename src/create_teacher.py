import argparse
import getpass
import json
from pathlib import Path

from teacher_auth import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a teacher login")
    parser.add_argument("username")
    args = parser.parse_args()

    username = args.username.strip()
    if not username:
        parser.error("username cannot be empty")

    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("passwords do not match")

    path = Path(__file__).parent / "teachers.json"
    data = json.loads(path.read_text()) if path.exists() else {"teachers": []}
    teachers = data["teachers"]
    updated_teacher = {
        "username": username,
        "password_hash": hash_password(password),
    }

    for index, teacher in enumerate(teachers):
        if teacher["username"] == username:
            teachers[index] = updated_teacher
            break
    else:
        teachers.append(updated_teacher)

    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(data, indent=2) + "\n")
    temporary_path.replace(path)
    print(f"Teacher {username!r} saved to {path}")


if __name__ == "__main__":
    main()
