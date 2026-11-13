from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from inventory.models import StockReservation
from inventory.services import release_order_reservations
from orders.models import Order, OrderStatusHistory


class Command(BaseCommand):
    help = "Libère les réservations de stock de commandes en attente arrivées à expiration."

    def handle(self, *args, **options):
        now = timezone.now()
        order_ids = StockReservation.objects.filter(status=StockReservation.Status.ACTIVE, expires_at__lte=now, order__status=Order.Status.PENDING).values_list("order_id", flat=True).distinct()
        released = 0
        for order_id in order_ids:
            with transaction.atomic():
                order = Order.objects.select_for_update().filter(pk=order_id, status=Order.Status.PENDING).first()
                if not order:
                    continue
                released += release_order_reservations(order)
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status", "updated_at"])
                OrderStatusHistory.objects.create(order=order, old_status=Order.Status.PENDING, new_status=Order.Status.CANCELLED, note="Réservation de stock expirée.")
        self.stdout.write(self.style.SUCCESS(f"{released} réservation(s) expirée(s) libérée(s)."))
