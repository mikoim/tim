import csv
import logging
from collections import OrderedDict
from io import TextIOWrapper

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.views.generic import ListView, FormView

from inventory.models import *

logger = logging.getLogger(__name__)


def item_upload(request):
    if request.method == 'GET':
        return render(request, 'inventory/item_upload.html')

    if 'csv' in request.FILES:
        form_data = TextIOWrapper(request.FILES['csv'].file)
        csv_file = csv.reader(form_data)

        try:
            for line in csv_file:
                try:
                    unit_cost = int(line[4])
                except ValueError:
                    unit_cost = 0
                    mes = f'{line[4]} cannot be cast to int. filled by 0. Check this line -> {line}'
                    messages.warning(request, mes)

                try:
                    item = Item.objects.get(pk=int(line[0]))
                except Item.DoesNotExist:
                    item = Item()

                item.id = int(line[0])
                item.category = line[1]
                item.name = line[2]
                item.description = line[3]
                item.unit_cost = unit_cost

                item.save()
        except csv.Error as e:
            logger.error(e)
            messages.error(request, f'Failed to import item data. {e}')
        else:
            messages.success(request, 'Item data import succeeded.')
    else:
        messages.warning(request, 'Item data is not uploaded.')

    return redirect('inventory:item_upload')


class InventoryUploadView(FormView):
    form_class = InventoryUploadForm
    template_name = 'inventory/inventory_upload.html'
    success_url = reverse_lazy('inventory:inventory_upload')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        files = request.FILES.getlist('inventory_data')
        if form.is_valid():
            for f in files:
                data = TextIOWrapper(f)
                print(data.readlines())
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def save_inventory(self, report: Report, file):
        pass


def report_detail(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    rack_ids = report.rack_ids()

    inventories = OrderedDict()
    subtotals_per_rack = OrderedDict()
    total = 0

    for x in rack_ids:
        inventories[x] = get_list_or_404(Inventory, report=report, rack_id=x)
        subtotal = report.sum(x)
        subtotals_per_rack[x] = subtotal
        total += subtotal

    context = {
        'inventories': inventories,
        'subtotals_per_rack': subtotals_per_rack,
        'total': total,
    }

    return render(request, 'inventory/report_detail.html', context)


class ReportList(ListView):
    model = Report
