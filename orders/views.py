from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import logging
import stripe

from catalog.models import Product
from .cart import Cart
from .forms import CheckoutForm
from .models import Customer, Order
from .services import create_web_order

logger = logging.getLogger(__name__)


def cart_detail(request):
    cart = Cart(request)
    return render(request, "orders/cart.html", {"cart": cart})


def cart_fragment(request):
    return render(request, "orders/partials/mini_cart.html", {"cart": Cart(request)})


def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=Product.Status.PUBLISHED)
    if request.method == "POST":
        cart = Cart(request)
        try:
            quantity = int(request.POST.get("quantity", "1"))
        except ValueError:
            quantity = 1
        cart.add(product, max(1, min(quantity, 99)))
        if request.htmx:
            return HttpResponse(cart_fragment(request).content, headers={"HX-Trigger": "cartUpdated"})
        messages.success(request, f"{product.name} a été ajouté au panier.")
    return redirect("orders:cart")


def cart_update(request, product_id):
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", "1"))
        except ValueError:
            quantity = 1
        cart = Cart(request)
        cart.set_quantity(product_id, max(0, quantity))
        if request.htmx:
            return render(request, "orders/partials/cart_contents.html", {"cart": cart})
    return redirect("orders:cart")


def cart_remove(request, product_id):
    if request.method == "POST":
        cart = Cart(request)
        cart.remove(product_id)
        if request.htmx:
            return render(request, "orders/partials/cart_contents.html", {"cart": cart})
    return redirect("orders:cart")


def checkout(request):
    cart = Cart(request)
    if not cart.items:
        messages.info(request, "Votre panier est vide.")
        return redirect("catalog:list")
    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        email = data["email"].strip().lower()
        customer = Customer.objects.filter(email__iexact=email).first()
        if customer:
            customer.full_name, customer.phone = data["full_name"], data["phone"]
            customer.save(update_fields=["full_name", "phone"])
        else:
            customer = Customer.objects.create(full_name=data["full_name"], email=email, phone=data["phone"])
        try:
            order = create_web_order(customer, cart.items, data["fulfillment"], data.get("delivery_zone"), data.get("shipping_address"), data.get("shipping_postal_code"), data.get("shipping_city"))
        except ValidationError as error:
            form.add_error(None, error.message)
        else:
            cart.clear()
            from payments.services import create_checkout_session
            try:
                checkout_url = create_checkout_session(order, request)
            except stripe.StripeError:
                logger.exception("Stripe Checkout could not be created for order %s", order.number)
                checkout_url = None
            if checkout_url:
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(checkout_url)
            if settings.STRIPE_SECRET_KEY:
                messages.error(request, "La commande est enregistrée mais la session de paiement n’a pas pu s’ouvrir. Le stock reste réservé temporairement.")
            else:
                messages.warning(request, "La commande est enregistrée et le stock réservé. Le paiement Stripe doit être configuré avant l’encaissement en ligne.")
            return redirect("orders:confirmation", number=order.number)
    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


def order_confirmation(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number, channel=Order.Channel.WEB)
    return render(request, "orders/confirmation.html", {"order": order, "payment_configured": bool(settings.STRIPE_SECRET_KEY), "payment_started": order.payments.exists()})
