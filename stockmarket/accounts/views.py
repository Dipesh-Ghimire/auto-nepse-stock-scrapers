from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserRegisterForm

@login_required
def normal_user_view(request):
    if request.user.is_normal_user:
        # Logic for normal user dashboard
        return redirect('company_list')  
    else:
        # Redirect or deny access if not a normal user
        return redirect(admin_view)  # or return an error page

@user_passes_test(lambda u: u.is_authenticated and u.is_admin_user)
def admin_view(request):
    # Logic for admin dashboard
    return render(request, 'accounts/admin_dashboard.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Optionally force user type if you don’t want users to choose
            user.is_normal_user = True
            user.is_admin_user = False
            user.save()
            # login(request, user)
            return redirect('login')
    else:
        form = CustomUserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def custom_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')  # or redirect to desired page after login
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')

# accounts/views.py
from django.contrib.auth import logout

def custom_logout(request):
    logout(request)
    return redirect('/accounts/login/')  # redirect after logout
