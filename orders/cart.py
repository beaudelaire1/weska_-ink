from catalog.models import Product
from inventory.models import StockItem


class Cart:
    session_key = "weska_cart"

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(self.session_key, {})

    def save(self):
        self.session[self.session_key] = self.data
        self.session.modified = True

    def add(self, product, quantity=1):
        key = str(product.pk)
        current = int(self.data.get(key, 0))
        stock = StockItem.objects.filter(product=product).first()
        available = stock.available if stock else 0
        self.data[key] = min(current + quantity, available)
        self.save()

    def set_quantity(self, product_id, quantity):
        product = Product.objects.filter(pk=product_id, status=Product.Status.PUBLISHED).first()
        if not product:
            self.data.pop(str(product_id), None)
        elif quantity <= 0:
            self.data.pop(str(product_id), None)
        else:
            stock = StockItem.objects.filter(product=product).first()
            available = stock.available if stock else 0
            if available:
                self.data[str(product_id)] = min(quantity, available)
            else:
                self.data.pop(str(product_id), None)
        self.save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self.save()

    def clear(self):
        self.data = {}
        self.save()

    @property
    def items(self):
        ids = [int(key) for key, qty in self.data.items() if str(key).isdigit() and int(qty) > 0]
        products = Product.objects.filter(pk__in=ids, status=Product.Status.PUBLISHED).select_related("stock")
        rows = []
        for product in products:
            quantity = int(self.data.get(str(product.pk), 0))
            stock = getattr(product, "stock", None)
            if quantity and stock and stock.available:
                quantity = min(quantity, stock.available)
                rows.append({"product": product, "quantity": quantity, "line_total_cents": product.price_cents * quantity})
        return rows

    @property
    def total(self):
        return sum(row["line_total_cents"] for row in self.items)

    @property
    def count(self):
        return sum(row["quantity"] for row in self.items)
