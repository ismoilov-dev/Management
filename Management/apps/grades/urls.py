from django.urls import path
from .views import (GradeListView,GradeCreateView,GradeRetrieveView,GradeUpdateView,GradeDestroyView,
                    MyGradesView,GradesByTypeView,RecentGradesView,GradeSubjectDetailView,
                    SemesterGPAListView,SemesterGPACreateView,SemesterGPARetrieveView,SemesterGPADestroyView,MyGPAView,GPASummaryView,
                    GroupSubjectStatsView,StudentSubjectGradesView,GradeDistributionView,)

urlpatterns = [
    path("grades/",        GradeListView.as_view(),   name="grade-list"),
    path("grades/create/", GradeCreateView.as_view(), name="grade-create"),
    path("grades/my/",       MyGradesView.as_view(),    name="grade-my"),
    path("grades/by-type/",  GradesByTypeView.as_view(), name="grade-by-type"),
    path("grades/recent/",   RecentGradesView.as_view(), name="grade-recent"),
    path("grades/stats/group-subject/",   GroupSubjectStatsView.as_view(),   name="grade-stats-group-subject"),
    path("grades/stats/student-subject/", StudentSubjectGradesView.as_view(), name="grade-stats-student-subject"),
    path("grades/stats/distribution/",    GradeDistributionView.as_view(),    name="grade-stats-distribution"),
    path("grades/<uuid:pk>/",              GradeRetrieveView.as_view(),    name="grade-detail"),
    path("grades/<uuid:pk>/update/",       GradeUpdateView.as_view(),      name="grade-update"),
    path("grades/<uuid:pk>/delete/",       GradeDestroyView.as_view(),     name="grade-delete"),
    path("grades/<uuid:pk>/subject-detail/", GradeSubjectDetailView.as_view(), name="grade-subject-detail"),
    path("semester-gpa/",        SemesterGPAListView.as_view(),   name="semester-gpa-list"),
    path("semester-gpa/create/", SemesterGPACreateView.as_view(), name="semester-gpa-create"),
    path("semester-gpa/my/",      MyGPAView.as_view(),      name="semester-gpa-my"),
    path("semester-gpa/summary/", GPASummaryView.as_view(), name="semester-gpa-summary"),
    path("semester-gpa/<uuid:pk>/",        SemesterGPARetrieveView.as_view(), name="semester-gpa-detail"),
    path("semester-gpa/<uuid:pk>/delete/", SemesterGPADestroyView.as_view(),  name="semester-gpa-delete"),
]