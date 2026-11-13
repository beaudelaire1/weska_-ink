from django.urls import path
from . import views

app_name = "orders"
urlpatterns = [
    path("panier/", views.cart_detail, name="cart"),
    path("panier/ajouter/<int:product_id>/", views.cart_add, name="cart_add"),
    path("panier/modifier/<int:product_id>/", views.cart_update, name="cart_update"),
    path("panier/supprimer/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("validation/", views.checkout, name="checkout"),
    path("confirmation/<str:number>/", views.order_confirmation, name="confirmation"),
]
