from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class StockItem(models.Model):
    product = models.OneToOneField("catalog.Product", verbose_name="produit", on_delete=models.PROTECT, related_name="stock")
    quantity_on_hand = models.PositiveIntegerField("quantité physique", default=0)
    quantity_reserved = models.PositiveIntegerField("quantité réservée", default=0)
    alert_threshold = models.PositiveIntegerField("seuil d'alerte", default=3)
    updated_at = models.DateTimeField("mis à jour le", auto_now=True)

    class Meta:
        ordering = ["product__name"]
        verbose_name = "stock produit"
        verbose_name_plural = "stocks produits"
        constraints = [models.CheckConstraint(condition=models.Q(quantity_reserved__lte=models.F("quantity_on_hand")), name="stock_reserved_lte_on_hand")]

    def __str__(self):
        return f"{self.product} — {self.available} disponible(s)"

    @property
    def available(self):
        return self.quantity_on_hand - self.quantity_reserved


class StockReservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CONSUMED = "CONSUMED", "Consommée"
        RELEASED = "RELEASED", "Libérée"

    order = models.ForeignKey("orders.Order", verbose_name="commande", on_delete=models.CASCADE, related_name="reservations")
    product = models.ForeignKey("catalog.Product", verbose_name="produit", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("quantité")
    status = models.CharField("état", max_length=12, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    expires_at = models.DateTimeField("expire le", db_index=True)
    created_at = models.DateTimeField("créée le", auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "product"], name="unique_reservation_per_order_product")]
        verbose_name = "réservation de stock"
        verbose_name_plural = "réservations de stock"

    def __str__(self):
        return f"{self.quantity} × {self.product} · {self.get_status_display()}"


class StockMovement(models.Model):
    class Type(models.TextChoices):
        RECEIPT = "RECEIPT", "Réception"
        WEB_SALE = "WEB_SALE", "Vente en ligne"
        POS_SALE = "POS_SALE", "Vente physique"
        ADJUSTMENT = "ADJUSTMENT", "Ajustement"
        RETURN = "RETURN", "Retour"
        CANCELLATION = "CANCELLATION", "Annulation"

    stock_item = models.ForeignKey(StockItem, verbose_name="stock", on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField("type de mouvement", max_length=16, choices=Type.choices)
    quantity_delta = models.IntegerField("variation de quantité")
    reason = models.CharField("motif", max_length=240, blank=True)
    order = models.ForeignKey("orders.Order", verbose_name="commande", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="utilisateur", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("date", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "mouvement de stock"
        verbose_name_plural = "mouvements de stock"

    def __str__(self):
        return f"{self.get_movement_type_display()} · {self.quantity_delta:+d} · {self.stock_item.product}"

    def clean(self):
        if self.quantity_delta == 0:
            raise ValidationError({"quantity_delta": "La variation doit être différente de zéro."})
