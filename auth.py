"""
auth.py - Authentication, signup helpers, and field validation.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Any

from db import get_connection


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")
SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


class AccountDisabledError(ValueError):
    pass


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return digest, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    digest, _ = hash_password(password, salt)
    return hmac.compare_digest(digest, password_hash)


def validate_email(email: str) -> str | None:
    if not email or not EMAIL_RE.match(email.strip()):
        return "Enter a valid email address."
    return None


def validate_password(password: str) -> str | None:
    if len(password or "") < 8:
        return "Password must be at least 8 characters long."
    if not any(ch.isupper() for ch in password):
        return "Password must include at least one uppercase letter."
    if not any(ch.isdigit() for ch in password):
        return "Password must include at least one digit."
    if not SPECIAL_RE.search(password):
        return "Password must include at least one special character."
    return None


def validate_age(value: str, minimum: int) -> str | None:
    try:
        age = int(value)
    except (TypeError, ValueError):
        return "Age must be a whole number."
    if age < minimum or age > 100:
        return f"Age must be between {minimum} and 100."
    return None


def validate_gpa(value: str) -> str | None:
    try:
        gpa = float(value)
    except (TypeError, ValueError):
        return "GPA must be a number."
    if gpa < 0.0 or gpa > 4.0:
        return "GPA must be between 0.0 and 4.0."
    return None


def validate_phone(value: str) -> str | None:
    if not value or not PHONE_RE.match(value.strip()):
        return "Enter a valid phone number."
    return None


def validate_year(value: str) -> str | None:
    try:
        year = int(value)
    except (TypeError, ValueError):
        return "Year must be a whole number."
    if year < 1950 or year > 2100:
        return "Year must be between 1950 and 2100."
    return None


def validate_salary(value: str) -> str | None:
    try:
        salary = float(value)
    except (TypeError, ValueError):
        return "Salary must be a number."
    if salary < 0:
        return "Salary cannot be negative."
    return None


def _create_user(email: str, password: str, role: str) -> int:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email.strip(),)
        ).fetchone()
        if existing:
            raise ValueError("An account with this email already exists.")

        password_hash, salt = hash_password(password)
        cur = conn.execute(
            "INSERT INTO users(email, password_hash, salt, role) VALUES(?,?,?,?)",
            (email.strip(), password_hash, salt, role),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _get_role_id(conn: Any, user_id: int, role: str) -> int | None:
    mapping = {
        "student": ("students", "student_id"),
        "professor": ("professors", "prof_id"),
        "lab_attendant": ("lab_attendants", "lab_id"),
    }
    if role not in mapping:
        return None
    table, key = mapping[role]
    row = conn.execute(
        f"SELECT {key} FROM {table} WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return row[key] if row else None


def login(email: str, password: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip(),),
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"], row["salt"]):
            raise ValueError("Invalid email or password.")
        if not row["is_active"]:
            raise AccountDisabledError("This account has been disabled by the administrator.")

        user = dict(row)
        role = user["role"]
        role_id = _get_role_id(conn, user["user_id"], role)
        return user, role_id
    finally:
        conn.close()


def signup_student(data: dict[str, str]) -> int:
    user_id = _create_user(data["email"], data["password"], "student")
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO students
               (user_id, first_name, last_name, age, gender, department, gpa, city, phone, enrollment_year)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                data["first_name"].strip(),
                data["last_name"].strip(),
                int(data["age"]),
                data["gender"],
                data["department"],
                float(data["gpa"]),
                data["city"].strip(),
                data["phone"].strip(),
                int(data["enrollment_year"]),
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        raise
    finally:
        conn.close()


def signup_professor(data: dict[str, str]) -> int:
    user_id = _create_user(data["email"], data["password"], "professor")
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO professors
               (user_id, first_name, last_name, age, gender, department, salary, city, phone, joining_year)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                data["first_name"].strip(),
                data["last_name"].strip(),
                int(data["age"]),
                data["gender"],
                data["department"],
                float(data["salary"]),
                data["city"].strip(),
                data["phone"].strip(),
                int(data["joining_year"]),
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        raise
    finally:
        conn.close()


def signup_lab_attendant(data: dict[str, str]) -> int:
    user_id = _create_user(data["email"], data["password"], "lab_attendant")
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO lab_attendants
               (user_id, first_name, last_name, age, gender, lab_name, shift, city, phone, joining_year)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                data["first_name"].strip(),
                data["last_name"].strip(),
                int(data["age"]),
                data["gender"],
                data["lab_name"],
                data["shift"],
                data["city"].strip(),
                data["phone"].strip(),
                int(data["joining_year"]),
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        raise
    finally:
        conn.close()
