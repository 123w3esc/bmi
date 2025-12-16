from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .models import User
import random

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def register(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return redirect('register')

        otp = str(random.randint(100000, 999999))
        user = User(
            name=name,
            email=email,
            password=make_password(password),
            otp_code=otp,
            is_verified=False
        )
        user.save()

        send_mail(
            subject='Your OTP Code for BMI Calculator',
            message=f'Hello {name},\n\nYour OTP code is: {otp}',
            from_email='your_email@gmail.com',
            recipient_list=[email],
            fail_silently=False,
        )

        request.session['email'] = email
        return redirect('verify')

    return render(request, 'register.html')

def login(request):
    # Clear session data to avoid stale popups
    request.session.pop('user_name', None)
    request.session.pop('user_id', None)
    request.session.pop('email', None)
    request.session.pop('reset_email', None)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid login credentials. Please try again.')
            return redirect('login')

        if not check_password(password, user.password) or not user.is_verified:
            messages.error(request, 'Invalid login credentials. Please try again.')
            return redirect('login')

        request.session['user_id'] = user.id
        request.session['user_name'] = user.name
        return redirect('user')

    return render(request, 'login.html')

def forget(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Email not found.')
            return redirect('forgetPass')

        otp = str(random.randint(100000, 999999))
        user.otp_code = otp
        user.save()

        send_mail(
            subject='Password Reset OTP - BMI Calculator',
            message=f'Hello,\n\nYour OTP for password reset is: {otp}',
            from_email='your_email@gmail.com',
            recipient_list=[email],
            fail_silently=False,
        )

        request.session['reset_email'] = email
        return redirect('verify')

    return render(request, 'forget.html')

def verify(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')

        if 'email' in request.session:
            email = request.session['email']
            flow = 'register'
        elif 'reset_email' in request.session:
            email = request.session['reset_email']
            flow = 'reset'
        else:
            messages.error(request, 'Session expired. Please start again.')
            return redirect('register')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('register')

        if user.otp_code == otp:
            user.otp_code = None
            user.save()

            if flow == 'reset':
                return redirect('changePass')
            else:
                user.is_verified = True
                user.save()
                return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('verify')

    return render(request, 'verify.html')

def changePass(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        email = request.session.get('reset_email')

        if not email:
            messages.error(request, 'Session expired. Please start again.')
            return redirect('forgetPass')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('changePass')

        if len(new_password) < 8 or not any(c.isalpha() for c in new_password):
            messages.error(request, 'Password must be at least 8 characters and contain letters.')
            return redirect('changePass')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgetPass')

        user.password = make_password(new_password)
        user.save()

        del request.session['reset_email']
        return redirect('login')

    return render(request, 'changePass.html')

def user_home(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please log in first.')
        return redirect('login')
    return render(request, 'user.html')

def logout(request):
    request.session.flush()
    return redirect('login')