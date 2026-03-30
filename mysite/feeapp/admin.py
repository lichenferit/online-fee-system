# feeapp/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    User, Clerk, ClerkOTP, FeeHead, FeeHeadProgram, Logo,
    Challan, Installment, Payment, ChallanFeeHead,
    Programs, CourseGroup, Session, SchemeOfStudy, RegisteredStudent,
    Province, District, SchemeCourse,
    ClerkLoginHistory, ClerkActivityHistory
)

# ===================================================================
# USER ADMIN
# ===================================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name")}),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "is_staff", "is_active"),
        }),
    )
    readonly_fields = ("date_joined", "last_login")


# ===================================================================
# CLERK ADMIN
# ===================================================================
@admin.register(Clerk)
class ClerkAdmin(admin.ModelAdmin):
    list_display = ("clerk_id", "clerk_name", "user_email", "phone_number", "position")
    search_fields = ("clerk_id", "clerk_name", "phone_number", "user__email")
    list_filter = ("position",)
    ordering = ("clerk_name",)
    readonly_fields = ("clerk_id",)

    fieldsets = (
        ("User Account", {"fields": ("user",)}),
        ("Clerk Information", {
            "fields": ("clerk_id", "clerk_name", "phone_number", "position", "cnic", "gender")
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else "No Email"
    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"


# ===================================================================
# CLERK OTP ADMIN
# ===================================================================
@admin.register(ClerkOTP)
class ClerkOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "get_clerk_name", "otp_code", "created_at", "is_used", "is_expired_display")
    readonly_fields = ("created_at", "otp_code")
    list_filter = ("is_used", "created_at")
    search_fields = ("clerk__clerk_name", "clerk__user__email", "otp_code")
    ordering = ("-created_at",)

    fieldsets = (
        ("OTP Information", {"fields": ("clerk", "otp_code", "is_used")}),
        ("Timing", {"fields": ("created_at",)}),
    )

    def get_clerk_name(self, obj):
        return obj.clerk.clerk_name
    get_clerk_name.short_description = "Clerk Name"
    get_clerk_name.admin_order_field = "clerk__clerk_name"

    def is_expired_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = "Status"


# ===================================================================
# ACADEMIC STRUCTURE ADMINS
# ===================================================================
@admin.register(Programs)
class ProgramsAdmin(admin.ModelAdmin):
    list_display = ("id", "heading", "created_at")
    search_fields = ("heading",)
    list_filter = ("created_at",)
    ordering = ("heading",)


@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "program_id", "created_at")
    search_fields = ("name",)
    list_filter = ("program_id", "created_at")
    ordering = ("name",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "year")
    search_fields = ("year",)
    ordering = ("year",)


@admin.register(SchemeOfStudy)
class SchemeOfStudyAdmin(admin.ModelAdmin):
    list_display = ("id", "program", "course_group", "session")
    search_fields = ("program__heading", "course_group__name", "session__year")
    list_filter = ("program", "session")
    ordering = ("program", "session")


@admin.register(SchemeCourse)
class SchemeCourseAdmin(admin.ModelAdmin):
    list_display = ("id", "scheme", "semester_year", "course_code", "course_name", "status")
    search_fields = ("course_code", "course_name")
    list_filter = ("status", "semester_year")
    ordering = ("scheme", "semester_year")


# ===================================================================
# LOCATION ADMINS
# ===================================================================
@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("id", "province")
    search_fields = ("province",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "district")
    search_fields = ("district",)


# ===================================================================
# REGISTERED STUDENT ADMIN
# ===================================================================
@admin.register(RegisteredStudent)
class RegisteredStudentAdmin(admin.ModelAdmin):
    list_display = (
        "name", "cnic_no", "college_roll_no", "registration_no",
        "get_program", "get_course_group", "status", "gender", "date_of_birth", "created_at"
    )
    search_fields = (
        "name", "cnic_no", "college_roll_no",
        "registration_no", "email", "mobile_no"
    )
    list_filter = ("status", "gender", "religion", "scheme_of_study__program", "created_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Academic Information", {
            "fields": ("scheme_of_study", "status", "college_roll_no", "university_roll_no", "registration_no")
        }),
        ("Personal Information", {
            "fields": ("name", "cnic_no", "photo", "date_of_birth", "mobile_no", "email", "gender", "religion")
        }),
        ("Father Information", {
            "fields": ("father_name", "father_cnic", "father_mobile_no", "father_occupation")
        }),
        ("Guardian Information", {
            "fields": ("guardian_name", "guardian_cnic", "guardian_contact_no")
        }),
        ("Address Information", {
            "fields": ("permanent_address", "postal_address", "province", "district", "city")
        }),
        ("Other Details", {
            "fields": ("blood_group", "marital_status", "hafiz_e_quran", "hafiz_doc", "disability_status", "disability_type")
        }),
        ("Worker Information", {
            "fields": ("related_to_worker", "worker_name", "worker_relation", "worker_payscale", "worker_status")
        }),
    )

    def get_program(self, obj):
        return obj.scheme_of_study.program.heading if obj.scheme_of_study else "N/A"
    get_program.short_description = "Program"

    def get_course_group(self, obj):
        return obj.scheme_of_study.course_group.name if obj.scheme_of_study else "N/A"
    get_course_group.short_description = "Course Group"


