class User:
    ROLE = "User"
    PERMISSIONS = frozenset()

    def __init__(
        self,
        user_id: int | None,
        full_name: str,
        email: str,
        password_hash: str,
    ):
        if not full_name.strip():
            raise ValueError("Full name cannot be empty.")

        if not email.strip():
            raise ValueError("Email address cannot be empty.")

        if not password_hash:
            raise ValueError("Password hash cannot be empty.")

        self._user_id = user_id
        self._full_name = full_name.strip()
        self._email = email.strip().lower()
        self._password_hash = password_hash

    @property
    def user_id(self) -> int | None:
        return self._user_id

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def email(self) -> str:
        return self._email

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def role(self) -> str:
        return self.ROLE

    @property
    def permissions(self) -> frozenset:
        return self.PERMISSIONS

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        return f"{self.full_name} ({self.role})"

class Lecturer(User):
    ROLE = "Lecturer"

    PERMISSIONS = frozenset({
        "view_resources",
        "create_booking",
        "view_own_bookings",
        "cancel_own_bookings",
    })

class CampusAdministrator(User):
    ROLE = "Campus Administrator"

    PERMISSIONS = frozenset({
        "manage_resources",
        "view_campus_bookings",
        "view_campus_reports",
    })

    def __init__(
        self,
        user_id: int | None,
        full_name: str,
        email: str,
        password_hash: str,
        campus_name: str,
    ):
        super().__init__(user_id, full_name, email, password_hash)

        if not campus_name.strip():
            raise ValueError("An administrator must have an assigned campus.")

        self._campus_name = campus_name.strip()

    @property
    def campus_name(self) -> str:
        return self._campus_name

class SystemOperator(User):
    ROLE = "System Operator"

    PERMISSIONS = frozenset({
        "view_all_campuses",
        "view_all_resources",
        "view_all_bookings",
        "compare_campuses",
    })