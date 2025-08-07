# urls.py
from django.urls import path
from .views import ActivityLogListView

urlpatterns = [
    path('activity-log/', ActivityLogListView.as_view(), name='activity-log-list'),
]
