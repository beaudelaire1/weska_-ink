from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Créé"
        PAID = "PAID", "Payé"
        FAILED = "FAILED", "Échec"
        REFUNDED = "REFUNDED", "Remboursé"

    order = models.ForeignKey("orders.Order", verbose_name="commande", on_delete=models.PROTECT, related_name="payments")
    provider = models.CharField("prestataire", max_length=24, default="stripe")
    external_id = models.CharField("identifiant prestataire", max_length=160, blank=True, db_index=True)
    amount_cents = models.PositiveIntegerField("montant", default=0)
    currency = models.CharField("devise", max_length=3, default="eur")
    status = models.CharField("statut", max_length=12, choices=Status.choices, default=Status.CREATED)
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "paiement"
        verbose_name_plural = "paiements"

    def __str__(self):
        return f"{self.order.number} · {self.get_status_display()}"


class PaymentEvent(models.Model):
    provider_event_id = models.CharField("identifiant événement", max_length=160, unique=True)
    event_type = models.CharField("type", max_length=120)
    payload = models.JSONField("contenu", default=dict)
    processed_at = models.DateTimeField("traité le", null=True, blank=True)
    processing_error = models.TextField("erreur de traitement", blank=True)
    received_at = models.DateTimeField("reçu le", auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "événement de paiement"
        verbose_name_plural = "événements de paiement"

    def __str__(self):
        return f"{self.provider_event_id} · {self.event_type}"
