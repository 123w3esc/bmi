from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

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