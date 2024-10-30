from django.shortcuts import render, redirect
from django.contrib.auth import logout
# Create your views here.

def home(request):
    return render(request, "users/home.html")


def logout_view(request):
    logout(request) #remueve la sesión del usuario
    return redirect("/") #redirige a la página principal

def profile(request):
    return render(request, "users/profile.html")