from django.urls import path
from . import views

urlpatterns = [

    path(route="userLogin/", view=views.home, name="home"),
    path(route="logout/", view=views.logout_view, name="logout"),
    path(route="profile/", view=views.profile, name="profile"),
    path(route="adminprofile/", view=views.adminprofile, name="adminprofile"),

]


