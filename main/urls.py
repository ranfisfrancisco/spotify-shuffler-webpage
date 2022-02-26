from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_request, name="login"),
    path("callback", views.callback, name="callback"),
    path("select", views.select, name="select"),
]