from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Sum
from .models import (
    Brand, ContactMessage, CustomerProfile, Device, Product, Promotion, RepairInvoice,
    RepairPayment, RepairPhoto, RepairQuote, RepairRequest, RepairService, RepairUpdate,
    SupportConversation, SupportMessage, Testimonial,
)


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


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "updated_at")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("brand", "model_name", "customer", "condition", "created_at")
    list_filter = ("brand", "condition")
    search_fields = ("model_name", "brand__name", "customer__username", "customer__email")
    readonly_fields = ("created_at",)
    formfield_overrides = {models.ImageField: {"widget": forms.FileInput}}


@admin.register(RepairService)
class RepairServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "starting_price", "display_order")
    list_editable = ("is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}


class RepairPhotoInline(admin.TabularInline):
    model = RepairPhoto
    extra = 0
    formfield_overrides = {models.ImageField: {"widget": forms.FileInput}}


class RepairUpdateInline(admin.TabularInline):
    model = RepairUpdate
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "device", "service", "status", "preferred_date", "created_at")
    list_filter = ("status", "service", "fulfillment", "created_at")
    search_fields = ("reference", "customer__username", "customer__email", "device__model_name")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = (RepairPhotoInline, RepairUpdateInline)

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = RepairRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if not change or previous_status != obj.status:
            RepairUpdate.objects.create(
                repair=obj, status=obj.status,
                comment=f"Repair status updated to {obj.get_status_display()}.",
                created_by=request.user,
            )


@admin.register(RepairQuote)
class RepairQuoteAdmin(admin.ModelAdmin):
    list_display = ("repair", "amount", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("repair__reference", "repair__customer__email")
    readonly_fields = ("created_at", "responded_at")

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)
        if is_new:
            obj.created_by = request.user
            obj.save(update_fields=("created_by",))
            obj.repair.status = "quoted"
            obj.repair.save(update_fields=("status", "updated_at"))
            RepairUpdate.objects.create(
                repair=obj.repair, status="quoted", comment="A quotation is ready for your review.",
                created_by=request.user,
            )


@admin.register(RepairInvoice)
class RepairInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "quote", "status", "issued_at")
    list_filter = ("status", "issued_at")
    readonly_fields = ("invoice_number", "issued_at")


@admin.register(RepairPayment)
class RepairPaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount", "reference", "recorded_by", "recorded_at")
    readonly_fields = ("recorded_at",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
        paid_total = obj.invoice.payments.aggregate(total=Sum("amount"))["total"] or 0
        if paid_total >= obj.invoice.quote.amount and obj.invoice.status != "paid":
            obj.invoice.status = "paid"
            obj.invoice.save(update_fields=("status",))

    def has_change_permission(self, request, obj=None):
        return False if obj is not None else super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "starts_at", "ends_at", "display_order")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active",)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "is_published", "created_at")
    list_editable = ("is_published",)
    list_filter = ("is_published",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_resolved", "created_at")
    list_filter = ("subject", "is_resolved", "created_at")
    search_fields = ("name", "email", "message")
    list_editable = ("is_resolved",)
    readonly_fields = ("customer", "name", "email", "subject", "message", "created_at")


@admin.register(SupportConversation)
class SupportConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "subject", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("customer__username", "customer__email", "subject")
    readonly_fields = ("customer", "created_at", "updated_at")


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "is_staff", "sent_at")
    list_filter = ("is_staff", "sent_at")
    search_fields = ("conversation__customer__username", "conversation__customer__email", "body")
    readonly_fields = ("sender", "is_staff", "sent_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.sender = request.user
            obj.is_staff = True
        super().save_model(request, obj, form, change)
        obj.conversation.save(update_fields=("updated_at",))
