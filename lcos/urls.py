# network/urls.py

from django.urls import path
from .views import LCOCreateListView, LCORetrieveUpdateDeleteView,BulkLCOUpload

urlpatterns = [
    path('lco/', LCOCreateListView.as_view(), name='lco-create-list'),
    path('lco/<int:pk>/', LCORetrieveUpdateDeleteView.as_view(), name='lco-detail'),
    path('bulk-upload/lco/', BulkLCOUpload.as_view(), name='bulk-upload-lco'),
]
