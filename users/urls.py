from django.urls import path
from . import views

urlpatterns = [
    path(route="", view=views.home, name="home"),
    path(route="logout/", view=views.logout_view, name="logout"),
    path(route="profile/", view=views.profile, name="profile"),

]


