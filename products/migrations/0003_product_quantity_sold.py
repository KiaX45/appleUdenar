# Generated by Django 5.1.2 on 2024-11-03 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_cart_cartitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='quantity_sold',
            field=models.IntegerField(default=0),
        ),
    ]