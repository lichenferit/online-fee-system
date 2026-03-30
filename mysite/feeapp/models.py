# feeapp/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string
from decimal import Decimal
from tinymce.models import HTMLField


# ============================================================================
# USER & AUTHENTICATION MODELS
# ============================================================================

class User(AbstractUser):
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'feeapp_user' 
    
    def __str__(self):
        return self.email

class Clerk(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clerk')
    clerk_id = models.CharField(max_length=20, unique=True, null=True, blank=True)  # blank=True added
    clerk_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    cnic = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.clerk_id or self.clerk_id.strip() == '':
            while True:
                new_id = 'CLK' + ''.join(random.choices(string.digits, k=5))
                if not Clerk.objects.filter(clerk_id=new_id).exists():
                    self.clerk_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.clerk_name

# ============================================================================
# ACADEMIC STRUCTURE MODELS
# ============================================================================

class Programs(models.Model):
    heading = models.CharField(max_length=255) 
    short_description = HTMLField()
    image = models.FileField(upload_to="program_images/", max_length=250, null=True, default=None)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Programs"
    
    def __str__(self):
        return self.heading


class CourseGroup(models.Model):
    name = models.CharField(max_length=100)
    short_description = HTMLField()
    program_id = models.ForeignKey(Programs, on_delete=models.CASCADE, default=1)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    created_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Session(models.Model):
    year = models.CharField(max_length=20, default='2024')  

    def __str__(self):
        return self.year


class SchemeOfStudy(models.Model):
    program = models.ForeignKey(Programs, on_delete=models.CASCADE)
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Schemes of Study"

    def __str__(self):
        return f"{self.program.heading} - {self.course_group.name} ({self.session.year})"


class SchemeCourse(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('old', 'Old'),
    )
    scheme = models.ForeignKey(SchemeOfStudy, on_delete=models.CASCADE, related_name='courses')
    semester_year = models.PositiveIntegerField(help_text="1–2 for Intermediate, 1–8 for BS")
    course_code = models.CharField(max_length=50, blank=True, null=True)
    course_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')

    def __str__(self):
        return f"{self.course_code or 'N/A'} - {self.course_name or 'N/A'} (Sem/Yr {self.semester_year})"


# ============================================================================
# LOCATION MODELS
# ============================================================================

class Province(models.Model):
    province = models.CharField(max_length=200)

    def __str__(self):
        return self.province


class District(models.Model):
    district = models.CharField(max_length=200)

    def __str__(self):
        return self.district


# ============================================================================
# STUDENT MODEL
# ============================================================================

class RegisteredStudent(models.Model):
    STATUS_CHOICES = (
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    )
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    RELIGION_CHOICES = [
        ("Islam", "Islam"),
        ("Christian", "Christian"),
        ("Sikh", "Sikh"),
        ("Other", "Other"),
    ]
    MARITAL_STATUS_CHOICES = [
        ("Married", "Married"),
        ("Unmarried", "Unmarried"),
        ("Divorced", "Divorced"),
    ]
    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("O+", "O+"), ("O-", "O-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='morning')
    college_roll_no = models.CharField(max_length=50, blank=True, null=True)
    university_roll_no = models.CharField(max_length=50, blank=True, null=True)
    registration_no = models.CharField(max_length=50, blank=True, null=True)

    name = models.CharField(max_length=255)
    cnic_no = models.CharField(max_length=20, unique=True)
    photo = models.ImageField(upload_to='std_photos/', blank=True, null=True)
    date_of_birth = models.DateField()
    mobile_no = models.CharField(max_length=15)
    email = models.EmailField()

    father_name = models.CharField(max_length=255)
    father_cnic = models.CharField(max_length=20)
    father_mobile_no = models.CharField(max_length=15)
    father_occupation = models.CharField(max_length=255)

    guardian_name = models.CharField(max_length=255, blank=True, null=True)
    guardian_cnic = models.CharField(max_length=20, blank=True, null=True)
    guardian_contact_no = models.CharField(max_length=15, blank=True, null=True)

    permanent_address = models.TextField()
    postal_address = models.TextField()
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    city = models.CharField(max_length=100)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    religion = models.CharField(max_length=50, choices=RELIGION_CHOICES)
    hafiz_e_quran = models.BooleanField(default=False)
    hafiz_doc = models.FileField(upload_to='hafiz_doc/', blank=True, null=True)
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, default='A+')
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    disability_status = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=100, blank=True, null=True)

    related_to_worker = models.BooleanField(default=False)
    worker_name = models.CharField(max_length=255, blank=True, null=True)
    worker_relation = models.CharField(max_length=30, blank=True, null=True)
    worker_payscale = models.CharField(max_length=50, blank=True, null=True)
    worker_status = models.BooleanField(default=False)

   
    scheme_of_study = models.ForeignKey(SchemeOfStudy, on_delete=models.CASCADE, related_name='students')
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.college_roll_no})"


