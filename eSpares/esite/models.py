import secrets
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.utils.deconstruct import deconstructible
from django.utils import timezone


@deconstructible
class PrivateUploadStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.BASE_DIR / "private_uploads", base_url=None)


private_upload_storage = PrivateUploadStorage()


def validate_upload_size(file):
    file_size=5*1024*1024
    if file.size > file_size:
        from django.core.exceptions import ValidationError
        raise ValidationError("Image files must be 5 MB or smaller.")


def repair_photo_path(instance, filename):
    suffix = Path(filename).suffix.lower()[:10]
    owner_id = getattr(instance, "customer_id", None)
    if owner_id is None and getattr(instance, "repair_id", None):
        owner_id = instance.repair.customer_id
    return f"repair_uploads/{owner_id or 'unassigned'}/{secrets.token_hex(16)}{suffix}"

# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

    def __repr__(self):
        return f"{self.username}"



class Brand(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products", null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name



class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"{self.product}"



class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __repr__(self):
        return f"{self.quantity}"



class  Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"{self.rating}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=250, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.get_username()}"


class Device(models.Model):
    CONDITION_CHOICES = [
        ("working", "Works, needs repair"),
        ("damaged", "Physically damaged"),
        ("not_powering", "Does not power on"),
        ("other", "Other condition"),
    ]
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="registered_devices")
    model_name = models.CharField(max_length=120)
    serial_number = models.CharField(max_length=100, blank=True)
    imei = models.CharField(max_length=20, blank=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default="working")
    notes = models.CharField(max_length=500, blank=True)
    photo = models.ImageField(storage=private_upload_storage, upload_to=repair_photo_path, blank=True, validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_upload_size])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.brand} {self.model_name}"


class RepairService(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        return self.name


class RepairRequest(models.Model):
    STATUS_CHOICES = [
        ("submitted", "Request received"), ("reviewing", "Under review"),
        ("quoted", "Quotation ready"), ("approved", "Approved"),
        ("in_repair", "Repair in progress"), ("ready", "Ready for collection"),
        ("collected", "Collected"), ("declined", "Closed without repair"),
    ]
    FULFILLMENT_CHOICES = [("dropoff", "I will bring it in"), ("collection", "Request collection")]
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="repair_requests")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="repair_requests")
    service = models.ForeignKey(RepairService, on_delete=models.PROTECT, related_name="repair_requests")
    reference = models.CharField(max_length=32, unique=True, editable=False)
    problem = models.TextField(max_length=2000)
    preferred_date = models.DateField()
    fulfillment = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES)
    service_address = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    estimated_completion = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"UP-{secrets.token_hex(10).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


class RepairPhoto(models.Model):
    repair = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(storage=private_upload_storage, upload_to=repair_photo_path, validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_upload_size])
    uploaded_at = models.DateTimeField(auto_now_add=True)


class RepairUpdate(models.Model):
    repair = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name="updates")
    status = models.CharField(max_length=20, choices=RepairRequest.STATUS_CHOICES, blank=True)
    comment = models.CharField(max_length=1000)
    visible_to_customer = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "pk")


class RepairQuote(models.Model):
    STATUS_CHOICES = [("pending", "Awaiting customer"), ("approved", "Approved"), ("rejected", "Rejected")]
    repair = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name="quotes")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    parts_and_labor = models.TextField(max_length=1500)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)


class RepairInvoice(models.Model):
    STATUS_CHOICES = [("unpaid", "Unpaid"), ("paid", "Paid")]
    quote = models.OneToOneField(RepairQuote, on_delete=models.PROTECT, related_name="invoice")
    invoice_number = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="unpaid")
    issued_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{secrets.token_hex(8).upper()}"
        super().save(*args, **kwargs)


class RepairPayment(models.Model):
    """Manual payment record only; online payments need a configured provider."""
    invoice = models.ForeignKey(RepairInvoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reference = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.invoice_id or self.amount is None:
            return
        existing = self.invoice.payments.exclude(pk=self.pk).aggregate(total=Sum("amount"))["total"] or 0
        if existing + self.amount > self.invoice.quote.amount:
            raise ValidationError({"amount": "Recorded payments cannot exceed the invoice total."})


class Promotion(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    is_active = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "title")


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=100)
    quote = models.CharField(max_length=500)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [("booking", "Repair booking"), ("tracking", "Repair tracking"), ("warranty", "Warranty enquiry"), ("complaint", "Complaint"), ("feedback", "Service feedback"), ("other", "Other")]
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)


class SupportConversation(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("closed", "Closed")]
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_conversations")
    subject = models.CharField(max_length=120, default="Support chat")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)


class SupportMessage(models.Model):
    conversation = models.ForeignKey(SupportConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    body = models.CharField(max_length=2000)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sent_at", "pk")
