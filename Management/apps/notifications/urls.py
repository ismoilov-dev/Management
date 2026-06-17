# apps/notifications/urls.py

from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    # SSE stream
    path("stream/",          views.sse_stream,              name="sse-stream"),

    # REST
    path("",                 views.NotificationListView.as_view(), name="list"),
    path("unread-count/",    views.unread_count,            name="unread-count"),
    path("mark-all-read/",   views.NotificationBulkReadView.as_view(), name="bulk-read"),
    path("<uuid:pk>/read/",   views.NotificationReadView.as_view(),  name="mark-read"),
]