# ===================================================================
# FEE HEAD ADMIN
# ===================================================================
class FeeHeadProgramInline(admin.TabularInline):
    model = FeeHeadProgram
    extra = 1
    fields = ('program',)


@admin.register(FeeHead)
class FeeHeadAdmin(admin.ModelAdmin):
    list_display = ("fee_head_account_id", "fee_head_name", "fee_head_amount", "get_programs")
    search_fields = ("fee_head_name",)
    ordering = ("fee_head_name",)
    inlines = [FeeHeadProgramInline]

    fieldsets = (
        ("Fee Information", {"fields": ("fee_head_name", "fee_head_amount")}),
    )

    def get_programs(self, obj):
        programs = FeeHeadProgram.objects.filter(fee_head=obj).select_related('program')
        return ", ".join([p.program.heading for p in programs])
    get_programs.short_description = "Programs"


# ===================================================================
# FEE HEAD PROGRAM ADMIN
# ===================================================================
@admin.register(FeeHeadProgram)
class FeeHeadProgramAdmin(admin.ModelAdmin):
    list_display = ("fee_head", "program")
    list_filter = ("program",)
    search_fields = ("fee_head__fee_head_name", "program__heading")

    fieldsets = (
        ("Association", {"fields": ("fee_head", "program")}),
    )


