from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from catalog.models import Collection, Product


def home(request):
    collections = Collection.objects.filter(is_active=True)[:3]
    products = Product.objects.filter(status=Product.Status.PUBLISHED).select_related("collection")[:4]
    return render(request, "core/home.html", {"collections": collections, "featured_products": products})


def about(request):
    return render(request, "core/about.html")


def contact(request):
    return render(request, "core/contact.html")


def faq(request):
    return render(request, "core/faq.html")


def legal(request):
    return render(request, "core/legal.html")


def robots(request):
    return HttpResponse("User-agent: *\nAllow: /\n", content_type="text/plain")
