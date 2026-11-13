from django.core.management import BaseCommand, call_command
from django.utils.text import slugify

from catalog.models import Collection, Product
from inventory.models import StockItem, StockMovement
from inventory.services import adjust_stock


class Command(BaseCommand):
    help = "Ajoute un petit catalogue de démonstration (prix et références à remplacer)."

    def handle(self, *args, **options):
        call_command("setup_roles", verbosity=0)
        collections = [
            ("Botanique", "Fougères, fleurs et petits trésors végétaux."),
            ("Soleil & symboles", "Des signes libres, des astres et des énergies douces."),
            ("Lignes libres", "Des dessins fins pour celles et ceux qui aiment la simplicité."),
        ]
        collection_map = {name: Collection.objects.get_or_create(name=name, defaults={"slug": slugify(name), "description": description})[0] for name, description in collections}
        examples = [
            ("Rose sauvage", "WI-BOT-001", "Botanique", 1800, 12, "Une rose fine pour une envie qui fleurit."),
            ("Fougère de Guyane", "WI-BOT-002", "Botanique", 1600, 12, "Une fronde légère inspirée des sous-bois."),
            ("Soleil levant", "WI-SOL-001", "Soleil & symboles", 1500, 10, "Un petit soleil à porter tout près."),
            ("Lune libre", "WI-SOL-002", "Soleil & symboles", 1700, 8, "Un croissant dessiné pour suivre ton rythme."),
            ("Trait d'union", "WI-LIG-001", "Lignes libres", 1400, 10, "Une ligne simple, un sens à toi."),
            ("Papillon nocturne", "WI-LIG-002", "Lignes libres", 1900, 6, "Un petit flash libre entre ombre et lumière."),
        ]
        for name, sku, collection_name, price, stock_count, short in examples:
            product, created = Product.objects.get_or_create(sku=sku, defaults={
                "name": name, "slug": slugify(name), "collection": collection_map[collection_name],
                "short_description": short, "description": short,
                "dimensions": "5 × 7 cm (exemple)", "wear_duration": "À confirmer",
                "application_instructions": "À compléter selon la notice fabricant.",
                "precautions": "Vérifier les précautions fabricant avant publication.",
                "price_cents": price, "status": Product.Status.PUBLISHED, "is_featured": name == "Rose sauvage",
            })
            stock, _ = StockItem.objects.get_or_create(product=product)
            if created and stock_count:
                adjust_stock(product, stock_count, StockMovement.Type.RECEIPT, "Stock de démonstration à remplacer", actor=None)
        self.stdout.write(self.style.SUCCESS("Catalogue de démonstration créé. Références, prix, stocks, images et caractéristiques sont des exemples."))
