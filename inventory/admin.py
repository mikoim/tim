from django.contrib import admin

from .models import *


class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name', 'unit_cost')


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'count', 'rack_id')


class ReportInline(admin.StackedInline):
    model = Inventory


class ReportAdmin(admin.ModelAdmin):
    inlines = [ReportInline]


admin.site.register(Item, ItemAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Report, ReportAdmin)
