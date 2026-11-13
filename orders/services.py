from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import StockItem
from inventory.services import consume_order_reservations, reserve_order
from .models import Customer, Order, OrderItem, OrderStatusHistory


ALLOWED_TRANSITIONS = {
    # Pending checkout sessions are canceled by Stripe's expiry event or the cleanup command.
    Order.Status.PENDING: set(),
    Order.Status.PAID: {Order.Status.PROCESSING, Order.Status.READY, Order.Status.COMPLETED},
    Order.Status.PROCESSING: {Order.Status.READY, Order.Status.COMPLETED},
    Order.Status.READY: {Order.Status.COMPLETED},
    # Refunds and paid-order cancellations need a dedicated payment/refund flow.
    Order.Status.COMPLETED: set(),
    Order.Status.CANCELLED: set(),
    Order.Status.REFUNDED: set(),
}


@transaction.atomic
def create_web_order(customer, cart_rows, fulfillment, delivery_zone=None, address=None, postal_code="", city=""):
    if not cart_rows:
        raise ValidationError("Votre panier est vide.")
    subtotal = sum(row["product"].price_cents * row["quantity"] for row in cart_rows)
    shipping = delivery_zone.fee_cents if fulfillment == Order.Fulfillment.DELIVERY and delivery_zone else 0
    if fulfillment == Order.Fulfillment.DELIVERY and not delivery_zone:
        raise ValidationError("Choisissez une zone de livraison.")
    order = Order.objects.create(
        customer=customer, channel=Order.Channel.WEB, status=Order.Status.PENDING,
        fulfillment=fulfillment, delivery_zone=delivery_zone,
        delivery_zone_name=delivery_zone.name if delivery_zone else "",
        shipping_address=address or "", shipping_postal_code=postal_code or "", shipping_city=city or "",
        subtotal_cents=subtotal, shipping_cents=shipping, total_cents=subtotal + shipping,
    )
    for row in cart_rows:
        product, quantity = row["product"], row["quantity"]
        OrderItem.objects.create(order=order, product=product, product_name=product.name, sku=product.sku, quantity=quantity, unit_price_cents=product.price_cents, unit_cost_cents=product.cost_cents)
    reserve_order(order)
    OrderStatusHistory.objects.create(order=order, old_status="", new_status=order.status, note="Commande créée et stock réservé.")
    return order


@transaction.atomic
def create_pos_order(cart_rows, payment_method, actor, customer=None):
    if not cart_rows:
        raise ValidationError("Sélectionnez au moins un article.")
    subtotal = sum(row["product"].price_cents * row["quantity"] for row in cart_rows)
    order = Order.objects.create(customer=customer, channel=Order.Channel.POS, status=Order.Status.PAID, fulfillment=Order.Fulfillment.PICKUP, subtotal_cents=subtotal, total_cents=subtotal, payment_method=payment_method, created_by=actor)
    for row in cart_rows:
        product, quantity = row["product"], row["quantity"]
        OrderItem.objects.create(order=order, product=product, product_name=product.name, sku=product.sku, quantity=quantity, unit_price_cents=product.price_cents, unit_cost_cents=product.cost_cents)
    # A POS sale consumes stock in the same database transaction as the paid order.
    stocks = {stock.product_id: stock for stock in StockItem.objects.select_for_update().filter(product_id__in=[row["product"].pk for row in cart_rows]).order_by("product_id")}
    for row in cart_rows:
        stock = stocks.get(row["product"].pk)
        if not stock or stock.available < row["quantity"]:
            raise ValidationError(f"Stock insuffisant pour {row['product'].name}.")
    from inventory.models import StockMovement
    for row in cart_rows:
        product, quantity = row["product"], row["quantity"]
        stock = stocks[product.pk]
        stock.quantity_on_hand -= quantity
        stock.save(update_fields=["quantity_on_hand", "updated_at"])
        StockMovement.objects.create(stock_item=stock, movement_type=StockMovement.Type.POS_SALE, quantity_delta=-quantity, reason=f"Commande {order.number}", order=order, actor=actor)
    OrderStatusHistory.objects.create(order=order, old_status="", new_status=order.status, note=f"Vente physique réglée par {payment_method}.", actor=actor)
    return order


@transaction.atomic
def transition_order(order, new_status, actor=None, note=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise ValidationError(f"Transition non autorisée : {order.get_status_display()} → {dict(Order.Status.choices).get(new_status, new_status)}.")
    old = order.status
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    OrderStatusHistory.objects.create(order=order, old_status=old, new_status=new_status, note=note, actor=actor)
    if new_status == Order.Status.CANCELLED:
        from inventory.services import release_order_reservations
        release_order_reservations(order)
    return order
