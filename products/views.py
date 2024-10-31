from django.shortcuts import render
from django.http import HttpResponse
from .models import Product

# Create your views here.

def home(request):
    #obtenemos todos los productos
    products = Product.objects.all()

    return render(request, 'products/home.html', context={'products': products})


def products(request):
    products = Product.objects.all()
    return render(request, 'products/products.html', context={'products': products})
