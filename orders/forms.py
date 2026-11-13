from django import forms
import unicodedata
from .models import DeliveryZone, Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(label="Nom complet", max_length=160)
    email = forms.EmailField(label="Adresse e-mail")
    phone = forms.CharField(label="Téléphone", max_length=40, required=False)
    fulfillment = forms.ChoiceField(label="Mode de remise", choices=Order.Fulfillment.choices, widget=forms.RadioSelect)
    delivery_zone = forms.ModelChoiceField(label="Zone de livraison", queryset=DeliveryZone.objects.none(), required=False, empty_label="Choisir une zone")
    shipping_address = forms.CharField(label="Adresse", max_length=200, required=False)
    shipping_postal_code = forms.CharField(label="Code postal", max_length=20, required=False)
    shipping_city = forms.CharField(label="Commune", max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivery_zone"].queryset = DeliveryZone.objects.filter(is_active=True)
        if not self.fields["delivery_zone"].queryset.exists():
            self.fields["fulfillment"].choices = [(Order.Fulfillment.PICKUP, "Retrait")]

    def clean(self):
        data = super().clean()
        if data.get("fulfillment") == Order.Fulfillment.DELIVERY:
            if not data.get("delivery_zone"):
                self.add_error("delivery_zone", "Aucune zone disponible ou aucune zone sélectionnée.")
            for field in ("shipping_address", "shipping_postal_code", "shipping_city"):
                if not data.get(field):
                    self.add_error(field, "Ce champ est requis pour une livraison.")
            zone, city = data.get("delivery_zone"), data.get("shipping_city", "")
            if zone and city:
                normalize = lambda value: "".join(char for char in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(char)).strip()
                covered = {normalize(commune) for commune in zone.communes.split(",") if commune.strip()}
                if normalize(city) not in covered:
                    self.add_error("shipping_city", "Cette commune ne figure pas dans la zone sélectionnée.")
        return data


class POSCustomerForm(forms.Form):
    full_name = forms.CharField(label="Nom du client (facultatif)", max_length=160, required=False)
    email = forms.EmailField(label="E-mail (facultatif)", required=False)
    phone = forms.CharField(label="Téléphone (facultatif)", max_length=40, required=False)
    payment_method = forms.ChoiceField(label="Encaissement", choices=[])

    def __init__(self, *args, choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].choices = choices or []
