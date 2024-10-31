from django.shortcuts import render
from django.http import HttpResponse
from .models import Product

# Create your views here.


def home(request):
    products = Product.objects.all()
    return render(request, 'products/home.html', context={'products': products})
