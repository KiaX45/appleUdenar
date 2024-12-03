from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import pandas as pd
from products.models import Product

# Create your views here.

def login(request):
    return render(request, "users/login.html")

@login_required
def adminprofile(request):
    if request.user.is_staff == False:
        return redirect('/')

    nombresProduct = Product.objects.values_list('name', flat=True)
    soldProduct = Product.objects.values_list('quantity_sold', flat=True)
    df = pd.DataFrame({'nombres': nombresProduct, 'cantidad': soldProduct})

    price = Product.objects.values_list('price', flat=True)
    profit = map(lambda x , y: x*y, soldProduct, price)
    profitGraph = pd.DataFrame({'nombres': nombresProduct, 'profit': profit})

    fig = px.bar(df, x='nombres', y='cantidad', title='Cantidad de productos vendidos')
    fig2 = px.bar(profitGraph, x='nombres', y='profit', title='Ganancias por producto')

    plot_quantity = json.dumps(fig, cls=PlotlyJSONEncoder)  
    plot_profit = json.dumps(fig2, cls=PlotlyJSONEncoder)

    context = {
        'plot_quantity': plot_quantity,
        'plot_profit': plot_profit
    }


    return render(request, "users/adminProfile.html", context)


def logout_view(request):
    logout(request) #remueve la sesión del usuario
    return redirect("/") #redirige a la página principal

def profile(request):
    return render(request, "users/profile.html")

@login_required
def redirect_after_login(request):
    if request.user.is_staff:  # O usa is_superuser si necesitas diferenciar más
        return redirect('/adminprofile')
    else:
        return redirect('/profile')
    

from django import forms
from products.models import Product
from django.http import JsonResponse

class MiFormulario(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

def mostrar_formulario(request):
    if request.method == 'POST':
        form = MiFormulario(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'})
    
    form = MiFormulario()
    return render(request, 'users/test.html', {'form': form})


