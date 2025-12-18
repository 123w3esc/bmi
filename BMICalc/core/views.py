from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .models import User, BMIRecord
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
        messages.success(request, 'Registration successful! Please check your email for OTP.')
        return redirect('verify')

    return render(request, 'register.html')

def login(request):
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
            messages.error(request, 'Invalid Email. Please try again.')
            return redirect('login')

        if not check_password(password, user.password) or not user.is_verified:
            messages.error(request, 'Invalid Password. Please try again.')
            return redirect('login')

        request.session['user_id'] = user.id
        request.session['user_name'] = user.name
        messages.success(request, f'Welcome back, {user.name}!')
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
        messages.success(request, 'OTP sent to your email')
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
                messages.success(request, 'OTP verified. You can now change your password.')
                return redirect('changePass')
            else:
                user.is_verified = True
                user.save()
                messages.success(request, 'Account verified successfully! Please log in.')
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

        if len(new_password) < 6 or not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
            messages.error(request, 'Password must be at least 6 characters and contain both letters and numbers.')
            return redirect('changePass')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgetPass')

        user.password = make_password(new_password)
        user.save()

        del request.session['reset_email']
        messages.success(request, 'Password changed successfully. Please log in with your new password.')
        return redirect('login')

    return render(request, 'changePass.html')

def user_home(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please log in first.')
        return redirect('login')
    return render(request, 'user.html')

def logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def calculate_bmi(request):
    if request.method == 'POST':
        try:
            height = float(request.POST.get('height'))
            weight = float(request.POST.get('weight'))

            if height < 55 or height > 272:
                messages.error(request, "Please enter valid height.")
                return redirect('calculate_bmi')
            if weight < 25 or weight > 150:
                messages.error(request, "Please enter valid weight.")
                return redirect('calculate_bmi')

            bmi = round(weight / ((height / 100) ** 2), 2)

            if bmi < 18.5:
                status = "Underweight"
            elif 18.5 <= bmi < 24.9:
                status = "Normal"
            elif 25 <= bmi < 29.9:
                status = "Overweight"
            else:
                status = "Obese"

            if 'user_id' in request.session:
                user = User.objects.get(id=request.session['user_id'])
                BMIRecord.objects.create(
                    user=user,
                    height=height,
                    weight=weight,
                    bmi=bmi,
                    status=status
                )

            messages.success(request, f'Your BMI was calculated successfully: {bmi} ({status}).')
            return render(request, 'calculate_bmi.html', {
                'bmi': bmi,
                'status': status,
                'height': height,
                'weight': weight
            })
        except ValueError:
            messages.error(request, "Invalid input. Please enter numbers only.")
            return redirect('calculate_bmi')

    return render(request, 'calculate_bmi.html')

def track_progress(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])
    records = user.bmi_records.order_by('created_at')
    
    return render(request, 'track_progress.html', {'records': records})
def diet_plan(request, status):
    return render(request, 'diet.html', {'status': status})

def workout_plan(request, status):
    return render(request, 'workout.html', {'status': status})