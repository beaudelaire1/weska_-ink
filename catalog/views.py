from django.db.models import F, Q
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, render
from inventory.models import StockItem
from .models import Collection, Product


def _products():
    return Product.objects.filter(status=Product.Status.PUBLISHED).select_related("collection", "stock")


def catalog(request):
    products = _products()
    query = request.GET.get("q", "").strip()
    collection_id = request.GET.get("collection", "")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(short_description__icontains=query) | Q(sku__icontains=query))
    if collection_id.isdigit():
        products = products.filter(collection_id=int(collection_id))
    for param, lookup, multiplier in (("min_price", "price_cents__gte", 100), ("max_price", "price_cents__lte", 100)):
        raw_price = request.GET.get(param, "").strip()
        if raw_price:
            try:
                price_cents = int(Decimal(raw_price) * multiplier)
                products = products.filter(**{lookup: price_cents})
            except (InvalidOperation, ValueError):
                pass
    if request.GET.get("availability") == "in_stock":
        products = products.filter(stock__quantity_on_hand__gt=F("stock__quantity_reserved"))
    context = {"products": products, "collections": Collection.objects.filter(is_active=True), "query": query, "selected_collection": collection_id}
    template = "catalog/partials/product_grid.html" if request.htmx else "catalog/catalog.html"
    return render(request, template, context)


def collection(request, slug):
    selected = get_object_or_404(Collection, slug=slug, is_active=True)
    products = _products().filter(collection=selected)
    return render(request, "catalog/catalog.html", {"products": products, "collections": Collection.objects.filter(is_active=True), "active_collection": selected, "selected_collection": str(selected.id)})


def product_detail(request, slug):
    product = get_object_or_404(_products().prefetch_related("images"), slug=slug)
    related = _products().filter(collection=product.collection).exclude(pk=product.pk)[:3] if product.collection else []
    return render(request, "catalog/product_detail.html", {"product": product, "related_products": related})
