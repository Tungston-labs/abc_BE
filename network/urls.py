
from django.urls import path
from .views import SwitchListCreateView, SwitchRetrieveUpdateDestroyView,OLTListCreateView,OLTRetrieveUpdateDestroyView,ISPCreateListView,ISPRetrieveUpdateDeleteView,UnassignedOLTListView,SwitchDropdownListView

urlpatterns = [
    path('switches/', SwitchListCreateView.as_view(), name='switch-list-create'),
    path('switches/<int:pk>/', SwitchRetrieveUpdateDestroyView.as_view(), name='switch-detail'),
    path('switches/dropdown/', SwitchDropdownListView.as_view(), name='switch-dropdown'),
    path('olts/', OLTListCreateView.as_view(), name='olt-list-create'),
    path('olts/<int:pk>/', OLTRetrieveUpdateDestroyView.as_view(), name='olt-detail'),
    path('isp/', ISPCreateListView.as_view(), name='isp-create-list'),
    path('isp/<int:pk>/', ISPRetrieveUpdateDeleteView.as_view(), name='isp-detail'),
    path('unassigned-olts/', UnassignedOLTListView.as_view(), name='unassigned-olts'),
]
