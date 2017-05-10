import csv
from io import TextIOWrapper

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView

from inventory.models import *


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
        except csv.Error:
            pass

        return redirect('inventory:index')


def inventory_upload(request):
    if request.method == 'GET':
        return render(request, 'inventory/inventory_upload.html')

    raise NotImplemented('Inventory uploader is not implemented.')


class InventoryList(ListView):
    model = Inventory

    def get_queryset(self):
        foo = get_object_or_404(Report, pk=self.kwargs['report_id'])
        return Inventory.objects.filter(report=foo)


class ReportList(ListView):
    model = Report
