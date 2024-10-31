from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
# Create your views here.

def login(request):
    return render(request, "users/login.html")

def adminprofile(request):
    return render(request, "users/adminprofile.html")


def logout_view(request):
    logout(request) #remueve la sesión del usuario
    return redirect("/") #redirige a la página principal

def profile(request):
    return render(request, "users/profile.html")

@login_required
def redirect_after_login(request):
    if request.user.is_staff:  # O usa is_superuser si necesitas diferenciar más
        return redirect('/profileAdmin')
    else:
        return redirect('/profile')