from django.conf.urls import url
from django.views.generic import TemplateView

from inventory.views import ReportList, InventoryList
from . import views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='inventory/index.html'), name='index'),

    # Upload forms
    url(r'^item/upload$', views.item_upload, name='item_upload'),
    url(r'^inventory/upload$', views.inventory_upload, name='inventory_upload'),

    # Viewers
    url(r'^reports$', ReportList.as_view(), name='list_report'),
    url(r'^reports/(?P<report_id>[0-9]+)$', InventoryList.as_view(), name='show_report'),
]
