import hashlib
import math
import secrets
import sqlite3

from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

from models import Lecturer, CampusAdministrator, SystemOperator
from policies import CAMPUS_POLICIES, STARTER_RESOURCES


DATABASE_PATH = Path(__file__).resolve().parent / "smart_campus.db"

PASSWORD_ITERATIONS = 200_000

class Database:

    def __init__(self, database_path=None):
        self.database_path = Path(database_path or DATABASE_PATH)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_database()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _hash_password(password):
        salt = secrets.token_hex(16)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            PASSWORD_ITERATIONS,
        ).hex()

        return salt, password_hash

    @staticmethod
    def _verify_password(password, salt, stored_hash):
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            PASSWORD_ITERATIONS,
        ).hex()

        return secrets.compare_digest(calculated_hash, stored_hash)

    def initialize_database(self):

        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS campuses (
                    campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    max_duration_hours INTEGER NOT NULL
                        CHECK (max_duration_hours > 0),
                    opening_time TEXT NOT NULL,
                    closing_time TEXT NOT NULL,
                    max_days_ahead INTEGER NOT NULL
                        CHECK (max_days_ahead > 0),
                    policy_description TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (
                        role IN (
                            'Lecturer',
                            'Campus Administrator',
                            'System Operator'
                        )
                    ),
                    campus_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campus_id)
                        REFERENCES campuses(campus_id),
                    CHECK (
                        role != 'Campus Administrator'
                        OR campus_id IS NOT NULL
                    )
                );

                CREATE TABLE IF NOT EXISTS resources (
                    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_code TEXT NOT NULL UNIQUE,
                    campus_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1
                        CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campus_id)
                        REFERENCES campuses(campus_id)
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    resource_id INTEGER NOT NULL,
                    campus_id INTEGER NOT NULL,
                    booking_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    duration_hours REAL NOT NULL
                        CHECK (duration_hours > 0),
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK (
                            status IN ('active', 'cancelled', 'completed')
                        ),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (resource_id)
                        REFERENCES resources(resource_id),
                    FOREIGN KEY (campus_id)
                        REFERENCES campuses(campus_id)
                );

                CREATE INDEX IF NOT EXISTS idx_booking_resource_date
                    ON bookings(resource_id, booking_date, status);

                CREATE INDEX IF NOT EXISTS idx_booking_user
                    ON bookings(user_id, status);

                CREATE INDEX IF NOT EXISTS idx_booking_campus
                    ON bookings(campus_id, status);
                """
            )

            for policy in CAMPUS_POLICIES.values():
                connection.execute(
                    """
                    INSERT OR IGNORE INTO campuses (
                        name,
                        max_duration_hours,
                        opening_time,
                        closing_time,
                        max_days_ahead,
                        policy_description
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        policy.campus_name,
                        policy.max_duration_hours,
                        policy.opening_time,
                        policy.closing_time,
                        policy.max_days_ahead,
                        policy.description,
                    ),
                )

            for campus_name, resources in STARTER_RESOURCES.items():
                campus = connection.execute(
                    "SELECT campus_id FROM campuses WHERE name = ?",
                    (campus_name,),
                ).fetchone()

                if campus is None:
                    continue

                for resource in resources:
                    code, name, category, description = resource

                    connection.execute(
                        """
                        INSERT OR IGNORE INTO resources (
                            resource_code,
                            campus_id,
                            name,
                            category,
                            description
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            code,
                            campus["campus_id"],
                            name,
                            category,
                            description,
                        ),
                    )

            demo_accounts = [
                (
                    "Durban Administrator",
                    "admin.durban@campus.test",
                    "Admin123!",
                    "Campus Administrator",
                    "Durban Campus",
                ),
                (
                    "Johannesburg Administrator",
                    "admin.johannesburg@campus.test",
                    "Admin123!",
                    "Campus Administrator",
                    "Johannesburg Campus",
                ),
                (
                    "Cape Town Administrator",
                    "admin.capetown@campus.test",
                    "Admin123!",
                    "Campus Administrator",
                    "Cape Town Campus",
                ),
                (
                    "System Operator",
                    "operator@campus.test",
                    "Operator123!",
                    "System Operator",
                    None,
                ),
            ]

            for name, email, password, role, campus_name in demo_accounts:
                existing_user = connection.execute(
                    "SELECT user_id FROM users WHERE email = ?",
                    (email,),
                ).fetchone()

                if existing_user:
                    continue

                campus_id = None

                if campus_name:
                    campus = connection.execute(
                        "SELECT campus_id FROM campuses WHERE name = ?",
                        (campus_name,),
                    ).fetchone()

                    if campus is None:
                        raise ValueError(
                            f"Campus not found: {campus_name}"
                        )

                    campus_id = campus["campus_id"]

                salt, password_hash = self._hash_password(password)

                connection.execute(
                    """
                    INSERT INTO users (
                        full_name,
                        email,
                        password_hash,
                        password_salt,
                        role,
                        campus_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        email,
                        password_hash,
                        salt,
                        role,
                        campus_id,
                    ),
                )

    def register_lecturer(self, full_name, email, password):
        full_name = full_name.strip()
        email = email.strip().lower()

        if not full_name:
            raise ValueError("Full name is required.")

        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("Enter a valid email address.")

        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")

        salt, password_hash = self._hash_password(password)

        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        full_name,
                        email,
                        password_hash,
                        password_salt,
                        role,
                        campus_id
                    )
                    VALUES (?, ?, ?, ?, 'Lecturer', NULL)
                    """,
                    (
                        full_name,
                        email,
                        password_hash,
                        salt,
                    ),
                )

                user_id = cursor.lastrowid

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "An account with that email already exists."
            ) from error

        return Lecturer(
            user_id,
            full_name,
            email,
            password_hash,
        )

    def authenticate_user(self, email, password):
        email = email.strip().lower()

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    u.*,
                    c.name AS campus_name
                FROM users u
                LEFT JOIN campuses c ON c.campus_id = u.campus_id
                WHERE u.email = ?
                """,
                (email,),
            ).fetchone()

        if row is None:
            return None

        if not self._verify_password(
            password,
            row["password_salt"],
            row["password_hash"],
        ):
            return None

        role = row["role"]
        user_id = row["user_id"]
        name = row["full_name"]
        stored_email = row["email"]
        stored_hash = row["password_hash"]

        if role == "Lecturer":
            return Lecturer(
                user_id,
                name,
                stored_email,
                stored_hash,
            )

        if role == "Campus Administrator":
            return CampusAdministrator(
                user_id,
                name,
                stored_email,
                stored_hash,
                row["campus_name"],
            )

        if role == "System Operator":
            return SystemOperator(
                user_id,
                name,
                stored_email,
                stored_hash,
            )

        return None

    def get_campuses(self):
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM campuses ORDER BY name"
            ).fetchall()

        return [dict(row) for row in rows]

    def get_campus_policy(self, campus_name):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM campuses WHERE name = ?",
                (campus_name,),
            ).fetchone()

        if row is None:
            raise ValueError("Campus not found.")

        return dict(row)

    def get_resources(self, campus_name, include_inactive=False):
        query = """
            SELECT
                r.*,
                c.name AS campus_name
            FROM resources r
            JOIN campuses c ON c.campus_id = r.campus_id
            WHERE c.name = ?
        """

        if not include_inactive:
            query += " AND r.is_active = 1"

        query += " ORDER BY r.name"

        with self._connection() as connection:
            rows = connection.execute(
                query,
                (campus_name,),
            ).fetchall()

        return [dict(row) for row in rows]

    def add_resource(
        self,
        campus_name,
        resource_code,
        name,
        category,
        description="",
    ):
        campus_name = campus_name.strip()
        resource_code = resource_code.strip().upper()
        name = name.strip()
        category = category.strip()
        description = description.strip()

        if not resource_code or not name or not category:
            raise ValueError(
                "Resource code, name and category are required."
            )

        try:
            with self._connection() as connection:
                campus = connection.execute(
                    "SELECT campus_id FROM campuses WHERE name = ?",
                    (campus_name,),
                ).fetchone()

                if campus is None:
                    raise ValueError("Campus not found.")

                cursor = connection.execute(
                    """
                    INSERT INTO resources (
                        resource_code,
                        campus_id,
                        name,
                        category,
                        description
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        resource_code,
                        campus["campus_id"],
                        name,
                        category,
                        description,
                    ),
                )

                return cursor.lastrowid

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "That resource code already exists or is invalid."
            ) from error

    def update_resource(
        self,
        resource_code,
        name,
        category,
        description="",
    ):
        resource_code = resource_code.strip().upper()
        name = name.strip()
        category = category.strip()

        if not name or not category:
            raise ValueError("Resource name and category are required.")

        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE resources
                SET name = ?, category = ?, description = ?
                WHERE resource_code = ? AND is_active = 1
                """,
                (
                    name,
                    category,
                    description.strip(),
                    resource_code,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Active resource not found. Check its resource code."
                )

    def remove_resource(self, resource_code):
        resource_code = resource_code.strip().upper()

        with self._connection() as connection:
            resource = connection.execute(
                """
                SELECT resource_id
                FROM resources
                WHERE resource_code = ? AND is_active = 1
                """,
                (resource_code,),
            ).fetchone()

            if resource is None:
                raise ValueError("Active resource not found.")

            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            future_booking = connection.execute(
                """
                SELECT booking_id
                FROM bookings
                WHERE resource_id = ?
                    AND status = 'active'
                    AND booking_date || ' ' || start_time >= ?
                LIMIT 1
                """,
                (resource["resource_id"], now),
            ).fetchone()

            if future_booking:
                raise ValueError(
                    "This resource has a future active booking. "
                    "Cancel or resolve that booking first."
                )

            connection.execute(
                """
                UPDATE resources
                SET is_active = 0
                WHERE resource_id = ?
                """,
                (resource["resource_id"],),
            )

    def create_booking(
        self,
        user_id,
        resource_code,
        booking_date,
        start_time,
        duration_hours,
    ):
        resource_code = resource_code.strip().upper()

        try:
            start = datetime.strptime(
                f"{booking_date} {start_time}",
                "%Y-%m-%d %H:%M",
            )
            duration = float(duration_hours)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Use a valid date, 24-hour time and booking duration."
            ) from error

        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Duration must be a positive number.")

        end = start + timedelta(hours=duration)

        if start.date() != end.date():
            raise ValueError(
                "A booking cannot extend into the following day."
            )

        with self._connection() as connection:
            user = connection.execute(
                "SELECT role FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            if user is None or user["role"] != "Lecturer":
                raise ValueError("Only registered lecturers can book.")

            resource = connection.execute(
                """
                SELECT resource_id, campus_id
                FROM resources
                WHERE resource_code = ? AND is_active = 1
                """,
                (resource_code,),
            ).fetchone()

            if resource is None:
                raise ValueError(
                    "Resource not found or no longer available."
                )

            existing_bookings = connection.execute(
                """
                SELECT start_time, duration_hours
                FROM bookings
                WHERE resource_id = ?
                    AND booking_date = ?
                    AND status = 'active'
                """,
                (
                    resource["resource_id"],
                    booking_date,
                ),
            ).fetchall()

            for existing in existing_bookings:
                existing_start = datetime.strptime(
                    f"{booking_date} {existing['start_time']}",
                    "%Y-%m-%d %H:%M",
                )

                existing_end = existing_start + timedelta(
                    hours=existing["duration_hours"]
                )

                overlaps = (
                    start < existing_end
                    and existing_start < end
                )

                if overlaps:
                    raise ValueError(
                        "This resource already has an overlapping booking."
                    )

            cursor = connection.execute(
                """
                INSERT INTO bookings (
                    user_id,
                    resource_id,
                    campus_id,
                    booking_date,
                    start_time,
                    duration_hours
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    resource["resource_id"],
                    resource["campus_id"],
                    booking_date,
                    start_time,
                    duration,
                ),
            )

            return cursor.lastrowid

    def get_bookings(
        self,
        user_id=None,
        campus_name=None,
        status=None,
    ):
        query = """
            SELECT
                b.*,
                u.full_name AS lecturer_name,
                u.email AS lecturer_email,
                r.resource_code,
                r.name AS resource_name,
                c.name AS campus_name
            FROM bookings b
            JOIN users u ON u.user_id = b.user_id
            JOIN resources r ON r.resource_id = b.resource_id
            JOIN campuses c ON c.campus_id = b.campus_id
        """

        conditions = []
        parameters = []

        if user_id is not None:
            conditions.append("b.user_id = ?")
            parameters.append(user_id)

        if campus_name is not None:
            conditions.append("c.name = ?")
            parameters.append(campus_name)

        if status is not None:
            allowed_statuses = {"active", "cancelled", "completed"}

            if status not in allowed_statuses:
                raise ValueError("Invalid booking status.")

            conditions.append("b.status = ?")
            parameters.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY b.booking_date, b.start_time"

        with self._connection() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return [dict(row) for row in rows]

    def cancel_booking(self, booking_id, user_id=None):
        with self._connection() as connection:
            booking = connection.execute(
                """
                SELECT *
                FROM bookings
                WHERE booking_id = ?
                """,
                (booking_id,),
            ).fetchone()

            if booking is None:
                raise ValueError("Booking not found.")

            if booking["status"] != "active":
                raise ValueError("This booking is not active.")

            if user_id is not None and booking["user_id"] != user_id:
                raise ValueError(
                    "You cannot cancel another lecturer's booking."
                )

            start = datetime.strptime(
                f"{booking['booking_date']} {booking['start_time']}",
                "%Y-%m-%d %H:%M",
            )

            if start <= datetime.now():
                raise ValueError(
                    "Only future bookings can be cancelled."
                )

            connection.execute(
                """
                UPDATE bookings
                SET status = 'cancelled'
                WHERE booking_id = ?
                """,
                (booking_id,),
            )
    def get_campus_report(self, campus_name):
        with self._connection() as connection:
            campus = connection.execute(
                "SELECT * FROM campuses WHERE name = ?",
                (campus_name,),
            ).fetchone()

            if campus is None:
                raise ValueError("Campus not found.")

            campus_id = campus["campus_id"]

            summary = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_bookings,
                    AVG(duration_hours) AS average_duration_hours
                FROM bookings
                WHERE campus_id = ?
                    AND status IN ('active', 'completed')
                """,
                (campus_id,),
            ).fetchone()

            resource_rows = connection.execute(
                """
                SELECT
                    r.resource_code,
                    r.name AS resource_name,
                    COUNT(b.booking_id) AS usage_count
                FROM resources r
                LEFT JOIN bookings b
                    ON b.resource_id = r.resource_id
                    AND b.status IN ('active', 'completed')
                WHERE r.campus_id = ?
                    AND r.is_active = 1
                GROUP BY r.resource_id, r.resource_code, r.name
                ORDER BY usage_count DESC, r.name
                LIMIT 3
                """,
                (campus_id,),
            ).fetchall()

        average = summary["average_duration_hours"]

        return {
            "campus_name": campus_name,
            "total_bookings": summary["total_bookings"],
            "average_duration_hours": (
                round(average, 2) if average is not None else 0
            ),
            "most_used_resources": [
                dict(row) for row in resource_rows
            ],
            "policy": {
                "max_duration_hours": campus["max_duration_hours"],
                "opening_time": campus["opening_time"],
                "closing_time": campus["closing_time"],
                "max_days_ahead": campus["max_days_ahead"],
                "description": campus["policy_description"],
            },
        }
    def get_cross_campus_report(self):
        reports = []

        for campus in self.get_campuses():
            report = self.get_campus_report(campus["name"])
            reports.append(report)

        return reports