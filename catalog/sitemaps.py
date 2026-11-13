from django.contrib.sitemaps import Sitemap
from .models import Collection, Product


class ProductsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(status=Product.Status.PUBLISHED)

    def lastmod(self, item):
        return item.updated_at


class CollectionsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Collection.objects.filter(is_active=True)
