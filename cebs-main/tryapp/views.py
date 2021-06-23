from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.urls import *
from .models import Account, Product
from django.contrib import messages
from django.shortcuts import (get_object_or_404, render, HttpResponseRedirect)
from django.views import View
from django.contrib.auth.decorators import login_required
from .forms import *
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from .cart import Cart
from django.views.decorators.http import require_POST
from .forms import CartAddProductForm
import stripe

# Create your views here.


def main(request):
    return render(request, 'tryapp/user/frontpage.html')


def signup(request):
    context = {}
    if request.user.is_authenticated:
        return redirect('home/')
    else:
        if request.method == 'POST':
            if request.POST.get('username') and request.POST.get('email') and request.POST.get('password1'):
                form = RegistrationForm(request.POST)
                if form.is_valid():
                    form.save()
                    email = form.cleaned_data.get('email')
                    raw_password = form.cleaned_data.get('password1')
                    account = authenticate(email=email, password=raw_password)
                    login(request, account)
                    return redirect('login/')
                else:
                    context['registration_form'] = form
        else:
            form = RegistrationForm()
            context['registration_form'] = form
        return render(request, 'tryapp/user/signup.html', context)


def logout_view(request):
    logout(request)
    return redirect('main/')


def loginview(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect('home/')

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            is_superuser = request.POST.get('is_superuser')
            user = authenticate(email=email, password=password,
                                is_superuser=is_superuser)

            if user:
                if user.is_superuser == True:
                    login(request, user)
                    return redirect('viewproduct/')
                else:
                    login(request, user)
                    return redirect('home/')
        else:
            messages.info(request, 'Username or password is incorrect')
    else:
        form = AccountAuthenticationForm()
    context['login_form'] = form
    return render(request, 'tryapp/user/login.html', context)


def products(request):
    productss = Product.objects.all()
    return render(request, 'tryapp/user/homepage.html', {'productss': productss})


def clothes(request):
    productss = Product.objects.filter(category='CLOTHES')
    return render(request, 'tryapp/user/homepage.html', {'productss': productss})


def electronics(request):
    productss = Product.objects.filter(category='ELECTRONICS')
    return render(request, 'tryapp/user/homepage.html', {'productss': productss})


def books(request):
    productss = Product.objects.filter(category='BOOKS')
    return render(request, 'tryapp/user/homepage.html', {'productss': productss})


def shoes(request):
    productss = Product.objects.filter(category='SHOES')
    return render(request, 'tryapp/user/homepage.html', {'productss': productss})


@login_required(login_url='login')
def contact(request):
    return render(request, 'tryapp/user/contact.html')


@login_required(login_url='login')
def orderhistory(request):
    orderss = Order.objects.filter(
        username=Account.objects.get(id=request.user.id).username)
    return render(request, 'tryapp/user/orderhistory.html', {'orderss': orderss})


def shipping(request, id):
    context = {}
    if request.method == 'POST':
        if request.POST.get('address') and request.POST.get('phone') and request.POST.get('quantity'):
            form = orderForm(request.POST)
            if form.is_valid():
                order = Order()
                product1 = Product.objects.get(id=id)
                quan = form.cleaned_data['quantity']
                pri = product1.price*quan
                stripe.api_key = settings.STRIPE_PRIVATE_KEY
                try:
                    charge = stripe.Charge.create(
                        amount=int(pri) * 100,
                        currency='INR',
                        description='Cebs Product',
                        source='tok_visa'
                    )
                    order = Order()
                    product1 = Product.objects.get(id=id)
                    order.productname = product1.productname
                    order.phone = form.cleaned_data['phone']
                    order.address = form.cleaned_data['address']
                    order.quantity = quan
                    order.username = Account.objects.get(
                        id=request.user.id).username
                    order.price = product1.price
                    order.total = pri
                    order.save()
                    return redirect('home')
                except Exception:
                    messages.error(
                        request, 'There was something wrong with the payment')

            else:
                context['order_form'] = form
    else:
        form = orderForm()
    return render(request, 'tryapp/user/shipping.html', {'order_form': form, 'stripe_pub_key': settings.STRIPE_PUBLIC_KEY})


@require_POST
def cart_add(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'], update_quantity=cd['update'])
    return redirect('cart_detail')


def cart_remove(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect('cart_detail')


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'update': True})
    return render(request, 'tryapp/user/usercart.html', {'cart': cart})


def product_list(request):
    products = Product.objects.all()
    context = {
        'products': products
    }
    return render(request, 'tryapp/user/homepage.html', context)


def product_detail(request, id):
    product = Product.objects.get(pk=id)
    cart_product_form = CartAddProductForm()
    context = {
        'product': product,
        'cart_product_form': cart_product_form
    }
    return render(request, 'tryapp/user/view.html', context)


# def CheckOut(request):
#     address = request.POST.get('address')
#     phone = request.POST.get('phone')
#     username = Account.objects.get(id=request.user.id).username
#     form = CartAddProductForm(request.POST)
#     cart = request.session.get('cart')
#     x = list(cart.keys())
#     res = [int(i) for i in x]
#     length_list = len(res)
#     for a in range(length_list):
#         products = Product.getProductById(res[a])
#         for product in products:
#             h = cart.get(str(product.id))
#             qua = h['quantity']
#             total_p = h['price']
#             t = int(float(total_p))
#             tot = t*qua
#             order = Order(username=username,
#                           productname=product.productname,
#                           price=product.price,
#                           address=address,
#                           phone=phone,
#                           quantity=qua,
#                           total=tot,
#                           )
#             order.save()
#     request.session['cart'] = {}
#     return render(request, 'tryapp/user/usercart.html')

def CheckOut(request):
    address = request.POST.get('address')
    phone = request.POST.get('phone')
    username = Account.objects.get(id=request.user.id).username
    form = CartAddProductForm(request.POST)
    cart = request.session.get('cart')
    x = list(cart.keys())
    res = [int(i) for i in x]
    length_list = len(res)
    for a in range(length_list):
        products = Product.getProductById(res[a])
        for product in products:
            h = cart.get(str(product.id))
            qua = h['quantity']
            total_p = h['price']
            t = int(float(total_p))
            tot = t*qua
            stripe.api_key = settings.STRIPE_PRIVATE_KEY
            try:
                charge = stripe.Charge.create(
                        amount=int(tot) * 100,
                        currency='INR',
                        description='Cebs Product',
                        source='tok_visa'
                    )
                order = Order(username=username,
                          productname=product.productname,
                          price=product.price,
                          address=address,
                          phone=phone,
                          quantity=qua,
                          total=tot,
                          )
                order.save()
                redirect('checkout')
            except Exception:
                    messages.error(request, 'There was something wrong with the payment')
    request.session['cart'] = {}
    return render(request, 'tryapp/user/usercart.html')

# Admin Views

@login_required(login_url='login')
def viewproduct(request):
    productss = Product.objects.all()
    return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})


