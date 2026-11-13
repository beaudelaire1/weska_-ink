from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product


@receiver(post_save, sender=Product)
def ensure_stock_item(sender, instance, created, **kwargs):
    if created:
        from inventory.models import StockItem
        StockItem.objects.get_or_create(product=instance)
