from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect,get_object_or_404
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib import messages
from .models import User, BMIRecord, Specialist
import random
# ---------------- HOME  AND ABOUT----------------
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')




# ---------------- REGISTER ----------------
def register(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        email = request.POST.get('email')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        city = request.POST.get('city')  # ✅ new
        has_condition = request.POST.get('has_condition')  # "Yes" or "No"
        condition = request.POST.get('condition') if has_condition == 'Yes' else None
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Age validation
        try:
            age = int(age)
        except (TypeError, ValueError):
            messages.error(request, 'Please enter a valid age.')
            return redirect('register')
        if age < 15 or age > 100:
            messages.error(request, 'Age must be between 15 and 100 years.')
            return redirect('register')

        # Gender required
        if not gender:
            messages.error(request, 'Please select your gender.')
            return redirect('register')

        # City required
        if not city:
            messages.error(request, 'Please select your city.')
            return redirect('register')

        # Confirm password
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        # Email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return redirect('register')

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Send OTP
        try:
            send_mail(
                subject='Your OTP Code for BMI Calculator',
                message=f'Hello {name},\n\nYour OTP code is: {otp}',
                from_email='your_email@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            messages.error(request, f"Could not send OTP email. Please try again later. ({e})")
            return redirect('register')

        # Save user
        user = User(
            name=name,
            email=email,
            password=make_password(password),
            age=age,
            gender=gender,
            city=city,  # ✅ required
            has_condition=(has_condition == 'Yes'),  # ✅ optional toggle
            condition=condition,  # ✅ optional
            otp_code=otp,
            is_verified=False
        )
        user.save()

        # Store email in session
        request.session['email'] = email
        messages.success(request, 'Registration successful! Please check your email for OTP.')
        return redirect('verify')

    return render(request, 'register.html')





# ---------------- LOGIN ----------------


def login(request):
    # Clear any previous session
    request.session.pop('user_name', None)
    request.session.pop('user_id', None)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid Email. Please try again.')
            return redirect('login')

        if not check_password(password, user.password):
            messages.error(request, 'Invalid Password. Please try again.')
            return redirect('login')

        if not user.is_verified:
            messages.error(request, 'Account not verified. Please check your email for OTP.')
            return redirect('login')

        # ✅ Save session
        request.session['user_id'] = user.id
        request.session['user_name'] = user.name
        messages.success(request, f'Welcome back, {user.name}!')

        # ✅ Redirect based on admin flag
        if user.admin:   # if admin column is True (1)
            return redirect('admin_home')   # goes to admin.html
        else:
            return redirect('user')    # goes to user.html

    return render(request, 'login.html')




# ---------------- FORGET PASSWORD ----------------
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

        try:
            send_mail(
                subject='Password Reset OTP - BMI Calculator',
                message=f'Hello,\n\nYour OTP for password reset is: {otp}',
                from_email='your_email@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            messages.error(request, f"Could not send OTP email. Please try again later. ({e})")
            return redirect('forgetPass')

        request.session['reset_email'] = email
        messages.success(request, 'OTP sent to your email.')
        return redirect('verify')

    return render(request, 'forget.html')





# ---------------- VERIFY OTP ----------------
def verify(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')

        if 'reset_email' in request.session:   # check reset first
            email = request.session['reset_email']
            flow = 'reset'
        elif 'email' in request.session:
            email = request.session['email']
            flow = 'register'
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
            if flow == 'reset':
                user.save()
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





# ---------------- CHANGE PASSWORD ----------------
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





# ---------------- USER HOME ----------------
def user_home(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please log in first.')
        return redirect('login')
    return render(request, 'user.html')




# ----------------LOGOUT USER HOME ----------------
def logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')




# ---------------- BMI CALCULATOR ----------------
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

            user_condition = None
            if 'user_id' in request.session:
                user = User.objects.get(id=request.session['user_id'])
                BMIRecord.objects.create(
                    user=user,
                    height=height,
                    weight=weight,
                    bmi=bmi,
                    status=status
                )
                # ✅ capture condition from user model
                user_condition = user.condition  

            messages.success(request, f'Your BMI was calculated successfully: {bmi} ({status}).')
            return render(request, 'calculate_bmi.html', {
                'bmi': bmi,
                'status': status,
                'height': height,
                'weight': weight,
                'condition': user_condition  # ✅ pass condition to template
            })
        except ValueError:
            messages.error(request, "Invalid input. Please enter numbers only.")
            return redirect('calculate_bmi')

    return render(request, 'calculate_bmi.html')




# ---------------- TRACK PROGRESS ----------------
def track_progress(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])
    records = user.bmi_records.order_by('created_at')
    return render(request, 'track_progress.html', {'records': records})




def diet_plan(request, status):
    return render(request, 'diet.html', {'status': status})

def diet_diabetes(request, status):
    
    return render(request, 'diet_diabetes.html', {'status': status})

def diet_bp(request, status):
    
    return render(request, 'diet_bp.html', {'status': status})


def workout_plan(request, status):
    return render(request, 'workout.html', {'status': status})



def admin_home(request):
    return render(request, 'admin.html')


def manage_users(request):
    users = User.objects.all()
    return render(request, 'manage_user.html', {'users': users})


def verify_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_verified = True
    user.save()
    messages.success(request, f'User {user.name} has been verified.')
    return redirect('manage_users')


def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f'User {user.name} has been deleted.')
    return redirect('manage_users')




def make_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.admin = True
    user.save()
    messages.success(request, f'User {user.name} is now an Admin.')
    return redirect('manage_users')







def specialist_bot(request):
    # Session auth
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Clear bad session and force login
        request.session.pop('user_id', None)
        request.session.pop('user_name', None)
        return redirect('login')

    # Latest BMI record (optional)
    bmi_record = BMIRecord.objects.filter(user=user).order_by('-created_at').first()
    bmi_status = (bmi_record.status if bmi_record and getattr(bmi_record, 'status', None) else None)

    # Normalize user fields (avoid None in template/JS)
    user_city = (user.city or "").strip()
    user_condition = (user.condition if getattr(user, 'has_condition', False) else None)

   
    specialists = Specialist.objects.all()

  
    context = {
        "specialists": specialists,
        "bmi_status": bmi_status,   # optional: can be shown in intro
        "condition": user_condition,
        "city": user_city,
    }
    return render(request, "bot.html", context)


# ---------------- DOWNLOAD PDF REPORT ----------------


# views.py (Update imports if needed)
# views.py
import io
from django.shortcuts import render, redirect
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import User, BMIRecord, Specialist

def download_report(request):
    # 1. Check Login
    if 'user_id' not in request.session:
        return redirect('login')

    # 2. Setup PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # --- Custom Styles (Compact for single page feel) ---
    style_header = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=10, textColor=colors.navy)
    style_sub = ParagraphStyle('Sub', parent=styles['Heading3'], fontSize=12, spaceBefore=10, spaceAfter=5, textColor=colors.darkgreen)
    style_cell_head = ParagraphStyle('CellHead', parent=styles['BodyText'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)
    style_cell = ParagraphStyle('Cell', parent=styles['BodyText'], fontSize=9, leading=10)

    # 3. Fetch Data
    user = User.objects.get(id=request.session['user_id'])
    last_record = BMIRecord.objects.filter(user=user).order_by('-created_at').first()

    if not last_record:
        return redirect('calculate_bmi')

    status = last_record.status
    condition = user.condition if user.has_condition else "None"
    city = user.city

    # ==========================================
    # 4. DATA LOGIC (All in one place)
    # ==========================================

    diet_data = []
    workout_data = []
    schedule_data = []
    specialist_query = condition if condition != "None" else status

    # --- A. DIABETES LOGIC ---
    if condition == "Diabetes":
        # Diet
        diet_data = [
            ["Multigrain Paratha", "Protein: 12g | 320 kcal", "2 Parathas"],
            ["Almond Milk (Sugar Free)", "Protein: 8g | 250 kcal", "1 Glass"],
            ["Chicken Stew / Soya", "Protein: 25g | 300 kcal", "1 Bowl"],
            ["Bitter Gourd (Karela)", "Cal: 120 kcal", "1 Bowl"],
            ["Brown Rice Khichdi", "Protein: 10g | 300 kcal", "1 Plate"],
        ]
        # Workout (Low Impact)
        workout_data = [
            ["Brisk Walking", "30 Mins", "Daily Sugar Control"],
            ["Light Weights", "3 Sets x 12 Reps", "Muscle uptake"],
            ["Yoga (Pranayama)", "15 Mins", "Stress Reduction"],
        ]
        # Schedule
        schedule_data = [
            ["07:00 AM", "Methi Water"], ["09:00 AM", "Breakfast"],
            ["11:30 AM", "Veg Juice"], ["01:30 PM", "Lunch"],
            ["05:00 PM", "Tea (No Sugar)"], ["08:00 PM", "Light Dinner"]
        ]

    # --- B. BLOOD PRESSURE LOGIC ---
    elif condition == "Blood Pressure":
        # Diet (DASH)
        diet_data = [
            ["Banana Oats Smoothie", "High Potassium", "1 Glass"],
            ["Grilled Fish / Tofu", "Omega-3 Rich", "150g"],
            ["Spinach (Palak) Dal", "Magnesium Rich", "1 Bowl"],
            ["Unsalted Nuts", "Healthy Fats", "Handful"],
            ["Curd Rice", "Probiotic", "1 Bowl"],
        ]
        # Workout (Cardio Focus)
        workout_data = [
            ["Walking / Cycling", "30 Mins", "Lower BP"],
            ["Swimming", "20 Mins", "Zero Joint Impact"],
            ["Breathing Exercises", "10 Mins", "Calms Nervous System"],
        ]
        # Schedule
        schedule_data = [
            ["07:00 AM", "Lemon Water"], ["07:30 AM", "Morning Walk"],
            ["09:00 AM", "Low Salt Breakfast"], ["01:00 PM", "Lunch"],
            ["06:00 PM", "Yoga"], ["08:00 PM", "Soup Dinner"]
        ]

    # --- C. STANDARD BMI LOGIC ---
    else:
        if status == "Underweight":
            diet_data = [
                ["Banana Shake", "High Calorie", "1 Large Glass"],
                ["Ghee Roti + Dal", "Calorie Dense", "3 Rotis"],
                ["Eggs / Paneer", "High Protein", "3 Units"],
                ["Dry Fruits", "Healthy Fats", "100g"],
                ["Peanut Butter", "Energy Dense", "2 Spoons"],
            ]
            workout_data = [
                ["Push Ups", "3 Sets x 12 Reps", "Upper Body"],
                ["Squats", "3 Sets x 15 Reps", "Legs"],
                ["Lunges", "3 Sets x 12 Reps", "Glutes"],
            ]
            schedule_data = [
                ["07:00 AM", "Heavy Breakfast"], ["10:00 AM", "Snack"],
                ["01:00 PM", "Heavy Lunch"], ["04:00 PM", "Shake"],
                ["08:00 PM", "Dinner"], ["10:00 PM", "Milk"]
            ]

        elif status == "Normal":
            diet_data = [
                ["Oats / Dalia", "Fiber Rich", "1 Bowl"],
                ["Grilled Chicken/Veg", "Balanced Protein", "150g"],
                ["Seasonal Fruit", "Vitamins", "1 Bowl"],
                ["Dal Rice", "Carbs + Protein", "1 Plate"],
            ]
            workout_data = [
                ["Running", "20 Mins", "Cardio"],
                ["Push Ups", "3 Sets x 15 Reps", "Strength"],
                ["Plank", "3 Sets (1 Min)", "Core"],
            ]
            schedule_data = [
                ["07:30 AM", "Breakfast"], ["12:30 PM", "Lunch"],
                ["05:00 PM", "Snack"], ["06:30 PM", "Workout"],
                ["08:30 PM", "Dinner"]
            ]

        elif status == "Overweight" or status == "Obese":
            diet_data = [
                ["Green Salad", "Fiber / Filling", "Large Bowl"],
                ["Clear Soup", "Low Calorie", "1 Bowl"],
                ["Grilled Protein", "High Satiety", "150g"],
                ["Buttermilk", "Probiotic", "1 Glass"],
                ["Papaya", "Digestion", "1 Bowl"],
            ]
            workout_data = [
                ["HIIT / Fast Walk", "30 Mins", "Fat Burn"],
                ["Burpees / Jacks", "3 Sets x 15", "Calorie Burn"],
                ["Bodyweight Squats", "3 Sets x 20", "Legs"],
            ]
            schedule_data = [
                ["07:00 AM", "Warm Water"], ["08:00 AM", "Light Breakfast"],
                ["01:00 PM", "Salad Lunch"], ["05:00 PM", "Green Tea"],
                ["07:30 PM", "Soup Dinner"]
            ]

    # --- 5. SPECIALIST FETCH ---
    if specialist_query == "Normal": specialist_query = "General"
    
    specialist = Specialist.objects.filter(
        location=city, 
        specialist_type__icontains=specialist_query
    ).first()

    # ==========================================
    # 6. BUILD PDF LAYOUT
    # ==========================================

    # Header
    elements.append(Paragraph("BMI & HEALTH INSTRUCTOR REPORT", style_header))
    
    # --- SECTION A: USER PROFILE ---
    elements.append(Paragraph(f"User Profile: {user.name}", style_sub))
    prof_data = [
        ["Age / Gender:", f"{user.age} / {user.gender}", "Condition:", condition],
        ["Current BMI:", f"{last_record.bmi}", "Status:", status],
        ["City:", city, "Date:", last_record.created_at.strftime('%Y-%m-%d')]
    ]
    t_prof = Table(prof_data, colWidths=[80, 120, 80, 120])
    t_prof.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.aliceblue),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_prof)
    elements.append(Spacer(1, 10))

    # --- SECTION B: DIET & SCHEDULE (Side by Side if possible, but stacked for safety) ---
    
    # 1. DIET TABLE
    elements.append(Paragraph("1. Recommended Diet Plan", style_sub))
    d_table = [['Food Item', 'Nutrition', 'Qty']] # Header
    for d in diet_data: d_table.append(d) # Rows

    t_diet = Table(d_table, colWidths=[150, 150, 100])
    t_diet.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkorange),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_diet)
    elements.append(Spacer(1, 10))

    # 2. WORKOUT TABLE
    elements.append(Paragraph("2. Workout Routine", style_sub))
    w_table = [['Exercise', 'Duration / Sets', 'Benefit']] # Header
    for w in workout_data: w_table.append(w)

    t_work = Table(w_table, colWidths=[150, 120, 130])
    t_work.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.teal),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_work)
    elements.append(Spacer(1, 10))

    # 3. SCHEDULE TABLE
    elements.append(Paragraph("3. Daily Schedule", style_sub))
    s_table = [['Time', 'Activity']]
    for s in schedule_data: s_table.append(s)
    
    t_sched = Table(s_table, colWidths=[100, 300])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_sched)
    elements.append(Spacer(1, 10))

    # 4. SPECIALIST INFO
    elements.append(Paragraph("4. Recommended Specialist", style_sub))
    if specialist:
        spec_data = [
            ["Doctor:", specialist.name],
            ["Specialty:", f"{specialist.specialty} ({specialist.specialist_type})"],
            ["Location:", specialist.location],
            ["Timing:", specialist.availability]
        ]
        t_spec = Table(spec_data, colWidths=[100, 300])
        t_spec.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        elements.append(t_spec)
    else:
        elements.append(Paragraph(f"No specific specialist found in {city}.", styles['BodyText']))

    # Build
    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'Full_Health_Report_{user.name}.pdf')


def privacy_policy(request):
    """Renders the Privacy Policy page."""
    return render(request, 'privacy.html')

def terms_of_service(request):
    """Renders the Terms & Disclaimer page."""
    return render(request, 'terms.html')