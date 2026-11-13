from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from catalog.models import Product
from core.permissions import staff_with
from .models import StockItem, StockMovement
from .services import adjust_stock


@user_passes_test(staff_with("inventory.view_stockitem"))
def stock_list(request):
    rows = StockItem.objects.select_related("product", "product__collection")
    low_stock = [row for row in rows if row.available <= row.alert_threshold]
    movements = StockMovement.objects.select_related("stock_item__product", "actor")[:12]
    return render(request, "inventory/stock_list.html", {"stock_items": rows, "low_stock": low_stock, "movements": movements, "products": Product.objects.filter(status__in=[Product.Status.PUBLISHED, Product.Status.UNAVAILABLE]), "can_adjust_stock": request.user.is_superuser or request.user.has_perm("inventory.add_stockmovement")})


@user_passes_test(staff_with("inventory.add_stockmovement"))
def stock_movement(request):
    if request.method != "POST":
        return redirect("inventory:list")
    try:
        product = Product.objects.get(pk=request.POST.get("product"))
        quantity = int(request.POST.get("quantity", "0"))
        kind = request.POST.get("movement_type", "")
        reason = request.POST.get("reason", "").strip()
        if kind not in (StockMovement.Type.RECEIPT, StockMovement.Type.ADJUSTMENT, StockMovement.Type.RETURN):
            raise ValidationError("Type de mouvement non autorisé.")
        if not reason or quantity == 0 or (kind != StockMovement.Type.ADJUSTMENT and quantity < 0):
            raise ValidationError("Saisissez un motif et une variation valide. Les ajustements peuvent être positifs ou négatifs.")
        adjust_stock(product, quantity, kind, reason, request.user)
        messages.success(request, f"Stock mis à jour pour {product.name}.")
    except (Product.DoesNotExist, ValueError, ValidationError) as error:
        messages.error(request, str(error) if not isinstance(error, Product.DoesNotExist) else "Produit introuvable.")
    return redirect("inventory:list")
