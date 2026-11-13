from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLES = {
    "Administrateurs": None,
    "Gestionnaires": {
        "catalog": {"collection", "product", "productimage"},
        "inventory": {"stockitem", "stockmovement", "stockreservation"},
        "orders": {"customer", "deliveryzone", "order", "orderitem", "orderstatushistory"},
        "payments": {"payment", "paymentevent"},
    },
    "Opérateurs de vente": {
        "catalog": {"collection", "product"},
        "inventory": {"stockitem"},
        "orders": {"customer", "order", "orderitem"},
    },
}


class Command(BaseCommand):
    help = "Crée les groupes et permissions de l'équipe WESKA INK."

    def handle(self, *args, **options):
        for name, apps in ROLES.items():
            group, _ = Group.objects.get_or_create(name=name)
            if apps is None:
                permissions = Permission.objects.filter(content_type__app_label__in=["auth", "axes", "catalog", "inventory", "orders", "payments", "pos", "core"])
            else:
                permissions = Permission.objects.none()
                for app_label, models in apps.items():
                    permissions |= Permission.objects.filter(content_type__app_label=app_label, content_type__model__in=models)
                if name == "Gestionnaires":
                    permissions |= Permission.objects.filter(content_type__app_label__in=["catalog", "inventory", "orders", "payments"], codename__startswith="view_")
                elif name == "Opérateurs de vente":
                    permissions |= Permission.objects.filter(content_type__app_label__in=["catalog", "inventory", "orders"], codename__in=["view_collection", "view_product", "view_stockitem", "add_order", "view_order", "add_customer", "view_customer"])
            group.permissions.set(permissions.distinct())
            self.stdout.write(self.style.SUCCESS(f"Groupe prêt : {name}"))
