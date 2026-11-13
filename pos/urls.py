from django.urls import path
from . import views

app_name = "pos"
urlpatterns = [path("", views.sale, name="sale"), path("tableau-de-bord/", views.dashboard, name="dashboard"), path("commandes/", views.order_list, name="orders"), path("commandes/<str:number>/statut/", views.update_order, name="update_order"), path("justificatif/<str:number>/", views.receipt, name="receipt")]
