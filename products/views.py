from django.shortcuts import render, get_object_or_404
from django import forms
from products.models import Product, Currency
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging
from cloudinary.forms import CloudinaryFileField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from decimal import Decimal
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import pandas as pd
from .forms import ProductForm
import requests
import math

#imports for paypal
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid # unique user id for duplicate transactions

# Create your views here.


def home(request):
    #obtenemos la moneda activa
    currency = Currency.objects.get(active=True)
    #obtenemos todos los productos
    products = Product.objects.all()
    
    print(currency.symbol)

    #si la moneda activa es diferente a USD convertimos los precios
    formatted = ''
    conversion_rate = get_conversion_rate(currency.symbol)
    for product in products:
        product.price = product.price * Decimal(conversion_rate)
        product.price = round(product.price, 2)
        formatted = formatted_price(product.price, currency.symbol)
        product.price_formatted = formatted
        #Product.objects.filter(id=product.id).update(price_formatted=product.price_formatted)

    



    form = MiFormulario()
    return render(request, 'products/home.html', context={'products': products, 'form': form})


def formatted_price(price, currency):
    price = str(price)
    contador = -1
    descarte = 0
    longitud = len(price)
    comenzar = not("." in price)
    for index in range(longitud):

        if price[-index] == '.':
            comenzar = True

        if comenzar:
           contador+=1
           if contador % 3 == 0 and contador != 0: 
                price = price[:longitud-descarte-contador] + ',' + price[longitud-descarte-contador:]
                
        else:
            descarte+=1    
         
            
    return f'{currency} {price}'


def get_conversion_rate(currency):
    url = 'https://v6.exchangerate-api.com/v6/6c87ed7edfc7c8fbe170f45a/latest/USD'
    # Making our request
    response = requests.get(url)
    data = response.json()
    #print(data)
    # Getting the conversion rate
    convertion_rate = data['conversion_rates'][currency]
    return convertion_rate


# Configurar logging
logger = logging.getLogger(__name__)

class MiFormulario(forms.ModelForm):
    # Sobreescribir el campo de imagen para usar CloudinaryFileField
    image = CloudinaryFileField(
        options = {
            'folder': 'productos',  # Carpeta en Cloudinary
            'allowed_formats': ['jpg', 'png'],
            'transformation': [
                {'width': 500, 'height': 500, 'crop': 'limit'}  # tamaño máximo
            ]
        },
        required=False  
    )

    class Meta:
        model = Product
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control mb-2'
            })



def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                product = form.save()
                # Podemos redirigir a la lista de productos o a la página del producto creado
                return JsonResponse({
                    'status': 'success',
                    'message': '¡Producto creado exitosamente!',
                    'redirect_url': '/'  # Cambia esto a tu URL deseada
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Por favor, verifica los datos del formulario',
                    'errors': dict(form.errors.items())
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    else:
        form = ProductForm()
    
    return render(request, 'products/create_product.html', {'form': form})

@login_required
@require_POST
def delete_product(request, pk):
    try:
        product = get_object_or_404(Product, id=pk)
        
        # Verificar si el usuario tiene permisos
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
        
        product.delete()
        return JsonResponse({'success': True, 'message': 'Producto eliminado exitosamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    

@login_required
@require_POST
def update_product(request, pk):
    try:
        # Verificar permisos de staff
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
        
        # Obtener el producto
        product = get_object_or_404(Product, id=pk)
        
        # Validar datos
        try:
            price = Decimal(request.POST.get('price', '0'))
            stock = int(request.POST.get('stock', '0'))
            quantity_sold = int(request.POST.get('quantity_sold', '0'))
            if price < 0 or stock < 0 or quantity_sold < 0:
                raise ValueError("El precio y el stock no pueden ser negativos")
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        
        # Actualizar campos básicos
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = price
        product.stock = stock
        product.quantity_sold = quantity_sold
        
        # Manejar la imagen si se proporciona una nueva
        if request.FILES.get('image'):
            # Si hay una imagen existente, Cloudinary la reemplazará automáticamente
            # gracias al campo CloudinaryField
            product.image = request.FILES['image']
        
        product.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Producto actualizado exitosamente'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error al actualizar el producto: {str(e)}'
        }, status=500)
    


#view para crear elementos del carro de compras y tambien para crear el carro si el usuario no tiene uno

from .models import Cart, CartItem
from products.models import Product
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F

@login_required
@require_POST
@transaction.atomic  # Ensures database consistency
def add_to_cart(request, product_id):
    try:
        # intentamos obtener el producto
        product = get_object_or_404(Product, id=product_id)
        
        # Gcreamos un carro si el usuario no tiene uno
        cart, _ = Cart.objects.get_or_create( # usamos _ para ignorar el booleano que retorna
            user=request.user,
            defaults={'created_at': timezone.now()}
        )
        
        # crearmos el carro o incrementamos la cantidad si ya existe
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            # compronamos si el producto ya esta en el carro
            #utilizamos F para evitar problemas de concurrencia
            cart_item.quantity = F('quantity') + 1
            cart_item.save()
        
        # Get the updated cart information
        cart_count = CartItem.objects.filter(cart=cart).count()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Product added to cart successfully',
            'cart_count': cart_count,
            'cart_item_id': cart_item.id
        })
        
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }, status=500)

