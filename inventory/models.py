from django import forms
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone


class CommonModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(object):
        abstract = True


class Item(CommonModel):
    category = models.CharField(blank=True, max_length=255)  # TODO Move to Category model

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    unit_cost = models.PositiveIntegerField()

    class Meta(object):
        ordering = ['id']

    def __str__(self):
        return f'[{self.category}] {self.name}'


class Report(CommonModel):
    datetime = models.DateTimeField()

    def __str__(self):
        return self.datetime.isoformat()

    def sum(self, rack_id=None):
        if rack_id is None:
            inv = self.inventories.all().aggregate(sum=Sum(F('item__unit_cost') * F('count')))
        else:
            inv = self.inventories.filter(rack_id=rack_id).aggregate(sum=Sum(F('item__unit_cost') * F('count')))

        return inv['sum']

    def rack_ids(self) -> list:
        return sorted([x['rack_id'] for x in self.inventories.values('rack_id').annotate(n=models.Count('pk'))])


class Inventory(CommonModel):
    report = models.ForeignKey(Report, related_name='inventories')

    item = models.ForeignKey(Item, related_name='items')
    count = models.IntegerField()

    rack_id = models.IntegerField()

    class Meta(object):
        verbose_name_plural = 'inventories'

    def sum(self) -> int:
        return self.item.unit_cost * self.count

    def __str__(self):
        return f'{str(self.item)} x {self.count} = {self.sum()} @ {self.rack_id}'


class InventoryUploadForm(forms.Form):
    datetime = forms.DateTimeField(initial=lambda: timezone.now())
    inventory_data = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
