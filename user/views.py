from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm
from django.contrib.auth import authenticate, login
from sale.utils import process_order

def login_page(request):
   form = LoginForm(request.POST or None)
   error = None
   
   if request.method == "POST" and form.is_valid():
      phone = form.cleaned_data['phone']
      print(phone)
      password = form.cleaned_data['password']
      user = authenticate(request, username=phone, password=password)
      if user is not None:
         login(request, user)
         request.user = user
         pending_order = request.session.pop('pending_order', None)
         if pending_order:
            return process_order(request, pending_order)
         next_url = request.POST.get('next') or '/'
         return redirect(next_url)
      else:
         error = "Téléphone ou mot de passe invalide"

   return render(request, 'user/login.html', {"form": form, 'error': error})


def register(request):
   if request.method == "POST":
      form = RegisterForm(request.POST)
      if form.is_valid():
         pass
   else:
      form = RegisterForm()

   return render(request, "user/register.html", {"form": form})