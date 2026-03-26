# network/urls.py

from django.urls import path
from .views import LCOCreateListView, LCORetrieveUpdateDeleteView,BulkLCOUpload,LCOScrollListView,PublicLCOSearchView,NearbyLCOView,DashboardCountView,LCOCustomerReportView

urlpatterns = [
    path('lco/', LCOCreateListView.as_view(), name='lco-create-list'),
    path('lco/<int:pk>/', LCORetrieveUpdateDeleteView.as_view(), name='lco-detail'),
    path("scroll/", LCOScrollListView.as_view(), name="lco-scroll-list"),
    path('bulk-upload/lco/', BulkLCOUpload.as_view(), name='bulk-upload-lco'),
    path('public/', PublicLCOSearchView.as_view()),
    path('public/nearby/', NearbyLCOView.as_view()),
    path('dashboard/count/', DashboardCountView.as_view(), name='dashboard-count'),
    path('client/report/', LCOCustomerReportView.as_view()),
]