@login_required(login_url='login')
def addproductform(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('viewproduct/')
    else:
        form = ProductForm()
        context = {'form': form}
        return render(request, 'tryapp/admin/productadd.html', context)


@login_required(login_url='login')
def vieworder(request):
    orderss = Order.objects.all()
    user = Account.objects.filter(is_superuser=False)
    if request.method == "POST":

        filter = request.POST['filter']

        if(filter != "allUsers"):
            orderss = Order.objects.all().filter(username=filter)

    if not orderss:
        messages.warning(request, "No Order Found")
    return render(request, 'tryapp/admin/vieworder.html', {'orderss': orderss, 'users': user})


@login_required(login_url='login')
def updateproduct(request, id):
    obj = get_object_or_404(Product, id=id)
    form = ProductForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        productss = Product.objects.all()
        return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})
    context = {'form': form}
    return render(request, "tryapp/admin/updateproduct.html", context)


@login_required(login_url='login')
def deleteproduct(request, id):
    context = {}
    obj = get_object_or_404(Product, id=id)
    if request.method == "POST":
        obj.delete()
        productss = Product.objects.all()
        return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})

    return render(request, "tryapp/admin/deleteproduct.html", context)


@login_required(login_url='login')
def updateprofile_view(request):
    if not request.user.is_authenticated:
        return redirect("login/")
    context = {}

    if request.POST:
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile is updated successfully!')
    else:
        form = UpdateProfileForm(
            initial={
                "email": request.user.email,
                "username": request.user.username,
                "phone_no": request.user.phone_no,
            }
        )
    context['account_form'] = form
    return render(request, 'tryapp/user/profile.html', context)


def allUsers(request):
    if request.user.is_authenticated == False and request.user.is_superuser:
        return redirect('login')

    user = Account.objects.all().filter(is_superuser=False)

    userList = user

    if request.method == "POST":

        filter = request.POST['filter']

        if(filter != "allUsers"):
            userList = Account.objects.all().filter(id=filter)

    if not userList:
        messages.warning(request, "No User Found")

    return HttpResponse(render(request, 'tryapp/admin/viewuser.html', {'users': user, 'userList': userList}))


def orderstatus(request, id):
    if request.method == 'POST':
        orderss = Order.objects.get(id=id)
        orderss.status = True
        orderss.save()
    return redirect('order')


def vclothes(request):
    productss = Product.objects.filter(category='CLOTHES')
    return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})


def velectronics(request):
    productss = Product.objects.filter(category='ELECTRONICS')
    return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})


def vbooks(request):
    productss = Product.objects.filter(category='BOOKS')
    return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})


def vshoes(request):
    productss = Product.objects.filter(category='SHOES')
    return render(request, 'tryapp/admin/viewproduct.html', {'productss': productss})
