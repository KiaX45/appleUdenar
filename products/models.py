from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_formatted = models.CharField(max_length=255, default='')
    stock = models.IntegerField()
    image = CloudinaryField('image', folder='products/')  # Reemplazamos image_url por este campo
    quantity_sold = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'products'

class Cart(models.Model):
    user= models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    class Meta:
        db_table = 'carts'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    class Meta:
        db_table = 'cart_items'


class Currency(models.Model):
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=5)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'currencies'


  