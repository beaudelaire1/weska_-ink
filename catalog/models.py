from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Collection(models.Model):
    name = models.CharField("nom", max_length=100, unique=True)
    slug = models.SlugField("slug", max_length=110, unique=True)
    description = models.TextField("description", blank=True)
    cover = models.ImageField("visuel de couverture", upload_to="collections/", blank=True)
    is_active = models.BooleanField("visible", default=True)
    display_order = models.PositiveSmallIntegerField("ordre d'affichage", default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "collection"
        verbose_name_plural = "collections"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:collection", kwargs={"slug": self.slug})


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        PUBLISHED = "PUBLISHED", "Publié"
        UNAVAILABLE = "UNAVAILABLE", "Indisponible"
        ARCHIVED = "ARCHIVED", "Archivé"

    name = models.CharField("nom", max_length=160)
    slug = models.SlugField("slug", max_length=180, unique=True)
    sku = models.CharField("référence SKU", max_length=60, unique=True)
    collection = models.ForeignKey(Collection, verbose_name="collection", on_delete=models.PROTECT, related_name="products", null=True, blank=True)
    short_description = models.CharField("description courte", max_length=240, blank=True)
    description = models.TextField("description", blank=True)
    price_cents = models.PositiveIntegerField("prix TTC (centimes)", validators=[MinValueValidator(1)])
    cost_cents = models.PositiveIntegerField("coût d'achat (centimes)", null=True, blank=True)
    dimensions = models.CharField("dimensions", max_length=100, blank=True)
    wear_duration = models.CharField("durée de tenue", max_length=100, blank=True)
    application_instructions = models.TextField("mode d'application", blank=True)
    precautions = models.TextField("précautions", blank=True)
    image = models.ImageField("visuel principal", upload_to="products/", blank=True)
    status = models.CharField("état", max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    is_featured = models.BooleanField("mis en avant", default=False)
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        ordering = ["-is_featured", "name"]
        verbose_name = "produit"
        verbose_name_plural = "produits"
        indexes = [models.Index(fields=["status", "collection"])]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def price(self):
        return self.price_cents / 100


class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name="produit", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("image", upload_to="products/gallery/")
    alt_text = models.CharField("texte alternatif", max_length=180, blank=True)
    display_order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "image produit"
        verbose_name_plural = "images produit"

    def __str__(self):
        return f"Image de {self.product}"