#funcion para extrare los elementos del carro de compras del usuario
@login_required
def get_cart_items(request):
    
    found_products = False
    try:
        cart = Cart.objects.get(user = request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        found_products = True
    #ponemos una exepción para ambos casos cuando no existe el carro o no hay elementos en el carro
    except Cart.DoesNotExist:
        found_products = False

    #variables paypal    
    host = request.get_host()
    total_amount = 0

    products = []

    if found_products:
        for cart_item in cart_items:
            total_amount += cart_item.product.price * cart_item.quantity
            products.append({
                'id': cart_item.id,
                'name': cart_item.product.name,
                'price': cart_item.product.price,
                'quantity': cart_item.quantity,
                'total': cart_item.product.price * cart_item.quantity,
                'stock': cart_item.product.stock,
                'image': cart_item.product.image.url,    
            })

    if len(products) == 0:
        found_products = False


    paypal_form = paypal_payment(total_amount, host,  request)


    return render(request, 'products/cart.html', {'products':products, 'found_products': found_products, 'paypal_form': paypal_form})
    
#función para poder obtener el formulario de paypal
def paypal_payment(quantity, host, request):
   #create paypal dictioanry
   paypal_dict = {
         'business': settings.PAYPAL_RECEIVER_EMAIL,
         #'amount': quantity,
         'amount': 10, #temporalmente para pruebas
         'item_name': 'Item_Name_xyz',
         'no_shipping': 2,
         'invoice': str(uuid.uuid4()), # unique invoice id
         'currency_code': 'USD',
         'notify_url': f'http://{host}{reverse("products:paypal-ipn")}',
         "return": request.build_absolute_uri(reverse('products:payment_success')),
         "cancel_return": request.build_absolute_uri(reverse('products:cart')),
         #'return_url': 'http://{}{}'.format(host, reverse('products:payment_success')),
         #'cancel_return': 'http://{}{}'.format(host, reverse('products:payment_success')),
         'custom': 'Este es el campo custom',
    }
   
   #create paypal form
   paypal_form = PayPalPaymentsForm(initial=paypal_dict)
   return paypal_form
    


def delete_cart_item(request, cart_item_id):
    try:
        cart_item = get_object_or_404(CartItem, pk=cart_item_id)
    except CartItem.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Cart item not found'
        }, status=404)
    
    cart_item.delete()
    return JsonResponse({
        'status': 'success',
        'message': 'Cart item deleted successfully'
    })



@login_required
def dashboard(request):


    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10]
    })

    fig = px.line(df, x='x', y='y', title='Sample Plot')

    # convertimos la figura a JSON
    plot_json = json.dumps(fig, cls=PlotlyJSONEncoder)

    return render(request, 'products/dashboard.html', {'plot': plot_json})



@login_required
def edit_cart_item(request, cart_item_id):

    stock = int(request.POST.get('stockInput'))
    try:
        cart_item = get_object_or_404(CartItem, pk=cart_item_id)
        quantity = int(request.POST.get('quantity_sold'))
        print(quantity)
        #validamos los datos si es menor a 1 
        if quantity < 1:
            raise ValueError('Quantity must be greater than 0')
        
        if quantity > stock:
            raise ValueError('Quantity must be less than or equal to stock')
        
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': str(e)
        }, status=500)
    
    cart_item.quantity = quantity
    print(cart_item.quantity)
    cart_item.save()
    return JsonResponse({
            'status': True,
            'message': 'Cart item updated successfully'
        })


@login_required
def checkout(request):
    try:
        send_email(request) #enviamos el correo
        #obtenemos el carro del usuario 
        cart = Cart.objects.get(user=request.user)
        #obtenemos los items del carro
        cart_items = CartItem.objects.filter(cart=cart)
        #recorremos los items del carro y actualizamos el stock y la cantidad vendida
        for cart_item in cart_items:
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.quantity_sold += cart_item.quantity
            product.save()
            cart_item.delete()
    except:
        return JsonResponse({
            'status': False,
            'message': 'An unexpected error occurred'
        }, status=500)
    
    return JsonResponse({
        'status': True,
        'message': 'La compra se realizó exitosamente'
    })

#view de la pagina de succes 
def payment_success(request):
    return render(request, 'products/payment_succes.html')



def currency_change(request, currency):
    # Cambiar la moneda activa
    try:
        # Desactivar la moneda actual
        Currency.objects.filter(active=True).update(active=False)
        
        # Activar la nueva moneda
        Currency.objects.filter(symbol=currency).update(active=True)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': True, 'message': 'Currency changed successfully'})

from django.http import HttpResponse
from django.template.loader import render_to_string

#funciones para email
from django.core.mail import send_mail, EmailMultiAlternatives
def send_email(request):
    currency = Currency.objects.get(active=True)
    #obtenemos el carro del usuario
    cart = Cart.objects.get(user=request.user)
    #obtenemos los items del carro
    cart_items = CartItem.objects.filter(cart=cart)
    #recorremos los items del carro y actualizamos el stock y la cantidad vendida
    products = []
    total = 0
    for cart_item in cart_items:
        product = cart_item.product
        nombre = product.name
        pagado = product.price * cart_item.quantity
        total += pagado
        pagado = formatted_price(pagado, currency.symbol)
        quantity = cart_item.quantity   
        img = product.image.url
        products.append({'name': nombre, 'pagado': pagado, 'quantity': quantity, 'img': img})

    #print(products)
    total = formatted_price(total, currency.symbol)
    test_email(request.user.email, request.user.username, products, total)
    return HttpResponse('Email sent successfully')


def test_email(email, name, products,  total):
        
    html_content = render_to_string('products/correo.html', {
    'name': name,  # Variables de contexto
    'link': 'https://www.ejemplo.com',
    'products': products,
    'total': total
    })

    email = EmailMultiAlternatives( 
        subject='Confirmación de compra',
        body='Este es el texto alternativo.',  # Texto en caso de que no soporte HTML
        from_email='appleudenar@gmail.com',
        to=[email],
        )
    
    email.attach_alternative(html_content, "text/html")

    email.send()

    return HttpResponse('Email sent successfully')