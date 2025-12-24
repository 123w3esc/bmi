from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=6,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        null=True,
        blank=True
    )
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    # ✅ City is required
    city = models.CharField(
        max_length=50,
        choices=[
            ('Indore', 'Indore'),
            ('Khargone', 'Khargone'),
            ('Bhopal', 'Bhopal'),
            ('Khandwa', 'Khandwa'),
        ],
        null=True,  
        blank=True   
    )

    # ✅ Health condition fields (optional)
    has_condition = models.BooleanField(default=False)
    condition = models.CharField(
        max_length=50,
        choices=[
            ('Diabetes', 'Diabetes'),
            ('Blood Pressure', 'Blood Pressure'),
        ],
        null=True,
        blank=True
    )
    admin = models.BooleanField(default=False)


    def __str__(self):
        return self.name



class BMIRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bmi_records")
    height = models.FloatField()   
    weight = models.FloatField()   
    bmi = models.FloatField()
    status = models.CharField(max_length=20)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - BMI: {self.bmi} ({self.status})"
# models.py
from django.db import models

# models.py
from django.db import models

# models.py
from django.db import models

class Specialist(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)        # Cardiologist, Nutritionist, etc.
    specialist_type = models.CharField(max_length=50)   # Overweight, Diabetes, Blood Pressure, Underweight, General
    location = models.CharField(max_length=100)         # Khargone, Indore, Bhopal, Khandwa
    availability = models.CharField(max_length=100, default="Mon-Fri 9:00 am - 12:00 pm")

    def __str__(self):
        return f"{self.name} - {self.specialist_type}"