# ===================================================================
# LOGO ADMIN
# ===================================================================
@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ("college_id", "college_name", "logo_thumbnail", "uploaded_by", "uploaded_date", "is_active")
    search_fields = ("college_name", "uploaded_by")
    list_filter = ("is_active", "uploaded_date")
    ordering = ("college_name",)
    readonly_fields = ("uploaded_date",)

    fieldsets = (
        ("College Information", {"fields": ("college_name", "is_active")}),
        ("Logo Details", {"fields": ("logo", "uploaded_by", "uploaded_date")}),
    )

    def logo_thumbnail(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No Logo"
    logo_thumbnail.short_description = "Logo Preview"


# ===================================================================
# CHALLAN FEE HEAD INLINE
# ===================================================================
class ChallanFeeHeadInline(admin.TabularInline):
    model = ChallanFeeHead
    extra = 1
    fields = ('fee_head_account', 'amount', 'date_of_generation')
    readonly_fields = ('date_of_generation',)


# ===================================================================
# CHALLAN ADMIN
# ===================================================================
@admin.register(Challan)
class ChallanAdmin(admin.ModelAdmin):
    list_display = (
        "challan_number",
        "get_student_name",
        "get_student_cnic",
        "original_total_amount",
        "challan_amount",
        "remaining_amount",
        "due_date",
        "payment_status",
        "get_created_by_clerk",
        "challan_generation_date",
        "challan_file",
    )

    search_fields = (
        "challan_number",
        "student__name",
        "student__cnic_no",
        "created_by_clerk__clerk_name",
    )

    list_filter = (
        "payment_status",
        "download_status",
        "due_date",
        "challan_generation_date",
        "created_by_clerk",
    )

    ordering = ("-challan_generation_date", "due_date")
    readonly_fields = ("challan_generation_date",)
    inlines = [ChallanFeeHeadInline]

    fieldsets = (
        ("Basic Information", {
            "fields": ("challan_number", "student", "payment_status", "download_status", "created_by_clerk")
        }),
        ("Amount and Dates", {
            "fields": (
                "challan_amount",
                "original_total_amount",
                "remaining_amount",
                "due_date",
                "challan_generation_date"
            )
        }),
        ("Details", {
            "fields": ("disciplines", "semesters", "one_bill_number", "status"),
            "classes": ("collapse",)
        }),
        ("Content", {
            "fields": ("html_content",),
            "classes": ("collapse",)
        }),
        ("File", {
            "fields": ("challan_file",),
            "classes": ("collapse",)
        }),
    )

    def get_student_name(self, obj):
        return obj.student.name if obj.student else "N/A"
    get_student_name.short_description = "Student Name"
    get_student_name.admin_order_field = "student__name"

    def get_student_cnic(self, obj):
        return obj.student.cnic_no if obj.student else "N/A"
    get_student_cnic.short_description = "CNIC"
    get_student_cnic.admin_order_field = "student__cnic_no"

    def get_created_by_clerk(self, obj):
        if obj.created_by_clerk:
            return f"{obj.created_by_clerk.clerk_name} ({obj.created_by_clerk.clerk_id})"
        return "N/A"
    get_created_by_clerk.short_description = "Created By"
    get_created_by_clerk.admin_order_field = "created_by_clerk__clerk_name"


# ===================================================================
# CHALLAN FEE HEAD ADMIN
# ===================================================================
@admin.register(ChallanFeeHead)
class ChallanFeeHeadAdmin(admin.ModelAdmin):
    list_display = ("id", "get_challan_number", "get_fee_head_name", "amount", "date_of_generation")
    search_fields = ("challan__challan_number", "fee_head_account__fee_head_name")
    list_filter = ("date_of_generation", "fee_head_account")
    ordering = ("-date_of_generation",)

    def get_challan_number(self, obj):
        return obj.challan.challan_number
    get_challan_number.short_description = "Challan Number"
    get_challan_number.admin_order_field = "challan__challan_number"

    def get_fee_head_name(self, obj):
        return obj.fee_head_account.fee_head_name
    get_fee_head_name.short_description = "Fee Head"
    get_fee_head_name.admin_order_field = "fee_head_account__fee_head_name"


# ===================================================================
# INSTALLMENT ADMIN
# ===================================================================
@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = (
        'get_original_challan_number',
        'get_student_name',
        'installment_number',
        'amount',
        'due_date',
        'status',
        'get_installment_challan_number',
    )

    search_fields = (
        'original_challan__challan_number',
        'original_challan__student__name',
        'installment_challan__challan_number',
    )

    list_filter = ('status', 'due_date', 'installment_number')
    ordering = ('original_challan__challan_number', 'installment_number')
    readonly_fields = ('original_challan', 'installment_challan')

    fieldsets = (
        ("Plan Information", {
            "fields": ('original_challan', 'installment_challan')
        }),
        ("Installment Details", {
            "fields": ('installment_number', 'amount', 'due_date', 'status')
        }),
    )

    def get_original_challan_number(self, obj):
        return obj.original_challan.challan_number
    get_original_challan_number.short_description = "Original Challan"

    def get_student_name(self, obj):
        return obj.original_challan.student.name
    get_student_name.short_description = "Student Name"

    def get_installment_challan_number(self, obj):
        return obj.installment_challan.challan_number if obj.installment_challan else "N/A"
    get_installment_challan_number.short_description = "Installment Challan"


# ===================================================================
# PAYMENT ADMIN
# ===================================================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "get_challan_number", "amount_paid", "payment_date", "payment_method", "is_verified")
    search_fields = ("challan__challan_number", "transaction_id")
    list_filter = ("is_verified", "payment_date", "payment_method")
    ordering = ("-payment_date",)

    fieldsets = (
        ("Payment Information", {
            "fields": ("challan", "amount_paid", "payment_method", "transaction_id")
        }),
        ("Date and Verification", {
            "fields": ("payment_date", "is_verified")
        }),
    )

    def get_challan_number(self, obj):
        return obj.challan.challan_number
    get_challan_number.short_description = "Challan Number"
    get_challan_number.admin_order_field = "challan__challan_number"


# ===================================================================
# NEW: CLERK LOGIN HISTORY ADMIN
# ===================================================================
@admin.register(ClerkLoginHistory)
class ClerkLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_email", "date", "login_time", "logout_time", "get_session_duration")
    search_fields = ("user__email",)
    list_filter = ("date",)
    ordering = ("-date", "-login_time")
    readonly_fields = ("user", "date", "login_time", "logout_time")

    fieldsets = (
        ("Login Information", {
            "fields": ("user", "date", "login_time", "logout_time")
        }),
    )

    def get_user_email(self, obj):
        return obj.user.email if obj.user else " "
    get_user_email.short_description = "User ID"
    get_user_email.admin_order_field = "user__email"

    def get_session_duration(self, obj):
        if obj.login_time and obj.logout_time:
            from datetime import datetime, date
            login_dt = datetime.combine(date.today(), obj.login_time)
            logout_dt = datetime.combine(date.today(), obj.logout_time)
            diff = logout_dt - login_dt
            total_seconds = int(diff.total_seconds())
            if total_seconds < 0:
                return "N/A"
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours}h {minutes}m {seconds}s"
        return "Still Active"
    get_session_duration.short_description = "Session Duration"


