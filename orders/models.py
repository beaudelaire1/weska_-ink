import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    full_name = models.CharField("nom complet", max_length=160)
    email = models.EmailField("adresse e-mail", blank=True, db_index=True)
    phone = models.CharField("téléphone", max_length=40, blank=True)
    created_at = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "client"
        verbose_name_plural = "clients"

    def __str__(self):
        return f"{self.full_name} · {self.email}"


class DeliveryZone(models.Model):
    name = models.CharField("zone", max_length=100, unique=True)
    communes = models.CharField("communes desservies", max_length=240, help_text="Ex. Cayenne, Matoury, Rémire-Montjoly")
    fee_cents = models.PositiveIntegerField("frais de livraison (centimes)", default=0)
    is_active = models.BooleanField("active", default=True)
    display_order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "zone de livraison"
        verbose_name_plural = "zones de livraison"

    def __str__(self):
        fee = f"{self.fee_cents / 100:.2f} €".replace(".", ",")
        return f"{self.name} · {self.communes} · {fee}"


class Order(models.Model):
    class Channel(models.TextChoices):
        WEB = "WEB", "Boutique en ligne"
        POS = "POS", "Vente physique"

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente de paiement"
        PAID = "PAID", "Payée"
        PROCESSING = "PROCESSING", "En préparation"
        READY = "READY", "Prête à remettre"
        COMPLETED = "COMPLETED", "Terminée"
        CANCELLED = "CANCELLED", "Annulée"
        REFUNDED = "REFUNDED", "Remboursée"

    class Fulfillment(models.TextChoices):
        PICKUP = "PICKUP", "Retrait"
        DELIVERY = "DELIVERY", "Livraison"

    number = models.CharField("numéro", max_length=32, unique=True, db_index=True, blank=True)
    customer = models.ForeignKey(Customer, verbose_name="client", on_delete=models.PROTECT, related_name="orders", null=True, blank=True)
    channel = models.CharField("canal", max_length=8, choices=Channel.choices, db_index=True)
    status = models.CharField("statut", max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    fulfillment = models.CharField("remise", max_length=10, choices=Fulfillment.choices, default=Fulfillment.PICKUP)
    delivery_zone = models.ForeignKey(DeliveryZone, verbose_name="zone de livraison", on_delete=models.SET_NULL, null=True, blank=True)
    delivery_zone_name = models.CharField("zone enregistrée", max_length=100, blank=True)
    shipping_address = models.CharField("adresse", max_length=200, blank=True)
    shipping_postal_code = models.CharField("code postal", max_length=20, blank=True)
    shipping_city = models.CharField("commune", max_length=100, blank=True)
    subtotal_cents = models.PositiveIntegerField("sous-total", default=0)
    shipping_cents = models.PositiveIntegerField("frais de remise", default=0)
    discount_cents = models.PositiveIntegerField("réduction", default=0)
    total_cents = models.PositiveIntegerField("total", default=0)
    payment_method = models.CharField("moyen de paiement", max_length=24, blank=True)
    tracking_reference = models.CharField("référence de suivi", max_length=120, blank=True)
    notes = models.TextField("notes internes", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="créée par", on_delete=models.SET_NULL, null=True, blank=True, related_name="weska_orders")
    created_at = models.DateTimeField("créée le", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("modifiée le", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "commande"
        verbose_name_plural = "commandes"
        indexes = [models.Index(fields=["channel", "status", "created_at"])]

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f"WI-{timezone.localdate():%y%m%d}-{secrets.token_hex(8).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} · {self.get_status_display()}"

    @property
    def payment_method_label(self):
        labels = {"CASH": "Espèces", "CARD": "Carte bancaire", "TRANSFER": "Virement", "OTHER": "Autre"}
        return labels.get(self.payment_method, self.payment_method)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="commande", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", verbose_name="produit", on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    product_name = models.CharField("désignation", max_length=160)
    sku = models.CharField("référence", max_length=60)
    quantity = models.PositiveIntegerField("quantité")
    unit_price_cents = models.PositiveIntegerField("prix unitaire TTC", default=0)
    unit_cost_cents = models.PositiveIntegerField("coût unitaire enregistré", null=True, blank=True)

    class Meta:
        verbose_name = "article commandé"
        verbose_name_plural = "articles commandés"

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total_cents(self):
        return self.quantity * self.unit_price_cents


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, verbose_name="commande", on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField("ancien statut", max_length=12, blank=True)
    new_status = models.CharField("nouveau statut", max_length=12, choices=Order.Status.choices)
    note = models.CharField("note", max_length=240, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="utilisateur", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("date", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "historique de commande"
        verbose_name_plural = "historiques de commande"

    def __str__(self):
        return f"{self.order.number} · {self.old_status} → {self.new_status}"
