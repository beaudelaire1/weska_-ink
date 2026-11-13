from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import StockItem, StockMovement, StockReservation


@transaction.atomic
def adjust_stock(product, quantity_delta, movement_type, reason="", actor=None, order=None):
    stock = StockItem.objects.select_for_update().get(product=product)
    if stock.quantity_on_hand + quantity_delta < stock.quantity_reserved:
        raise ValidationError("Cet ajustement rendrait le stock disponible négatif.")
    stock.quantity_on_hand += quantity_delta
    stock.save(update_fields=["quantity_on_hand", "updated_at"])
    return StockMovement.objects.create(stock_item=stock, movement_type=movement_type, quantity_delta=quantity_delta, reason=reason, actor=actor, order=order)


@transaction.atomic
def reserve_order(order, expires_in_minutes=60):
    items = list(order.items.select_related("product").order_by("product_id"))
    stocks = {stock.product_id: stock for stock in StockItem.objects.select_for_update().filter(product_id__in=[item.product_id for item in items]).order_by("product_id")}
    now = timezone.now()
    for item in items:
        stock = stocks.get(item.product_id)
        if stock is None or stock.quantity_on_hand - stock.quantity_reserved < item.quantity:
            raise ValidationError(f"Stock insuffisant pour {item.product_name}.")
    expiry = now + timedelta(minutes=expires_in_minutes)
    for item in items:
        stock = stocks[item.product_id]
        stock.quantity_reserved += item.quantity
        stock.save(update_fields=["quantity_reserved", "updated_at"])
        StockReservation.objects.update_or_create(order=order, product_id=item.product_id, defaults={"quantity": item.quantity, "status": StockReservation.Status.ACTIVE, "expires_at": expiry})


@transaction.atomic
def release_order_reservations(order):
    reservations = list(order.reservations.select_for_update().filter(status=StockReservation.Status.ACTIVE).select_related("product").order_by("product_id"))
    for reservation in reservations:
        stock = StockItem.objects.select_for_update().get(product=reservation.product)
        stock.quantity_reserved = max(0, stock.quantity_reserved - reservation.quantity)
        stock.save(update_fields=["quantity_reserved", "updated_at"])
        reservation.status = StockReservation.Status.RELEASED
        reservation.save(update_fields=["status"])
    return len(reservations)


@transaction.atomic
def consume_order_reservations(order, channel, actor=None):
    reservations = list(order.reservations.select_for_update().filter(status=StockReservation.Status.ACTIVE).select_related("product").order_by("product_id"))
    expected = order.items.count()
    if len(reservations) != expected:
        raise ValidationError("Les réservations de stock de cette commande sont incomplètes.")
    movement_type = StockMovement.Type.WEB_SALE if channel == "WEB" else StockMovement.Type.POS_SALE
    movements = []
    for reservation in reservations:
        stock = StockItem.objects.select_for_update().get(product=reservation.product)
        if stock.quantity_on_hand < reservation.quantity or stock.quantity_reserved < reservation.quantity:
            raise ValidationError("Le stock réservé ne peut pas être consommé.")
        stock.quantity_on_hand -= reservation.quantity
        stock.quantity_reserved -= reservation.quantity
        stock.save(update_fields=["quantity_on_hand", "quantity_reserved", "updated_at"])
        reservation.status = StockReservation.Status.CONSUMED
        reservation.save(update_fields=["status"])
        movements.append(StockMovement.objects.create(stock_item=stock, movement_type=movement_type, quantity_delta=-reservation.quantity, reason=f"Commande {order.number}", order=order, actor=actor))
    return movements
