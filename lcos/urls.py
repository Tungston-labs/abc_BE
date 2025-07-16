# network/urls.py

from django.urls import path
from .views import LCOCreateListView, LCORetrieveUpdateDeleteView

urlpatterns = [
    path('lco/', LCOCreateListView.as_view(), name='lco-create-list'),
    path('lco/<int:pk>/', LCORetrieveUpdateDeleteView.as_view(), name='lco-detail'),
]
