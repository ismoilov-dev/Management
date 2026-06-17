from django.utils import timezone
from .models import SubmissionModel , AssignmentModel


def mark_late_if_needed(submission: SubmissionModel) -> None:
    if submission.submitted_at > submission.assignment.due_date:
        submission.status = SubmissionModel.StatusChoices.LATE
        submission.save(update_fields=["status"])
       


def grade_submission(submission: SubmissionModel, score, feedback: str = "") -> SubmissionModel:
    submission.score     = score
    submission.feedback  = feedback
    submission.status    = SubmissionModel.StatusChoices.GRADED
    submission.graded_at = timezone.now()
    submission.save(update_fields=["score", "feedback", "status", "graded_at"])
    return submission


def get_group_assignments(group_id: int):
    return (
        AssignmentModel.objects
        .filter(group_id=group_id, is_published=True)
        .select_related("teacher", "subject")
        .order_by("due_date")
    )


def get_student_submissions(student):   
    return (
        SubmissionModel.objects
        .filter(student=student)
        .select_related("assignment", "assignment__subject")
        .order_by("-submitted_at")
    )