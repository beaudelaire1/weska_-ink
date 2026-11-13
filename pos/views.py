from datetime import datetime, time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from catalog.models import Product
from core.permissions import staff_with
from inventory.models import StockItem
from orders.forms import POSCustomerForm
from orders.models import Customer, Order
from orders.services import ALLOWED_TRANSITIONS, create_pos_order, transition_order


def payment_choices():
    labels = {"CASH": "Espèces", "CARD": "Carte bancaire", "TRANSFER": "Virement", "OTHER": "Autre"}
    return [(method, labels.get(method, method.title())) for method in settings.POS_PAYMENT_METHODS]


@user_passes_test(staff_with("orders.add_order"))
def sale(request):
    products = Product.objects.filter(status=Product.Status.PUBLISHED).select_related("collection", "stock").order_by("name")
    form = POSCustomerForm(request.POST or None, choices=payment_choices())
    if request.method == "POST":
        rows = []
        for product in products:
            try:
                quantity = max(0, int(request.POST.get(f"qty_{product.pk}", "0")))
            except ValueError:
                quantity = 0
            if quantity:
                rows.append({"product": product, "quantity": quantity})
        if not rows:
            form.add_error(None, "Sélectionnez au moins un article.")
        if form.is_valid() and rows:
            data = form.cleaned_data
            customer = None
            if data["email"]:
                customer, _ = Customer.objects.get_or_create(email=data["email"].strip().lower(), defaults={"full_name": data["full_name"] or "Client caisse", "phone": data["phone"]})
            elif data["full_name"] or data["phone"]:
                customer = Customer.objects.create(full_name=data["full_name"] or "Client caisse", email="", phone=data["phone"])
            try:
                order = create_pos_order(rows, data["payment_method"], request.user, customer)
            except ValidationError as error:
                form.add_error(None, error.message)
            else:
                messages.success(request, f"Vente {order.number} enregistrée.")
                return redirect("pos:receipt", number=order.number)
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    return render(request, "pos/sale.html", {"products": products, "form": form})


@user_passes_test(staff_with("orders.view_order"))
def dashboard(request):
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, time.min))
    paid = Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.PROCESSING, Order.Status.READY, Order.Status.COMPLETED])
    today_paid = paid.filter(created_at__gte=start)
    products_count = Product.objects.filter(status=Product.Status.PUBLISHED).count()
    low_stock = [stock for stock in StockItem.objects.select_related("product") if stock.available <= stock.alert_threshold]
    context = {
        "today_sales": today_paid.aggregate(value=Sum("total_cents"))["value"] or 0,
        "today_count": today_paid.count(), "web_sales": paid.filter(channel="WEB").aggregate(value=Sum("total_cents"))["value"] or 0,
        "pos_sales": paid.filter(channel="POS").aggregate(value=Sum("total_cents"))["value"] or 0,
        "products_count": products_count, "low_stock": low_stock[:8],
        "pending_orders": Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.PROCESSING, Order.Status.READY]).select_related("customer")[:8],
        "best_sellers": Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.COMPLETED, Order.Status.PROCESSING, Order.Status.READY]).values("items__product_name").annotate(sold=Sum("items__quantity")).order_by("-sold")[:5],
    }
    return render(request, "pos/dashboard.html", context)


@user_passes_test(staff_with("orders.view_order"))
def order_list(request):
    orders = Order.objects.select_related("customer").all()
    channel = request.GET.get("channel")
    status = request.GET.get("status")
    if channel in dict(Order.Channel.choices):
        orders = orders.filter(channel=channel)
    if status in dict(Order.Status.choices):
        orders = orders.filter(status=status)
    orders = list(orders[:100])
    labels = dict(Order.Status.choices)
    for order in orders:
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        order.status_options = [(order.status, f"— {labels[order.status]} —")] + [(value, label) for value, label in Order.Status.choices if value in allowed]
    return render(request, "pos/order_list.html", {"orders": orders, "channels": Order.Channel.choices, "statuses": Order.Status.choices, "selected_channel": channel, "selected_status": status, "can_update_orders": request.user.is_superuser or request.user.has_perm("orders.change_order")})


@user_passes_test(staff_with("orders.change_order"))
def update_order(request, number):
    order = get_object_or_404(Order, number=number)
    if request.method == "POST":
        try:
            new_status = request.POST.get("status")
            if new_status == order.status:
                messages.info(request, "Aucun changement de statut à enregistrer.")
            else:
                transition_order(order, new_status, request.user, request.POST.get("note", ""))
                messages.success(request, "Statut de commande mis à jour.")
        except ValidationError as error:
            messages.error(request, error.message)
    return redirect("pos:orders")


@user_passes_test(staff_with("orders.view_order"))
def receipt(request, number):
    order = get_object_or_404(Order.objects.select_related("customer", "created_by").prefetch_related("items"), number=number, channel=Order.Channel.POS)
    return render(request, "pos/receipt.html", {"order": order})
