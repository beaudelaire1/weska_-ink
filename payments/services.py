from datetime import timedelta

import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from inventory.services import consume_order_reservations, release_order_reservations
from orders.models import Order, OrderStatusHistory
from .models import Payment, PaymentEvent


def send_order_confirmation(order_id):
    order = Order.objects.select_related("customer").prefetch_related("items").filter(pk=order_id).first()
    if not order or not order.customer or not order.customer.email:
        return
    lines = [f"{item.quantity} × {item.product_name} — {item.line_total_cents / 100:.2f} €" for item in order.items.all()]
    body = "Bonjour " + order.customer.full_name + ",\n\nNous avons bien reçu ton paiement.\n\n" + "\n".join(lines) + f"\n\nTotal : {order.total_cents / 100:.2f} €\nCommande : {order.number}\n\nMerci,\nWESKA INK"
    send_mail(f"Paiement confirmé · {order.number}", body, settings.DEFAULT_FROM_EMAIL, [order.customer.email], fail_silently=True)


def create_checkout_session(order, request):
    if not settings.STRIPE_SECRET_KEY:
        return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = [{
        "price_data": {"currency": "eur", "product_data": {"name": item.product_name, "metadata": {"sku": item.sku}}, "unit_amount": item.unit_price_cents},
        "quantity": item.quantity,
    } for item in order.items.all()]
    if order.shipping_cents:
        line_items.append({"price_data": {"currency": "eur", "product_data": {"name": "Livraison"}, "unit_amount": order.shipping_cents}, "quantity": 1})
    checkout = stripe.checkout.Session.create(
        mode="payment", line_items=line_items,
        customer_email=order.customer.email if order.customer else None,
        expires_at=int((timezone.now() + timedelta(minutes=35)).timestamp()),
        payment_method_types=["card"],
        success_url=request.build_absolute_uri(f"/commande/confirmation/{order.number}/?session_id={{CHECKOUT_SESSION_ID}}"),
        cancel_url=request.build_absolute_uri("/commande/panier/"),
        metadata={"order_number": order.number},
        idempotency_key=f"weska-checkout-{order.number}",
    )
    Payment.objects.create(order=order, provider="stripe", external_id=checkout.id, amount_cents=order.total_cents)
    return checkout.url


@transaction.atomic
def process_stripe_event(event):
    event_obj = event["data"]["object"]
    safe_payload = {
        "id": event["id"],
        "type": event["type"],
        "data": {"object": {key: event_obj.get(key) for key in ("id", "metadata", "amount_total", "currency", "payment_status", "expires_at")}},
    }
    record, created = PaymentEvent.objects.get_or_create(
        provider_event_id=event["id"],
        defaults={"event_type": event["type"], "payload": safe_payload},
    )
    record = PaymentEvent.objects.select_for_update().get(pk=record.pk)
    if record.processed_at:
        return False

    def reject(reason):
        record.processing_error = reason
        record.processed_at = timezone.now()
        record.save(update_fields=["processing_error", "processed_at"])
        return False

    if event["type"] == "checkout.session.completed" and event_obj.get("payment_status") == "paid":
        order = Order.objects.select_for_update().get(number=event_obj["metadata"]["order_number"])
        if event_obj.get("amount_total") != order.total_cents or event_obj.get("currency", "eur").lower() != "eur":
            return reject("Le montant ou la devise de la session Stripe ne correspond pas à la commande.")
        if order.status == Order.Status.PENDING:
            consume_order_reservations(order, order.channel)
            old_status = order.status
            order.status = Order.Status.PAID
            order.save(update_fields=["status", "updated_at"])
            OrderStatusHistory.objects.create(order=order, old_status=old_status, new_status=order.status, note="Paiement confirmé par Stripe.")
            transaction.on_commit(lambda order_id=order.pk: send_order_confirmation(order_id))
        elif order.status != Order.Status.PAID:
            return reject(f"Paiement reçu pour une commande au statut {order.get_status_display()}; rapprochement manuel requis.")
        Payment.objects.filter(order=order, provider="stripe", external_id=event_obj["id"]).update(status=Payment.Status.PAID)
        Payment.objects.filter(order=order, provider="stripe", status=Payment.Status.CREATED).update(status=Payment.Status.PAID)
    elif event["type"] == "checkout.session.expired":
        order_number = event_obj.get("metadata", {}).get("order_number")
        if order_number:
            order = Order.objects.select_for_update().filter(number=order_number, status=Order.Status.PENDING).first()
            if order:
                release_order_reservations(order)
                old_status = order.status
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status", "updated_at"])
                OrderStatusHistory.objects.create(order=order, old_status=old_status, new_status=order.status, note="Session de paiement expirée.")
    record.processed_at = timezone.now()
    record.save(update_fields=["processed_at", "processing_error"])
    return created
