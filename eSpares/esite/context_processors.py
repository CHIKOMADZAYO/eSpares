from .models import Brand


def product_brands(request):
    """Expose the catalog brands to the shared navigation dropdown."""
    cart = request.session.get("cart", {})
    cart_count = sum(
        int(quantity) for quantity in cart.values()
        if str(quantity).isdigit() and 0 < int(quantity) <= 99
    )
    return {"product_brands": Brand.objects.all(), "cart_count": cart_count}
