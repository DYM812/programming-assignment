import math
from datetime import date, datetime, timedelta

class BookingService:

    def __init__(self, database):
        self.database = database

    def _require_permission(self, user, permission):
        if user is None or not user.has_permission(permission):
            raise PermissionError(
                "You do not have permission to perform this action."
            )

    def _check_campus_access(self, user, campus_name):
        if user is None:
            raise PermissionError("You must log in first.")

        if user.role == "Campus Administrator":
            if user.campus_name != campus_name:
                raise PermissionError(
                    "You can only access your assigned campus."
                )

    def get_campuses(self, user):
        if user is None:
            raise PermissionError("You must log in first.")

        return self.database.get_campuses()

    def get_campus_policy(self, user, campus_name):
        if user is None:
            raise PermissionError("You must log in first.")

        self._check_campus_access(user, campus_name)

        return self.database.get_campus_policy(campus_name)

    def get_resources(
        self,
        user,
        campus_name,
        include_inactive=False,
    ):
        if user is None:
            raise PermissionError("You must log in first.")

        allowed = (
            user.has_permission("view_resources")
            or user.has_permission("manage_resources")
            or user.has_permission("view_all_resources")
        )

        if not allowed:
            raise PermissionError(
                "You do not have permission to view resources."
            )

        if include_inactive and not user.has_permission(
            "manage_resources"
        ):
            raise PermissionError(
                "You cannot view inactive resources."
            )

        self._check_campus_access(user, campus_name)

        return self.database.get_resources(
            campus_name,
            include_inactive,
        )

    def validate_booking(
        self,
        campus_name,
        booking_date,
        start_time,
        duration_hours,
    ):
        policy = self.database.get_campus_policy(campus_name)

        try:
            booking_day = datetime.strptime(
                booking_date,
                "%Y-%m-%d",
            ).date()

            booking_time = datetime.strptime(
                start_time,
                "%H:%M",
            ).time()

            duration = float(duration_hours)

        except (TypeError, ValueError) as error:
            raise ValueError(
                "Enter a valid date, time and duration."
            ) from error

        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(
                "Booking duration must be greater than zero."
            )

        today = date.today()

        if booking_day < today:
            raise ValueError(
                "You cannot book a resource for a past date."
            )

        days_ahead = (booking_day - today).days

        if days_ahead > policy["max_days_ahead"]:
            raise ValueError(
                "This booking is too far in advance for this campus."
            )

        if duration > policy["max_duration_hours"]:
            raise ValueError(
                f"The maximum booking duration is "
                f"{policy['max_duration_hours']} hours."
            )

        start = datetime.combine(booking_day, booking_time)
        end = start + timedelta(hours=duration)

        if start <= datetime.now():
            raise ValueError(
                "The booking must start in the future."
            )

        if end.date() != booking_day:
            raise ValueError(
                "A booking cannot extend into the following day."
            )

        opening_time = datetime.strptime(
            policy["opening_time"],
            "%H:%M",
        ).time()

        closing_time = datetime.strptime(
            policy["closing_time"],
            "%H:%M",
        ).time()

        if booking_time < opening_time:
            raise ValueError(
                f"This campus opens at {policy['opening_time']}."
            )

        if end.time() > closing_time:
            raise ValueError(
                f"This campus closes at {policy['closing_time']}."
            )

        return duration

    def create_booking(
        self,
        user,
        campus_name,
        resource_code,
        booking_date,
        start_time,
        duration_hours,
    ):
        self._require_permission(user, "create_booking")

        self._check_campus_access(user, campus_name)

        resources = self.database.get_resources(campus_name)

        resource_codes = {
            resource["resource_code"]
            for resource in resources
        }

        if resource_code.strip().upper() not in resource_codes:
            raise ValueError(
                "Select an available resource from the active campus."
            )

        duration = self.validate_booking(
            campus_name,
            booking_date,
            start_time,
            duration_hours,
        )

        return self.database.create_booking(
            user.user_id,
            resource_code,
            booking_date,
            start_time,
            duration,
        )

    def get_my_bookings(self, user, status=None):
        self._require_permission(user, "view_own_bookings")

        return self.database.get_bookings(
            user_id=user.user_id,
            status=status,
        )

    def cancel_booking(self, user, booking_id):
        self._require_permission(user, "cancel_own_bookings")

        self.database.cancel_booking(
            booking_id,
            user_id=user.user_id,
        )

    def add_resource(
        self,
        user,
        campus_name,
        resource_code,
        name,
        category,
        description="",
    ):
        self._require_permission(user, "manage_resources")

        self._check_campus_access(user, campus_name)

        return self.database.add_resource(
            campus_name,
            resource_code,
            name,
            category,
            description,
        )

    def update_resource(
        self,
        user,
        campus_name,
        resource_code,
        name,
        category,
        description="",
    ):
        self._require_permission(user, "manage_resources")

        self._check_campus_access(user, campus_name)

        resources = self.database.get_resources(
            campus_name,
            include_inactive=True,
        )

        resource_codes = {
            resource["resource_code"]
            for resource in resources
        }

        if resource_code.strip().upper() not in resource_codes:
            raise ValueError(
                "The resource does not belong to this campus."
            )

        self.database.update_resource(
            resource_code,
            name,
            category,
            description,
        )

    def remove_resource(self, user, campus_name, resource_code):
        self._require_permission(user, "manage_resources")

        self._check_campus_access(user, campus_name)

        resources = self.database.get_resources(
            campus_name,
            include_inactive=True,
        )

        resource_codes = {
            resource["resource_code"]
            for resource in resources
        }

        if resource_code.strip().upper() not in resource_codes:
            raise ValueError(
                "The resource does not belong to this campus."
            )

        self.database.remove_resource(resource_code)

    def get_bookings(
        self,
        user,
        campus_name=None,
        status=None,
    ):
        if user is None:
            raise PermissionError("You must log in first.")

        if user.role == "Lecturer":
            self._require_permission(
                user,
                "view_own_bookings",
            )

            return self.database.get_bookings(
                user_id=user.user_id,
                campus_name=campus_name,
                status=status,
            )

        if user.role == "Campus Administrator":
            self._require_permission(
                user,
                "view_campus_bookings",
            )

            assigned_campus = user.campus_name

            if (
                campus_name is not None
                and campus_name != assigned_campus
            ):
                raise PermissionError(
                    "You can only view bookings for your assigned campus."
                )

            return self.database.get_bookings(
                campus_name=assigned_campus,
                status=status,
            )

        if user.role == "System Operator":
            self._require_permission(
                user,
                "view_all_bookings",
            )

            return self.database.get_bookings(
                campus_name=campus_name,
                status=status,
            )

        raise PermissionError("Unrecognised user role.")

    def get_campus_report(self, user, campus_name):
        if user is None:
            raise PermissionError("You must log in first.")

        if user.role == "Campus Administrator":
            self._require_permission(
                user,
                "view_campus_reports",
            )

            self._check_campus_access(user, campus_name)

        elif user.role == "System Operator":
            self._require_permission(
                user,
                "compare_campuses",
            )

        else:
            raise PermissionError(
                "You do not have permission to view campus reports."
            )

        return self.database.get_campus_report(campus_name)

    def get_cross_campus_report(self, user):
        self._require_permission(user, "compare_campuses")

        return self.database.get_cross_campus_report()