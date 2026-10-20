from dataclasses import dataclass

@dataclass(frozen=True)
class CampusPolicy:
    campus_name: str
    max_duration_hours: int
    opening_time: str
    closing_time: str
    max_days_ahead: int
    description: str

CAMPUS_POLICIES = {
    "Durban Campus": CampusPolicy(
        campus_name="Durban Campus",
        max_duration_hours=4,
        opening_time="07:00",
        closing_time="20:00",
        max_days_ahead=30,
        description=(
            "Maximum 4 hours per booking, between 07:00 and 20:00, "
            "up to 30 days ahead."
        ),
    ),
    "Johannesburg Campus": CampusPolicy(
        campus_name="Johannesburg Campus",
        max_duration_hours=2,
        opening_time="08:00",
        closing_time="18:00",
        max_days_ahead=14,
        description=(
            "Maximum 2 hours per booking, between 08:00 and 18:00, "
            "up to 14 days ahead."
        ),
    ),
    "Cape Town Campus": CampusPolicy(
        campus_name="Cape Town Campus",
        max_duration_hours=3,
        opening_time="09:00",
        closing_time="17:00",
        max_days_ahead=21,
        description=(
            "Maximum 3 hours per booking, between 09:00 and 17:00, "
            "up to 21 days ahead."
        ),
    ),
}

STARTER_RESOURCES = {
    "Durban Campus": [
        (
            "DBN-LAB-01",
            "Computer Laboratory 1",
            "Computer Lab",
            "Main computer laboratory",
        ),
        (
            "DBN-PROJ-01",
            "Multimedia Projector 1",
            "Projector",
            "Portable classroom projector",
        ),
    ],
    "Johannesburg Campus": [
        (
            "JHB-SEM-01",
            "Seminar Room 1",
            "Seminar Room",
            "Small group seminar room",
        ),
        (
            "JHB-EQP-01",
            "Presentation Kit 1",
            "Presentation Equipment",
            "Presentation equipment set",
        ),
    ],
    "Cape Town Campus": [
        (
            "CPT-LAB-01",
            "Multimedia Laboratory 1",
            "Computer Lab",
            "Multimedia teaching laboratory",
        ),
        (
            "CPT-PROJ-01",
            "Multimedia Projector 1",
            "Projector",
            "Portable classroom projector",
        ),
    ],
}