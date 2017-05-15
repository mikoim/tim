import csv
import logging
import os.path
import re
from collections import OrderedDict
from io import TextIOWrapper

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.views.generic import ListView, FormView

from inventory.models import *

logger = logging.getLogger(__name__)

REGEX_NORMALIZED = re.compile(r'(\d{5})')
REGEX_RAW = re.compile(r'[a-z](\d{5})[a-z]')
REGEX_RAW_CD = re.compile(r'[a-z](\d{5})[0-9A-D$/:+-.][a-z]')


def parse_line(line: list) -> tuple:
    item_id = int(line[0])
    category = line[1]
    name = line[2]
    try:
        unit_cost = int(line[3])
    except ValueError:
        unit_cost = 0

    return item_id, category, name, unit_cost


def item_upload(request):
    if request.method == 'GET':
        return render(request, 'inventory/item_upload.html')

    if 'csv' in request.FILES:
        form_data = TextIOWrapper(request.FILES['csv'].file, encoding='utf-8')
        scrubbed_data = [x.replace('\0', '') for x in form_data.readlines()]
        csv_file = csv.reader(scrubbed_data)

        try:
            for line in csv_file:
                try:
                    parsed_line = parse_line(line)
                except ValueError:
                    messages.warning(request, f'Can\'t parse this line. Skipped! {line}')
                    continue

                try:
                    item = Item.objects.get(pk=int(parsed_line[0]))
                except Item.DoesNotExist:
                    item = Item()

                item.id = parsed_line[0]
                item.category = parsed_line[1]
                item.name = parsed_line[2]
                item.unit_cost = parsed_line[3]

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
            report = Report()
            report.datetime = form.cleaned_data['datetime']
            report.save()

            for f in files:
                filename = os.path.splitext(f.name)[0]

                try:
                    rack_id = int(filename)
                except ValueError:
                    messages.error(request, f'"{filename}" contains invalid character. Use integers only. ex) 1.txt')
                    continue

                lines = TextIOWrapper(f).readlines()
                self.save_inventory(report, rack_id, lines)

            messages.success(request, 'Import complete. Please check warnings and errors.')

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def normalize(self, code: str) -> int:
        result = list(map(lambda x: x.match(code), [REGEX_RAW_CD, REGEX_RAW, REGEX_NORMALIZED]))

        if not any(result):
            messages.warning(self.request, f'Unknown barcode format. Skipped! {code}')
            return -1

        return int([x for x in result if x is not None][0].group(1))

    def save_inventory(self, report: Report, rack_id: int, lines: list):
        result = {}

        for line in [x for x in map(self.normalize, lines) if x != -1]:
            if line in result:
                result[line] += 1
            else:
                result[line] = 1

        for item_id, count in result.items():
            inventory = Inventory()
            inventory.report = report
            try:
                item = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                messages.warning(self.request, f'{item_id} does not exists on Item database. Skipped!')
                continue
            inventory.item = item
            inventory.count = count
            inventory.rack_id = rack_id
            inventory.save()


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