# ============================================================================
# FEE HEAD MODELS
# ============================================================================

class FeeHead(models.Model):
    fee_head_account_id = models.AutoField(primary_key=True)
    fee_head_name = models.CharField(max_length=255)
    fee_head_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.fee_head_name} - Rs.{self.fee_head_amount}"


class FeeHeadProgram(models.Model):
    fee_head = models.ForeignKey(FeeHead, on_delete=models.CASCADE)
    program = models.ForeignKey(Programs, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('fee_head', 'program')
    
    def __str__(self):
        return f"{self.fee_head.fee_head_name} for {self.program.heading}"

class Logo(models.Model):
    college_id = models.AutoField(primary_key=True)
    college_name = models.CharField(max_length=255)
    logo_path = models.CharField(max_length=255, null=True, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    uploaded_by = models.CharField(max_length=255, null=True, blank=True)
    uploaded_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.college_name

# ============================================================================
# CHALLAN MODELS
# ============================================================================

class Challan(models.Model):
    challan_number = models.CharField(max_length=50, primary_key=True)
    due_date = models.DateField(null=True, blank=True)
    challan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='UNPAID')
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PAID', 'Paid'),
            ('UNPAID', 'Unpaid'),
            ('PARTIALLY_PAID', 'Partially Paid'),
        ],
        default='UNPAID'
    )
    
    original_total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    download_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Download'),
            ('DOWNLOADED', 'Downloaded'),
            ('SUSPENDED', 'Suspended'),
            ('NOT_APPLICABLE', 'Not Applicable'),
        ],
        default='NOT_APPLICABLE'
    )
    
    created_by_clerk = models.ForeignKey(Clerk, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_challans')
    challan_generation_date = models.DateField()
    challan_generation_time = models.TimeField(null=True, blank=True) 
    student = models.ForeignKey(RegisteredStudent, on_delete=models.CASCADE)
    html_content = models.TextField(null=True, blank=True)
    challan_file = models.FileField(upload_to='challan_files/', null=True, blank=True)
    disciplines = models.TextField(null=True, blank=True)
    semesters = models.TextField(null=True, blank=True)
    one_bill_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.challan_number} - {self.payment_status}"


class ChallanFeeHead(models.Model):
    fee_head_account = models.ForeignKey(FeeHead, on_delete=models.CASCADE)
    challan = models.ForeignKey(Challan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_of_generation = models.DateField()
    
    class Meta:
        unique_together = ('fee_head_account', 'challan')
    
    def __str__(self):
        return f"{self.fee_head_account.fee_head_name} - {self.challan.challan_number}"


class Installment(models.Model):
    original_challan = models.ForeignKey(Challan, on_delete=models.CASCADE, related_name='installments')
    installment_challan = models.OneToOneField(Challan, on_delete=models.CASCADE, related_name='installment_info')
    installment_number = models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('PAID', 'Paid'), ('UNPAID', 'Unpaid')], default='UNPAID')

    class Meta:
        unique_together = ('original_challan', 'installment_number')
        ordering = ['installment_number']

    def __str__(self):
        return f"Inst#{self.installment_number} - {self.original_challan.challan_number}"


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    challan = models.ForeignKey(Challan, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=[("Bank", "Bank"), ("Online", "Online")])
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Payment {self.payment_id} for Challan #{self.challan.challan_number}"


class ClerkOTP(models.Model):
    clerk = models.ForeignKey(Clerk, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)
    
    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.clerk.clerk_name} - {self.otp_code}"
    
# ============================================================================
# LOGIN HISTORY MODEL
# ============================================================================

class ClerkLoginHistory(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    date        = models.DateField()                             
    login_time  = models.TimeField()
    logout_time = models.TimeField(null=True, blank=True)
    logout_date = models.DateField(null=True, blank=True)       
 
    class Meta:
        ordering = ['-date', '-login_time']
        verbose_name_plural = "Clerk Login Histories"
 
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.login_time}"
 

# ============================================================================
# ACTIVITY HISTORY MODEL
# ============================================================================

class ClerkActivityHistory(models.Model):
    clerk = models.ForeignKey('Clerk', on_delete=models.CASCADE, related_name='activity_history')
    date = models.DateField()
    time = models.TimeField()
    first_challan_number = models.CharField(max_length=50, null=True, blank=True)
    last_challan_number = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name_plural = "Clerk Activity Histories"

    def __str__(self):
        return f"{self.clerk.clerk_name} - {self.date}"