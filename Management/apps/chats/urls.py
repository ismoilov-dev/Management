from django.urls import path
from apps.chats import views

urlpatterns = [
    path("rooms/", views.ChatRoomListCreateView.as_view(), name="room-list-create"),
    path("rooms/<uuid:pk>/", views.ChatRoomDetailView.as_view(), name="room-detail"),
    path("rooms/<uuid:room_id>/messages/", views.MessageListView.as_view(), name="message-list"),
    path("rooms/<uuid:room_id>/participants/", views.ParticipantListView.as_view(), name="participant-list"),
    path("rooms/<uuid:room_id>/participants/add/", views.AddParticipantView.as_view(), name="add-participant"),
    path("rooms/<uuid:room_id>/participants/<uuid:user_id>/remove/", views.RemoveParticipantView.as_view(), name="remove-participant"),
    path("rooms/<uuid:room_id>/leave/", views.LeaveRoomView.as_view(), name="leave-room"),
    path("rooms/<uuid:room_id>/upload/", views.UploadAttachmentView.as_view(), name="upload-attachment"),
    path("rooms/<uuid:room_id>/search/", views.SearchMessagesView.as_view(), name="search-messages"),
]