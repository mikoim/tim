from django.db import models


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
            inv = self.inventories.all()
        else:
            inv = self.inventories.filter(rack_id=rack_id)

        if inv.count() > 0:
            return sum([x.sum() for x in inv])
        else:
            return 0


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
