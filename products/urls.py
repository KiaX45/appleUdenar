from django.urls import path, include
from . import views


app_name = "products"

urlpatterns = [
    path(route="", view=views.home, name="home"),
    path('product/create/', views.create_product, name='create_product'),
    path('product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('product/update/<int:pk>/', views.update_product, name='update_product'),
    path('create_cart/<int:product_id>/', views.add_to_cart, name='create_cart'),
    path('cart/', views.get_cart_items, name='cart'),
    path('cart/delete/<int:cart_item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('product/dashboard/', views.dashboard, name='dashboard'),  
    path('cart/edit/<int:cart_item_id>/', views.edit_cart_item, name='edit_cart_item'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('payment_succes/', views.payment_success, name='payment_success'),
    path('payment_succes/checkout/', views.checkout, name='checkout'),
    path('product/change_currency/<str:currency>/', views.currency_change, name='currency_change'),
    path('product/email/', views.send_email, name='send_email'),

]
