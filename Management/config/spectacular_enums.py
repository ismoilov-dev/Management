"""
drf-spectacular status enum names (avoids Status788Enum / StatusB43Enum collisions).
Import paths are resolved after Django is ready.
"""

ENUM_NAME_OVERRIDES = {
    "StudentStatusEnum": "apps.students.models.StudentProfile.StatusChoices",
    "TeacherStatusEnum": "apps.teachers.models.TeacherProfile.StatusChoices",
    "AttendanceStatusEnum": "apps.attendance.models.AttendanceRecord.StatusChoices",
    "PaymentStatusEnum": "apps.payments.models.Payment.Status",
    "HomeworkSubmissionStatusEnum": "apps.homework.models.Submission.StatusChoices",
    "TaskStatusEnum": "apps.tasks.models.Task.Status",
}
