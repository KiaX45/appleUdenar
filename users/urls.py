from django.urls import path
from . import views

urlpatterns = [

    path(route="userLogin/", view=views.login, name="userLogin"),
    path(route="logout/", view=views.logout_view, name="logout"),
    path(route="profile/", view=views.profile, name="profile"),
    path(route="adminprofile/", view=views.adminprofile, name="adminprofile"),
    path(route="redirect_after_login/", view=views.redirect_after_login, name="redirect_after_login"),
   
    #path('formulario/', views.mostrar_formulario, name='mostrar_formulario'),
    
]


