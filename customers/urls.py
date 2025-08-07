from django.urls import path
from .views import CustomerListCreateView, CustomerRetrieveUpdateDestroyView,BulkCustomerUpload,CustomerSearchListView,LCOByOLTView,ISPByLCOView,CustomerReportView,LCOCustomerSearchListView,DropdownDataAPIView,DashboardCountsView,CustomersExpiringSoonFilteredView
from django.conf.urls.static import static
from django.conf import settings




urlpatterns = [
    path('customer/', CustomerListCreateView.as_view(), name='customer-list-create'),
    path('customer/<int:pk>/', CustomerRetrieveUpdateDestroyView.as_view(), name='customer-detail'),

    # bulk upload

    path('upload/', BulkCustomerUpload.as_view(), name='bulk-upload'),


    # report module

    path('by-olt/<int:olt_id>/', LCOByOLTView.as_view(), name='lco-by-olt'),

    path('isp/by-lco/<int:lco_id>/', ISPByLCOView.as_view(), name='isp-by-lco'),

    path('search/', CustomerSearchListView.as_view(), name='customer-search'),

    path('report/', CustomerReportView.as_view(), name='customer-report'),

    path('my-customers/search/', LCOCustomerSearchListView.as_view(), name='lco-customer-search'),

    path('dropdowns/', DropdownDataAPIView.as_view(), name='dropdowns-all'),

    path('counts/', DashboardCountsView.as_view(), name='dashboard-counts'),

    path('expiring-soon/', CustomersExpiringSoonFilteredView.as_view(), name='customers-expiring-soon'),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

