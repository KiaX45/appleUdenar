from django.db import models
from cloudinary.models import CloudinaryField

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = CloudinaryField('image', folder='products/')  # Reemplazamos image_url por este campo
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'products'