from django.urls import path
from . import views

urlpatterns = [
    path("", views.TaskListCreateView.as_view(), name="task-list-create"),
    path("<uuid:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("<uuid:pk>/status/", views.TaskStatusUpdateView.as_view(), name="task-status-update"),
    path("<uuid:pk>/cancel/", views.TaskCancelView.as_view(), name="task-cancel"),

    path("my/", views.MyTasksView.as_view(), name="my-tasks"),
    path("created-by-me/", views.CreatedByMeTasksView.as_view(), name="created-by-me"),
    path("urgent/", views.UrgentTasksView.as_view(), name="urgent-tasks"),
    path("overdue/", views.OverdueTasksView.as_view(), name="overdue-tasks"),
    path("completed/", views.CompletedTasksView.as_view(), name="completed-tasks"),
    path("cancelled/", views.CancelledTasksView.as_view(), name="cancelled-tasks"),
    path("today/", views.TodayDueTasksView.as_view(), name="today-tasks"),

    path("priority/<str:priority>/", views.TasksByPriorityView.as_view(), name="tasks-by-priority"),
    path("assignee/<uuid:user_id>/", views.TasksByAssigneeView.as_view(), name="tasks-by-assignee"),
]