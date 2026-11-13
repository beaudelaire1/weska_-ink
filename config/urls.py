from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from catalog.sitemaps import CollectionsSitemap, ProductsSitemap

sitemaps = {"collections": CollectionsSitemap, "products": ProductsSitemap}

admin.site.site_header = "WESKA INK · Administration"
admin.site.site_title = "WESKA INK"
admin.site.index_title = "Gestion de la boutique"

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("django-admin/", admin.site.urls),
    path("", include("core.urls")),
    path("boutique/", include("catalog.urls")),
    path("commande/", include("orders.urls")),
    path("paiements/", include("payments.urls")),
    path("equipe/stock/", include("inventory.urls")),
    path("equipe/caisse/", include("pos.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