# ===================================================================
# NEW: CLERK ACTIVITY HISTORY ADMIN
# ===================================================================
@admin.register(ClerkActivityHistory)
class ClerkActivityHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "get_clerk_name", "date", "time", "first_challan_number", "last_challan_number", "get_total_challans")
    search_fields = ("clerk__clerk_name", "first_challan_number", "last_challan_number")
    list_filter = ("date", "clerk")
    ordering = ("-date", "-time")
    readonly_fields = ("clerk", "date", "time", "first_challan_number", "last_challan_number")

    fieldsets = (
        ("Clerk Information", {
            "fields": ("clerk", "date", "time")
        }),
        ("Challan Activity", {
            "fields": ("first_challan_number", "last_challan_number")
        }),
    )

    def get_clerk_name(self, obj):
        return obj.clerk.clerk_name if obj.clerk else " "
    get_clerk_name.short_description = "Clerk Name"
    get_clerk_name.admin_order_field = "clerk__clerk_name"

    def get_total_challans(self, obj):
        if obj.first_challan_number and obj.last_challan_number:
            try:
                first_seq = int(obj.first_challan_number[-3:])
                last_seq = int(obj.last_challan_number[-3:])
                total = last_seq - first_seq + 1
                return total
            except (ValueError, TypeError):
                return ""
        return ""
    get_total_challans.short_description = "Total Challans Generated"


# ===================================================================
# ADMIN SITE CUSTOMIZATION
# ===================================================================
admin.site.site_header = "Fee System Administration"
admin.site.index_title = "Welcome to Fee System"
admin.site.site_title = "Fee System Admin"