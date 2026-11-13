from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.catalog, name="list"),
    path("collection/<slug:slug>/", views.collection, name="collection"),
    path("<slug:slug>/", views.product_detail, name="product"),
]
