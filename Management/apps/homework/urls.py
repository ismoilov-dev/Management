from django.urls import path
from . import views

app_name = "homework"

urlpatterns = [

    # ── Assignment endpoints ──────────────────────────────────────────
    # GET   /assignments/              → ro'yxat
    path(
        "assignments/",
        views.AssignmentListAPIView.as_view(),
        name="assignment-list",
    ),

    # POST  /assignments/create/       → yangi assignment
    path(
        "assignments/create/",
        views.AssignmentCreateAPIView.as_view(),
        name="assignment-create",
    ),

    # GET   /assignments/<id>/         → bitta assignment detail
    path(
        "assignments/<int:pk>/",
        views.AssignmentDetailAPIView.as_view(),
        name="assignment-detail",
    ),

    # PUT/PATCH /assignments/<id>/update/  → tahrirlash
    path(
        "assignments/<int:pk>/update/",
        views.AssignmentUpdateAPIView.as_view(),
        name="assignment-update",
    ),

    # DELETE /assignments/<id>/delete/    → o'chirish
    path(
        "assignments/<int:pk>/delete/",
        views.AssignmentDeleteAPIView.as_view(),
        name="assignment-delete",
    ),

    # GET /assignments/group/<group_id>/  → bitta groupning vazifalari
    path(
        "assignments/group/<int:group_id>/",
        views.GroupAssignmentListAPIView.as_view(),
        name="group-assignments",
    ),

    # ── Submission endpoints ──────────────────────────────────────────
    # GET  /submissions/               → barcha submissionlar (teacher/admin)
    path(
        "submissions/",
        views.SubmissionListAPIView.as_view(),
        name="submission-list",
    ),

    # POST /submissions/create/        → javob yuborish (student)
    path(
        "submissions/create/",
        views.SubmissionCreateAPIView.as_view(),
        name="submission-create",
    ),

    # GET  /submissions/<id>/          → bitta submission detail
    path(
        "submissions/<int:pk>/",
        views.SubmissionDetailAPIView.as_view(),
        name="submission-detail",
    ),

    # PATCH /submissions/<id>/grade/   → baholash (teacher)
    path(
        "submissions/<int:pk>/grade/",
        views.SubmissionGradeAPIView.as_view(),
        name="submission-grade",
    ),
]