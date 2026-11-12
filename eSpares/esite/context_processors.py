from .models import Brand


def product_brands(request):
    """Expose the catalog brands to the shared navigation dropdown."""
    return {"product_brands": Brand.objects.all()}
