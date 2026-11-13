from django.conf import settings

from catalog.models import Collection
from orders.cart import Cart


def store_context(request):
    try:
        collections = Collection.objects.filter(is_active=True)[:5]
        cart = Cart(request)
        return {"nav_collections": collections, "cart_count": cart.count, "cart_total": cart.total, "pickup_instructions": settings.WESKA_PICKUP_INSTRUCTIONS}
    except Exception:
        return {"nav_collections": [], "cart_count": 0, "cart_total": 0, "pickup_instructions": settings.WESKA_PICKUP_INSTRUCTIONS}
