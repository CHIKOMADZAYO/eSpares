from django.contrib import admin
from .models import Brand, Product


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "price")
    list_filter = ("brand",)
    search_fields = ("name", "description", "brand__name")
    ordering = ("name",)
