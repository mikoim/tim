import csv
from collections import OrderedDict
from io import TextIOWrapper

from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.views.generic import ListView

from inventory.models import *
import logging
from django.contrib import messages

logger = logging.getLogger(__name__)


def item_upload(request):
    if request.method == 'GET':
        return render(request, 'inventory/item_upload.html')

    form_data = TextIOWrapper(request.FILES['csv'].file)

    if form_data:
        csv_file = csv.reader(form_data)

        try:
            for line in csv_file:
                try:
                    unit_cost = int(line[4])
                except ValueError:
                    unit_cost = 0

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

        return redirect('inventory:index')


def inventory_upload(request):
    if request.method == 'GET':
        return render(request, 'inventory/inventory_upload.html')

    raise NotImplemented('Inventory uploader is not implemented.')


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
