from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.template.loader import get_template
from django.db import transaction
from decimal import Decimal
import random
import json
import re
import io
import hashlib
import requests
import base64
import os
from django.conf import settings

from functools import wraps
from django.http import HttpResponse
def no_cache(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return wrapper


from .models import User, Clerk, ClerkOTP, FeeHead, Challan, ChallanFeeHead, Logo, FeeHeadProgram, Installment, Payment
from .models import (
    User, Clerk, ClerkOTP, FeeHead, Challan, ChallanFeeHead,
    Logo, FeeHeadProgram, Installment, Payment,
    Programs, CourseGroup, Session, SchemeOfStudy, RegisteredStudent, ClerkLoginHistory, ClerkActivityHistory
)


# ─────────────────────────────────────────────────────────────────────────────
# ROLE SELECTION
# ─────────────────────────────────────────────────────────────────────────────

@no_cache
def role_select_view(request):
    if 'student_id' in request.session:
        request.session.flush()
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/role_select.html', {'active_logo': active_logo})


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT LOGIN & DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@no_cache
def student_login(request):
    active_logo = Logo.objects.filter(is_active=True).first()  # ← یہ اوپر ہے ✅
    
    if 'student_id' in request.session:
        request.session.flush()  
    
    if request.method == 'POST':
        cnic = request.POST.get('cnic')
        dob = request.POST.get('dob')
        if not cnic or not dob:
            messages.error(request, "CNIC and Date of Birth are required.")
            return render(request, 'feeapp/student_login.html', {'active_logo': active_logo})  
        try:
            student = RegisteredStudent.objects.get(cnic_no=cnic, date_of_birth=dob)
            request.session['student_id'] = student.id
            request.session['student_name'] = student.name
            return redirect('student_dashboard')
        except RegisteredStudent.DoesNotExist:
            messages.error(request, "Invalid CNIC or Date of Birth. Please try again.")
            return render(request, 'feeapp/student_login.html', {'active_logo': active_logo})  
    return render(request, 'feeapp/student_login.html', {'active_logo': active_logo})
@no_cache
def student_dashboard(request):
    if 'student_id' not in request.session:
        return redirect('student_login')

    student = get_object_or_404(RegisteredStudent, id=request.session['student_id'])

    check_and_apply_arrears(student)
    base_challans = Challan.objects.filter(
        student=student,
        original_total_amount__isnull=False
    ).exclude(
        challan_number__contains='-'
    ).order_by('-challan_generation_date')

    challan_data = []
    for base_challan in base_challans:
        installments = base_challan.installments.all().order_by('installment_number')

        installment_details = []
        if installments.exists():
            for inst in installments:
                inst_challan = inst.installment_challan
                installment_details.append({
                    'label': f'Installment {inst.installment_number}',
                    'challan_number': inst_challan.challan_number,
                    'amount': float(inst.amount),
                    'due_date': inst.due_date.strftime('%d/%m/%Y'),
                    'status': inst.status,
                    'challan_file_url': inst_challan.challan_file.url if inst_challan.challan_file else None,
                })

        challan_data.append({
            'challan_number': base_challan.challan_number,
            'original_amount': float(base_challan.original_total_amount or base_challan.challan_amount),
            'remaining_amount': float(base_challan.remaining_amount or 0),
            'due_date': base_challan.due_date,
            'status': base_challan.status,
            'payment_status': base_challan.payment_status,
            'installment_details': installment_details,
            'has_installments': len(installment_details) > 0,
            'challan_file_url': base_challan.challan_file.url if base_challan.challan_file else None,
        })

    context = {
        'student_name': student.name,
        'challan_data': challan_data,
    }
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/student_dashboard.html', {'active_logo': active_logo, **context})


# ─────────────────────────────────────────────────────────────────────────────
# CLERK LOGIN & AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────

@no_cache
def clerk_login(request): 
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/clerk_login.html', {'active_logo': active_logo})


@no_cache
@login_required

def clerk_dashboard(request):
    is_admin = request.user.is_superuser or request.user.is_staff

    try:
        clerk = Clerk.objects.get(user=request.user)
        active_logo = Logo.objects.filter(is_active=True).first()
        context = {
            'clerk_name': clerk.clerk_name,
            'clerk_id': clerk.clerk_id,
            'active_logo': active_logo,
            'is_admin': is_admin,
        }
        return render(request, 'feeapp/clerk_dashboard.html', context)

    except Clerk.DoesNotExist:
        if is_admin:
            active_logo = Logo.objects.filter(is_active=True).first()
            context = {
                'clerk_name': request.user.get_full_name() or request.user.email,
                'clerk_id': 'ADMIN',
                'active_logo': active_logo,
                'is_admin': True,
            }
            return render(request, 'feeapp/clerk_dashboard.html', context)

        from django.contrib.auth import logout as auth_logout
        auth_logout(request)
        return redirect('clerk_login')


@csrf_exempt
@require_POST
def clerk_login_api(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        print(f"Login attempt for email: {email}")

        if not email or not password:
            return JsonResponse({'success': False, 'message': 'Email and password are required.'})

        try:
            user = User.objects.get(email=email)
            print(f"User found: {user.username}, {user.email}")
        except User.DoesNotExist:
            print(f"No user found with email: {email}")
            return JsonResponse({'success': False, 'message': 'Invalid email or password.'})

        is_admin = user.is_superuser or user.is_staff
        is_clerk = Clerk.objects.filter(user=user).exists()

        if not is_admin and not is_clerk:
            print(f"No clerk found for user: {user.username}")
            return JsonResponse({'success': False, 'message': 'Access denied. You are not authorized.'})

        authenticated_user = authenticate(request, username=email, password=password)
        if authenticated_user is not None:
            login(request, authenticated_user)
            print(f"Login successful for: {email}")

            now = datetime.now()

            if is_clerk:
                clerk = Clerk.objects.get(user=user)

                login_record = ClerkLoginHistory.objects.create(
                    user=user,
                    date=now.date(),
                    login_time=now.time(),
                    logout_time=None,
                )
                request.session['login_history_id'] = login_record.id

                activity_record = ClerkActivityHistory.objects.create(
                    clerk=clerk,
                    date=now.date(),
                    time=now.time(),
                    first_challan_number=None,
                    last_challan_number=None,
                )
                request.session['activity_history_id'] = activity_record.id

            request.session['is_admin_login'] = is_admin

            return JsonResponse({'success': True, 'message': 'Login successful.'})
        else:
            print(f"Authentication failed for: {email}")
            if user.check_password(password):
                return JsonResponse({'success': False, 'message': 'Authentication failed. Please contact administrator.'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid email or password.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format.'})
    except Exception as e:
        print(f"Login API error: {str(e)}")
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@csrf_exempt
@require_POST
def clerk_forgot_password_api(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        print(f"Forgot password request for: {email}")

        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'This email is not registered in our system.'})

        is_admin = user.is_superuser or user.is_staff

        if not is_admin:
            try:
                clerk = Clerk.objects.get(user=user)
            except Clerk.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'This email is not registered as a clerk.'})

        if is_admin:
            import random
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            request.session['admin_reset_otp'] = otp_code
            request.session['admin_reset_email'] = email
            request.session['admin_reset_otp_time'] = str(datetime.now())

            display_name = user.get_full_name() or user.email

            try:
                subject = 'Admin Password Reset OTP'
                message = f'Dear {display_name},\\n\\nYour OTP for password reset is: {otp_code}\\n\\nThis OTP will expire in 5 minutes.\\n\\nBest regards,\\nSystem'
                from_email = settings.DEFAULT_FROM_EMAIL
                send_mail(subject, message, from_email, [email], fail_silently=False)
                print(f"Admin OTP email sent to: {email}")
            except Exception as email_error:
                print(f"Admin OTP email failed: {str(email_error)}")

            return JsonResponse({'success': True, 'message': 'OTP has been sent to your email.'})

        else:
            ClerkOTP.objects.filter(clerk=clerk).delete()
            otp_code = ClerkOTP.generate_otp()
            ClerkOTP.objects.create(clerk=clerk, otp_code=otp_code)

            try:
                subject = 'Password Reset OTP - Government Graduate College'
                message = f'Dear {clerk.clerk_name},\\n\\nYour OTP for password reset is: {otp_code}\\n\\nThis OTP will expire in 5 minutes.\\n\\nBest regards,\\nGovernment Graduate College'
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            except Exception as email_error:
                print(f"Email sending failed: {str(email_error)}")

            return JsonResponse({'success': True, 'message': 'OTP has been sent to your email.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@csrf_exempt
@require_POST
def clerk_resend_otp_api(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'})

        try:
            user = User.objects.get(email=email)
            clerk = Clerk.objects.get(user=user)
        except (User.DoesNotExist, Clerk.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'This email is not registered in our system.'})

        ClerkOTP.objects.filter(clerk=clerk).delete()

        otp_code = ClerkOTP.generate_otp()
        ClerkOTP.objects.create(clerk=clerk, otp_code=otp_code)

        try:
            subject = 'Password Reset OTP - Resent'
            message = f'Dear {clerk.clerk_name},\n\nYour new OTP for password reset is: {otp_code}\n\nThis OTP will expire in 5 minutes.\n\nBest regards,\nGovernment Graduate College'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as email_error:
            print(f"Resend email failed: {str(email_error)}")
            pass

        return JsonResponse({'success': True, 'message': 'A new OTP has been sent to your email.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@csrf_exempt
@require_POST
def clerk_verify_otp_api(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        otp = data.get('otp')
        if not email or not otp:
            return JsonResponse({'success': False, 'message': 'Email and OTP are required.'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid email or OTP.'})

        is_admin = user.is_superuser or user.is_staff

        if is_admin:
            session_otp   = request.session.get('admin_reset_otp')
            session_email = request.session.get('admin_reset_email')
            session_time  = request.session.get('admin_reset_otp_time')

            if not session_otp or session_email != email:
                return JsonResponse({'success': False, 'message': 'Invalid OTP. Please request again.'})

            if session_time:
                otp_time = datetime.fromisoformat(session_time)
                if (datetime.now() - otp_time).total_seconds() > 300:
                    return JsonResponse({'success': False, 'message': 'OTP has expired. Please request a new one.'})

            if otp != session_otp:
                return JsonResponse({'success': False, 'message': 'Invalid OTP.'})

            request.session['admin_otp_verified'] = True
            return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})

        else:
            try:
                clerk = Clerk.objects.get(user=user)
            except Clerk.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid email or OTP.'})

            try:
                clerk_otp = ClerkOTP.objects.get(clerk=clerk, otp_code=otp, is_used=False)
            except ClerkOTP.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid OTP.'})

            if clerk_otp.is_expired():
                return JsonResponse({'success': False, 'message': 'OTP has expired. Please request a new one.'})

            clerk_otp.is_used = True
            clerk_otp.save()
            return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@csrf_exempt
@require_POST
def clerk_reset_password_api(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        new_password = data.get('new_password')
        if not email or not new_password:
            return JsonResponse({'success': False, 'message': 'Email and new password are required.'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid email.'})

        is_admin = user.is_superuser or user.is_staff

        if is_admin:
            if not request.session.get('admin_otp_verified'):
                return JsonResponse({'success': False, 'message': 'Please verify OTP first.'})
            if request.session.get('admin_reset_email') != email:
                return JsonResponse({'success': False, 'message': 'Session mismatch. Please try again.'})

            user.set_password(new_password)
            user.save()

            for key in ['admin_reset_otp', 'admin_reset_email', 'admin_reset_otp_time', 'admin_otp_verified']:
                request.session.pop(key, None)

            return JsonResponse({'success': True, 'message': 'Password has been reset successfully.'})

        else:
            try:
                clerk = Clerk.objects.get(user=user)
            except Clerk.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid email.'})

            recent_used_otp = ClerkOTP.objects.filter(
                clerk=clerk,
                is_used=True,
                created_at__gte=timezone.now() - timedelta(minutes=10)
            ).first()
            if not recent_used_otp:
                return JsonResponse({'success': False, 'message': 'Please verify OTP first.'})

            user.set_password(new_password)
            user.save()
            ClerkOTP.objects.filter(clerk=clerk).delete()

            return JsonResponse({'success': True, 'message': 'Password has been reset successfully.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

def logout_action(request):
    from django.contrib.auth import logout as auth_logout

    user_type = request.GET.get('from', 'student')

    if user_type == 'student':
        if 'student_id' in request.session:
            del request.session['student_id']
        if 'student_name' in request.session:
            del request.session['student_name']
        if 'last_activity' in request.session:
            del request.session['last_activity']
        request.session.flush()
        
        response = redirect('role_select')         
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    elif user_type == 'clerk':

        login_history_id = request.session.get('login_history_id')
        if login_history_id:
            try:
                login_record = ClerkLoginHistory.objects.get(id=login_history_id)
                login_record.logout_time = datetime.now().time()
                login_record.save()
            except ClerkLoginHistory.DoesNotExist:
                pass

        activity_history_id = request.session.get('activity_history_id')
        if activity_history_id:
            try:
                activity_record = ClerkActivityHistory.objects.get(id=activity_history_id)

                if not activity_record.first_challan_number:
                    activity_record.delete()
                else:
                    if request.user.is_authenticated:
                        try:
                            clerk = Clerk.objects.get(user=request.user)
                            last_challan = Challan.objects.filter(
                                created_by_clerk=clerk
                            ).order_by('-challan_generation_date', '-challan_generation_time').first()
                            if last_challan:
                                activity_record.last_challan_number = last_challan.challan_number
                                activity_record.save()
                        except Clerk.DoesNotExist:
                            pass

            except ClerkActivityHistory.DoesNotExist:
                pass

        auth_logout(request)
        request.session.flush()

        response = redirect('role_select')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return redirect('role_select')


def logout(request):
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'logout.html', {'active_logo': active_logo})


def logout_confirmation(request):
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/logout.html', {'active_logo': active_logo})


@csrf_exempt
@require_POST
def save_auto_logout_time(request):
    login_history_id = request.session.get('login_history_id')

    if not login_history_id:
        return JsonResponse({'success': False, 'message': 'No session found.'})

    try:
        login_record = ClerkLoginHistory.objects.get(id=login_history_id)

        if not login_record.logout_time:
            now = datetime.now()
            login_record.logout_time = now.time()
            login_record.logout_date = now.date()
            login_record.save()

        return JsonResponse({'success': True})

    except ClerkLoginHistory.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Login record not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# ONELINK / 1BILL PAYMENT SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class OneLinkService:

    @staticmethod
    def generate_consumer_number(student, challan_amount):
        config = getattr(settings, 'ONELINK_CONFIG', {})

        if config.get('USE_REAL_API', False):
            return OneLinkService._create_real_consumer_number(student, challan_amount)
        else:
            return OneLinkService._create_demo_consumer_number(student)

    @staticmethod
    def _create_demo_consumer_number(student):
        config = getattr(settings, 'ONELINK_CONFIG', {})
        prefix = config.get('CONSUMER_NUMBER_PREFIX', '01')

        roll_suffix = student.college_roll_no[-2:] if len(student.college_roll_no) >= 2 else student.college_roll_no.zfill(2)[-2:]

        max_attempts = 100
        for _ in range(max_attempts):
            cnic_hash = hashlib.md5(student.cnic_no.encode()).hexdigest()[:6]
            random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            suffix = cnic_hash + random_suffix

            consumer_number = f"{prefix}{roll_suffix}{suffix}"
            consumer_number = consumer_number[:14].ljust(14, '0')

            if not Challan.objects.filter(one_bill_number=consumer_number).exists():
                return consumer_number

        return prefix + ''.join([str(random.randint(0, 9)) for _ in range(12)])

    @staticmethod
    def _create_real_consumer_number(student, challan_amount):
        config = getattr(settings, 'ONELINK_CONFIG', {})

        try:
            api_url = config.get('API_URL') + 'consumer/register'

            payload = {
                'merchant_id': config.get('MERCHANT_ID'),
                'company_code': config.get('COMPANY_CODE'),
                'consumer_detail': {
                    'name': student.name,
                    'mobile': student.mobile_no,
                    'cnic': student.cnic_no,
                    'email': student.email,
                    'roll_number': student.college_roll_no,
                },
                'bill_amount': str(challan_amount),
                'due_date': datetime.now().strftime('%Y-%m-%d'),
            }

            headers = {
                'Authorization': f"Bearer {config.get('API_KEY')}",
                'Content-Type': 'application/json'
            }

            response = requests.post(api_url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('consumer_number')
            else:
                print(f"1Bill API Error: {response.text}")
                return OneLinkService._create_demo_consumer_number(student)

        except Exception as e:
            print(f"OneLink API Exception: {str(e)}")
            return OneLinkService._create_demo_consumer_number(student)

    @staticmethod
    def verify_payment(consumer_number, transaction_id=None):
        config = getattr(settings, 'ONELINK_CONFIG', {})

        if not config.get('USE_REAL_API', False):
            return {
                'status': 'PENDING_VERIFICATION',
                'message': 'Demo mode - manual verification required'
            }

        try:
            api_url = config.get('API_URL') + 'payment/verify'

            payload = {
                'merchant_id': config.get('MERCHANT_ID'),
                'consumer_number': consumer_number,
            }

            if transaction_id:
                payload['transaction_id'] = transaction_id

            headers = {
                'Authorization': f"Bearer {config.get('API_KEY')}",
                'Content-Type': 'application/json'
            }

            response = requests.post(api_url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'ERROR', 'message': response.text}

        except Exception as e:
            return {'status': 'ERROR', 'message': str(e)}

    @staticmethod
    def get_supported_banks():
        return [
            'HBL (Habib Bank Limited)',
            'UBL (United Bank Limited)',
            'BOP (Bank Of Punjab)',
        ]


# ─────────────────────────────────────────────────────────────────────────────
# CHALLAN FORM & PROGRAM/STUDENT API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

def challan_form(request):
    active_logo = get_active_logo()
    context = {
        'active_logo': active_logo
    }
    return render(request, 'feeapp/challan_form.html', context)


@csrf_exempt
def get_programs(request):
    programs = Programs.objects.all().values('id', 'heading')
    return JsonResponse({'programs': [
        {'program_id': p['id'], 'ProgramName': p['heading']}
        for p in programs
    ]})


@csrf_exempt
def get_program_details(request, program_id):
    try:
        program_id = int(program_id)
        program = Programs.objects.get(id=program_id)

        shifts = ['Morning', 'Evening']

        schemes = SchemeOfStudy.objects.filter(program=program).select_related('session').distinct()
        sessions = list({scheme.session.year: {'session_name': scheme.session.year}
                        for scheme in schemes}.values())

        course_groups = CourseGroup.objects.filter(program_id=program).values('id', 'name')
        disciplines_list = [
            {
                'discipline_id': int(cg['id']),
                'discipline_name': str(cg['name'])
            }
            for cg in course_groups
        ]

        if 'BS' in program.heading.upper() or 'FOUR' in program.heading.upper():
            semesters = [{'semester_id': i, 'semester_name': f'Semester {i}'} for i in range(1, 9)]
        elif 'INTER' in program.heading.upper():
            semesters = [{'semester_id': i, 'semester_name': f'Year {i}'} for i in range(1, 3)]
        elif 'BACHELOR' in program.heading.upper() or 'MASTER' in program.heading.upper():
            semesters = [{'semester_id': i, 'semester_name': f'Semester {i}'} for i in range(1, 5)]
        elif 'ADP' in program.heading.upper():
            semesters = [{'semester_id': i, 'semester_name': f'Semester {i}'} for i in range(1, 5)]
        else:
            semesters = [{'semester_id': i, 'semester_name': f'Semester {i}'} for i in range(1, 5)]

        fee_heads = []
        fee_head_programs = FeeHeadProgram.objects.filter(program_id=program_id)
        for fhp in fee_head_programs:
            fee_head = fhp.fee_head
            fee_heads.append({
                'fee_head_account_id': fee_head.fee_head_account_id,
                'fee_head_name': fee_head.fee_head_name,
                'fee_head_amount': str(fee_head.fee_head_amount),
            })

        print(f" Program: {program.heading}")
        print(f" Found {len(disciplines_list)} course groups:")
        for d in disciplines_list:
            print(f"   - ID: {d['discipline_id']} (type: {type(d['discipline_id'])}), Name: {d['discipline_name']}")

        return JsonResponse({
            'shifts': shifts,
            'sessions': sessions,
            'disciplines': disciplines_list,
            'semesters': semesters,
            'fee_heads': fee_heads
        })
    except ValueError:
        return JsonResponse({'error': 'Invalid program ID format'}, status=400)
    except Programs.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)
    except Exception as e:
        import traceback
        print(f" Error in get_program_details: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def get_bs_disciplines(request, category):
    category_mapping = {
        'science': 'BS Science',
        'arts': 'BS Arts'
    }
    db_category = category_mapping.get(category, category)

    course_groups = CourseGroup.objects.filter(name__icontains=db_category).values('id', 'name')
    return JsonResponse({
        'disciplines': [
            {'discipline_id': cg['id'], 'discipline_name': cg['name']}
            for cg in course_groups
        ]
    })


@csrf_exempt
def save_session(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        program_id = data.get('program_id')
        session_name = data.get('session_name')
        try:
            program = Programs.objects.get(id=program_id)
            session, created = Session.objects.get_or_create(year=session_name)
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'session_name': session.year,
                'created': created
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def add_fee_head(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        program_ids = data.get('program_ids', [])
        fee_head_name = data.get('fee_head_name')
        fee_head_amount = data.get('fee_head_amount')
        try:
            fee_head = FeeHead.objects.create(
                fee_head_name=fee_head_name,
                fee_head_amount=fee_head_amount
            )
            programs = Programs.objects.filter(id__in=program_ids)
            for program in programs:
                FeeHeadProgram.objects.create(
                    fee_head=fee_head,
                    program=program
                )
            return JsonResponse({
                'success': True,
                'fee_head_id': fee_head.fee_head_account_id,
                'fee_head_name': fee_head.fee_head_name,
                'fee_head_amount': str(fee_head.fee_head_amount)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_students(request):
    program_id = request.GET.get('program_id')
    shift = request.GET.get('shift')
    session = request.GET.get('session')
    discipline_id = request.GET.get('discipline')
    semester_id = request.GET.get('semester')

    print(f"DEBUG get_students: program={program_id}, shift={shift}, session={session}, discipline={discipline_id}, semester={semester_id}")

    if not all([program_id, shift, session, discipline_id, semester_id]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    try:
        program_id    = int(program_id)
        discipline_id = int(discipline_id)
        semester_id   = int(semester_id)

        students = RegisteredStudent.objects.filter(
            scheme_of_study__program_id=program_id,
            status=shift.lower(),
            scheme_of_study__session__year=session,
            scheme_of_study__course_group_id=discipline_id
        )

        print(f"DEBUG: Exact match found: {students.count()} students")

        if students.count() == 0:
            print(f"DEBUG: Trying without session filter...")
            students = RegisteredStudent.objects.filter(
                scheme_of_study__program_id=program_id,
                status=shift.lower(),
                scheme_of_study__course_group_id=discipline_id
            )
            print(f"DEBUG: Without session found: {students.count()} students")

        if students.count() == 0:
            print(f"DEBUG: Trying with program only...")
            students = RegisteredStudent.objects.filter(
                scheme_of_study__program_id=program_id,
                status=shift.lower(),
            )
            print(f"DEBUG: Program only found: {students.count()} students")

        for s in students:
            print(f"  Student: {s.name}, Session: {s.scheme_of_study.session.year if s.scheme_of_study else 'N/A'}, Shift: {s.status}")

        return JsonResponse({
            'students': [
                {
                    'user_id': s['id'],
                    'student_name': s['name'],
                    'college_roll_number': s['college_roll_no']
                }
                for s in students.values('id', 'name', 'college_roll_no')
            ]
        })

    except ValueError:
        return JsonResponse({'error': 'Invalid ID format'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in get_students: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# CHALLAN GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_challan_number(student):
    total_existing = Challan.objects.count()
    next_sequence = total_existing + 1
    sequence_str = str(next_sequence).zfill(3)

    max_attempts = 100
    for _ in range(max_attempts):
        middle = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        challan_number = f"CH{middle}{sequence_str}"

        if not Challan.objects.filter(challan_number=challan_number).exists():
            return challan_number

    return f"CH{random.randint(1000, 9999)}{sequence_str}"


def get_active_logo():
    try:
        return Logo.objects.get(is_active=True)
    except Logo.DoesNotExist:
        return None


def get_logo_base64():
    try:
        active_logo = get_active_logo()
        if active_logo and active_logo.logo:
            logo_path = active_logo.logo.path
        else:
            logo_path = os.path.join(settings.BASE_DIR, 'static/feeapp/images/logo_college.jpg')

        with open(logo_path, "rb") as image_file:
            return f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    except Exception as e:
        print(f"Error loading logo: {e}")
        return ""


@csrf_exempt
def generate_challan(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        program_id = data.get('program_id')
        shift = data.get('shift')
        session = data.get('session')
        disciplines = data.get('disciplines', [])
        semesters = data.get('semesters', [])
        fee_heads = data.get('fee_heads', [])
        tuition_fee = data.get('tuition_fee')
        due_date = data.get('due_date')
        is_bulk = data.get('is_bulk', False)
        student_id = data.get('student_id')

        print(f" Received disciplines: {disciplines}")
        print(f" Type: {type(disciplines)}")

        disciplines = [int(d) for d in disciplines if d and str(d).strip()]

        if not disciplines:
            return JsonResponse({
                'success': False,
                'error': 'No valid course groups selected. Please select at least one course group.'
            }, status=400)

        clerk = None
        if request.user.is_authenticated:
            try:
                clerk = Clerk.objects.get(user=request.user)
            except Clerk.DoesNotExist:
                pass

        try:
            program = Programs.objects.get(id=program_id)

            if is_bulk:
                course_groups = CourseGroup.objects.filter(id__in=disciplines)

                print(f" Found {course_groups.count()} course groups")

                students = RegisteredStudent.objects.filter(
                    scheme_of_study__program=program,
                    status=shift.lower(),
                    scheme_of_study__session__year=session,
                    scheme_of_study__course_group__in=course_groups
                )

                print(f"✅ Found {students.count()} students")

                if students.count() == 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'No students found matching the selected criteria'
                    }, status=400)

                challans = []
                for student in students:
                    try:
                        challan = create_single_challan_with_html(
                            student, program, shift, session,
                            disciplines, semesters, fee_heads,
                            tuition_fee, due_date, clerk=clerk
                        )
                        challans.append(challan)
                    except Exception as e:
                        print(f" Error creating challan for student {student.name}: {str(e)}")

                return JsonResponse({
                    'success': True,
                    'challans_count': len(challans),
                    'message': f' challans generated for {len(challans)} students successfully'
                })
            else:
                try:
                    student = RegisteredStudent.objects.get(id=student_id)
                except RegisteredStudent.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Student not found'
                    }, status=400)

                try:
                    challan = create_single_challan_with_html(
                        student, program, shift, session,
                        disciplines, semesters, fee_heads,
                        tuition_fee, due_date, clerk=clerk
                    )

                    active_logo = get_active_logo()
                    logo_data = {
                        'logo_url': active_logo.logo.url if active_logo and active_logo.logo else "/static/feeapp/images/logo_college.jpg",
                        'college_name': active_logo.college_name if active_logo else "Government Graduate College, Civil Lines Sheikhupura"
                    }

                    fee_heads_data = []
                    for fee_head in challan.challanfeehead_set.all():
                        fee_heads_data.append({
                            'name': fee_head.fee_head_account.fee_head_name,
                            'amount': str(fee_head.amount)
                        })

                    return JsonResponse({
                        'success': True,
                        'challan_number': challan.challan_number,
                        'student_name': student.name,
                        'roll_number': student.college_roll_no,
                        'shift': student.status,
                        'amount': str(challan.challan_amount),
                        'due_date': challan.due_date.strftime('%Y-%m-%d'),
                        'disciplines': challan.disciplines,
                        'semesters': challan.semesters,
                        'session': session,
                        'fee_heads': fee_heads_data,
                        'one_bill_number': challan.one_bill_number or 'Pending',
                        'logo': logo_data
                    })
                except Exception as e:
                    print(f" Error creating single challan: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    return JsonResponse({
                        'success': False,
                        'error': f'Error creating challan: {str(e)}'
                    }, status=400)
        except Exception as e:
            print(f" Error in generate_challan: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def create_single_challan_with_html(student, program, shift, session, disciplines, semesters, fee_heads, tuition_fee, due_date, clerk=None):
    try:
        with transaction.atomic():
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

            challan_number = generate_challan_number(student)
            total_amount = float(tuition_fee)
            for fee_head_data in fee_heads:
                total_amount += float(fee_head_data['amount'])

            onelink_number = OneLinkService.generate_consumer_number(student, total_amount)

            active_logo = get_active_logo()
            college_name = active_logo.college_name if active_logo else "Government Graduate College, Civil Lines Sheikhupura"

            discipline_names = []
            if disciplines:
                discipline_objects = CourseGroup.objects.filter(id__in=disciplines)
                discipline_names = [obj.name for obj in discipline_objects]

            semester_names = []
            if semesters:
                semester_names = [f"Semester {s}" for s in semesters]

            logo_base64 = get_logo_base64()
            formatted_due_date = due_date.strftime('%d/%m/%Y')
            disciplines_str = ', '.join(discipline_names)
            semesters_str = ', '.join(semester_names)

            fee_table_rows = f"<tr><td>Tuition Fee</td><td>{float(tuition_fee):,.2f}</td></tr>\n"
            for fee_head_data in fee_heads:
                try:
                    fee_head = FeeHead.objects.get(fee_head_account_id=fee_head_data['id'])
                    fee_table_rows += f"<tr><td>{fee_head.fee_head_name}</td><td>{float(fee_head_data['amount']):,.2f}</td></tr>\n"
                except FeeHead.DoesNotExist:
                    pass

            def generate_single_copy(copy_label):
                return f"""
                <div class="challan-copy">
                    <div class="copy-label">{copy_label}</div>
                    <div class="header-section">
                        <div class="logo-container">
                            <img src="{logo_base64}" alt="Logo">
                        </div>
                        <span class="college-name">{college_name}</span>
                    </div>
                    <div class="challan-number"><strong>Challan No.</strong> {challan_number}</div>
                    <div class="program-info">{disciplines_str} - {semesters_str} - Session {session}</div>
                    <hr>
                    <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
                    <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
                    <div class="fee-details">
                        <strong>Fee Breakdown:</strong>
                        <table class="fee-table">
                            <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                            <tbody>{fee_table_rows}</tbody>
                        </table>
                    </div>
                    <div class="amount-box"><strong>Total Due Amount: Rs. {total_amount:,.2f}</strong></div>
                    <div class="instructions">
                        &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                        &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {onelink_number}</strong> and pay.
                    </div>
                    <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
                    <div class="signature-line">Cashier: _________&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Stamp: _________</div>
                </div>"""

            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fee Challan - {challan_number}</title>
    <meta charset="UTF-8">
    <style>
        @page {{ size: 297mm 210mm; margin: 5mm; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Times New Roman', serif; font-size: 14px; background: #fff; }}
        .page-container {{
            width: 100%;
            display: flex;
            flex-direction: row;
            gap: 15px;
            justify-content: left;
            align-items: flex-start;
        }}
        .challan-copy {{
            width: 460px;
            min-height: 800px;
            max-height: 850px;
            border: 2px solid black;
            padding: 15px;
            box-sizing: border-box;
            background: white;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        .copy-label {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #1e3a8a; flex-shrink: 0; }}
        .header-section {{ display: flex; align-items: center; justify-content: left; gap: 8px; margin-bottom: 4px; flex-shrink: 0; }}
        .logo-container {{ width: 35px; height: 35px; border-radius: 50%; overflow: hidden; display: flex; align-items: left; justify-content: left; }}
        .logo-container img {{ width: 100%; height: 100%; border-radius: 50%; }}
        .college-name {{ font-weight: bold; font-size: 14px; margin: 0; }}
        .challan-number {{ text-align: right; font-size: 12px; margin: 3px 0; flex-shrink: 0; }}
        .program-info {{ text-align: center; font-size: 12px; margin: 2px 0; flex-shrink: 0; }}
        .challan-copy hr {{ border: none; border-top: 1px solid black; margin: 5px 0; flex-shrink: 0; }}
        .student-info {{ font-size: 13px; margin: 3px 0; flex-shrink: 0; }}
        .date-box {{ text-align: right; font-size: 12px; margin: 1px 0; flex-shrink: 0; }}
        .fee-details {{ font-size: 12px; margin: 10px 0; height: auto; flex-shrink: 0; }}
        .fee-details strong {{ font-size: 12px; display: block; margin-bottom: 5px; }}
        .fee-table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
        .fee-table th {{ border: 1px solid black; padding: 5px; text-align: center; background-color: #f0f0f0; font-weight: bold; }}
        .fee-table td {{ border: 1px solid black; padding: 5px 8px; word-wrap: break-word; text-align: center; }}
        .fee-table td:first-child {{ width: 60%; text-align: center; }}
        .fee-table td:last-child {{ width: 40%; text-align: center; }}
        .amount-box {{ text-align: right; font-size: 12px; margin: 10px 0; font-weight: bold; flex-shrink: 0; }}
        .instructions {{ border: 2px solid black; padding: 8px; font-size: 12px; margin: 1px 0; line-height: 1.4; flex-shrink: 0; background-color: white; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        .footer-note {{ font-style: italic; font-size: 11px; margin: 5px 0; flex-shrink: 0; }}
        .signature-line {{ font-size: 12px; margin-top: auto; padding-top: 10px; flex-shrink: 0; }}
        .remaining-amount {{ font-weight: bold; }}
        @media print {{
            .page-container {{ display: table !important; width: 100% !important; border-collapse: separate; border-spacing: 2mm; }}
            .challan-copy {{ display: table-cell !important; width: 460mm !important; min-height: auto !important; max-height: 240mm !important; padding: 3mm !important; vertical-align: top; border: 1.5px solid black; }}
            .instructions {{ border: 2px solid black; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="page-container">
        {generate_single_copy('Student Copy')}
        {generate_single_copy('Bank Copy')}
        {generate_single_copy('College Copy')}
    </div>
</body>
</html>"""

            challan = Challan.objects.create(
                challan_number=challan_number,
                due_date=due_date,
                challan_amount=total_amount,
                status='Unpaid',
                payment_status='UNPAID',
                remaining_amount=total_amount,
                challan_generation_date=datetime.now().date(),
                challan_generation_time=datetime.now().time(),
                student=student,
                disciplines=disciplines_str,
                semesters=semesters_str,
                html_content=html_content,
                one_bill_number=onelink_number,
                created_by_clerk=clerk
            )

            tuition_fee_head, created = FeeHead.objects.get_or_create(
                fee_head_name='Tuition Fee',
                defaults={'fee_head_amount': 0}
            )
            if created:
                FeeHeadProgram.objects.create(fee_head=tuition_fee_head, program=program)

            ChallanFeeHead.objects.create(
                fee_head_account=tuition_fee_head,
                challan=challan,
                amount=tuition_fee,
                date_of_generation=datetime.now().date()
            )

            for fee_head_data in fee_heads:
                try:
                    fee_head = FeeHead.objects.get(fee_head_account_id=fee_head_data['id'])
                    ChallanFeeHead.objects.create(
                        fee_head_account=fee_head,
                        challan=challan,
                        amount=fee_head_data['amount'],
                        date_of_generation=datetime.now().date()
                    )
                except FeeHead.DoesNotExist:
                    pass

            challan.challan_file.save(
                f"{challan_number}.html",
                ContentFile(html_content.encode('utf-8'))
            )

            if clerk:
                today = datetime.now().date()
                activity_record = ClerkActivityHistory.objects.filter(
                    clerk=clerk,
                    date=today
                ).order_by('-time').first()

                if activity_record:
                    if not activity_record.first_challan_number:
                        activity_record.first_challan_number = challan_number
                        activity_record.time = datetime.now().time()
                    activity_record.last_challan_number = challan_number
                    activity_record.save()

            return challan

    except Exception as e:
        print(f"Error in create_single_challan_with_html: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise


# ─────────────────────────────────────────────────────────────────────────────
# CHALLAN DOWNLOAD, VIEW & SEARCH
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def download_challan_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cnic = data.get('cnic')

            if not cnic:
                return JsonResponse({'error': 'Please enter your CNIC number'}, status=400)

            if 'student_id' not in request.session:
                return JsonResponse({
                    'error': 'You are not logged in. Please log in first.'
                }, status=401)

            session_student_id = request.session['student_id']

            try:
                session_student = RegisteredStudent.objects.get(id=session_student_id)
            except RegisteredStudent.DoesNotExist:
                return JsonResponse({
                    'error': 'Session expired. Please log in again.'
                }, status=401)

            cnic_entered = re.sub(r'\D', '', cnic)
            cnic_session = re.sub(r'\D', '', session_student.cnic_no)

            if cnic_entered != cnic_session:
                return JsonResponse({
                    'error': 'CNIC does not match your logged-in account. Please enter your own CNIC.'
                }, status=403)

            student = session_student

            check_and_apply_arrears(student)

            all_challans = Challan.objects.filter(
                student=student
            ).order_by('-challan_generation_date')

            if not all_challans.exists():
                return JsonResponse({
                    'error': 'No challans found for this student.'
                }, status=404)

            challan_list = []
            for challan in all_challans:
                is_paid = (
                    challan.payment_status == 'PAID' or
                    challan.status.upper() == 'PAID'
                )

                challan_list.append({
                    'challan_number': challan.challan_number,
                    'challan_amount': str(challan.challan_amount),
                    'due_date': challan.due_date.strftime('%d/%m/%Y') if challan.due_date else 'N/A',
                    'generation_date': challan.challan_generation_date.strftime('%d/%m/%Y') if challan.challan_generation_date else 'N/A',
                    'is_paid': is_paid,
                    'disciplines': challan.disciplines or 'N/A',
                    'semesters': challan.semesters or 'N/A',
                    'html_content': challan.html_content or '',
                })

            return JsonResponse({
                'success': True,
                'student_name': student.name,
                'challan_list': challan_list,
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format.'}, status=400)
        except Exception as e:
            print(f"DEBUG: Error in download_challan_api: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)


def download_challan_pdf(request, challan_number):
    try:
        import pdfkit

        challan = get_object_or_404(Challan, challan_number=challan_number)

        if not challan.html_content:
            return HttpResponse('Challan content not available', status=404)

        config = pdfkit.configuration(
            wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        )

        fixed_html = challan.html_content.replace(
            '.page-container {',
            '.page-container { display: table !important; width: 120% !important; border-collapse: separate; border-spacing: 5px;'
        ).replace(
            '.challan-copy {',
            '.challan-copy { display: table-cell !important; width: 33% !important; vertical-align: top;'
        ).replace(
            '.header-section {',
            '.header-section { display: table !important; width: 100% !important;'
        ).replace(
            '.college-name {',
            '.college-name { display: table-cell !important; vertical-align: middle !important;'
        ).replace(
            '.logo-container {',
            '.logo-container { display: table-cell !important; width: 38px !important; vertical-align: middle !important;'
        )
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '5mm',
            'margin-right': '5mm',
            'margin-bottom': '5mm',
            'margin-left': '5mm',
            'enable-local-file-access': None,
            'print-media-type': None,
        }

        pdf = pdfkit.from_string(
            fixed_html,
            False,
            configuration=config,
            options=options
        )

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="challan_{challan_number}.pdf"'
        return response

    except Exception as e:
        print(f"PDF Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return HttpResponse(f'Error: {str(e)}', status=500)


@csrf_exempt
def check_challan_saved(request, challan_number):
    try:
        challan = Challan.objects.get(challan_number=challan_number)
        return JsonResponse({
            'success': True,
            'saved_to_db': True,
            'pdf_exists': bool(challan.challan_file),
            'pdf_url': challan.challan_file.url if challan.challan_file else None
        })
    except Challan.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Challan not found'
        }, status=404)


@csrf_exempt
def get_challan(request, challan_number):
    try:
        challan = Challan.objects.get(challan_number=challan_number)
        student = challan.student
        fee_heads = []
        for fee_head in challan.challanfeehead_set.all():
            fee_heads.append(f"{fee_head.fee_head_account.fee_head_name}: Rs.{fee_head.amount}")

        return JsonResponse({
            'challan_number': challan.challan_number,
            'student_name': student.name,
            'roll_number': student.college_roll_no,
            'shift': student.status,
            'disciplines': challan.disciplines,
            'semesters': challan.semesters,
            'session': challan.student.scheme_of_study.session.year if challan.student.scheme_of_study else '',
            'fee_heads': ', '.join(fee_heads),
            'amount': str(challan.challan_amount),
            'due_date': challan.due_date.strftime('%d/%m/%Y') if challan.due_date else '',
            'one_bill_number': challan.one_bill_number or 'Pending'
        })
    except Challan.DoesNotExist:
        return JsonResponse({'error': 'Challan not found'}, status=404)


@csrf_exempt
def get_active_logo_api(request):
    try:
        active_logo = get_active_logo()
        if active_logo:
            return JsonResponse({
                'success': True,
                'logo_url': active_logo.logo.url if active_logo.logo else "/static/feeapp/images/logo_college.jpg",
                'college_name': active_logo.college_name
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No active logo found'
            }, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def challan_preview(request):
    if request.method == 'POST':
        cnic = request.POST.get('cnic', '')
        try:
            challan = Challan.objects.get(student__cnic_no=cnic)
            return render(request, 'feeapp/challan_preview.html', {'challan': challan})
        except Challan.DoesNotExist:
            return render(request, 'feeapp/challan_not_found.html')
    else:
        return redirect('feeapp:download_challan')


def download_challan(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/download_challan.html', {'active_logo': active_logo})

    student_id = request.session['student_id']
    student = RegisteredStudent.objects.get(id=student_id)

    if request.method == 'POST':
        cnic = request.POST.get('cnic', '')
        normalized_cnic = ''.join(filter(str.isdigit, cnic))
        normalized_student_cnic = ''.join(filter(str.isdigit, student.cnic_no))

        if normalized_cnic != normalized_student_cnic:
            messages.error(request, "CNIC doesn't match your account. Please try again.")
            return render(request, 'feeapp/download_challan.html')

        try:
            challan = Challan.objects.filter(student=student).order_by('-challan_generation_date').first()
            if challan:
                return render(request, 'feeapp/challan_preview.html', {'challan': challan})
            else:
                return render(request, 'feeapp/challan_not_found.html')
        except Exception as e:
            messages.error(request, f"Error retrieving challan: {str(e)}")
            return render(request, 'feeapp/download_challan.html')
    else:
        return render(request, 'feeapp/download_challan.html')


@csrf_exempt
def search_challans_by_cnic(request):
    cnic = request.GET.get('cnic', '').strip()

    if not cnic:
        return JsonResponse({
            'success': False,
            'message': 'CNIC is required.'
        }, status=400)

    cnic_entered = re.sub(r'\D', '', cnic)

    try:
        student = RegisteredStudent.objects.get(cnic_no=cnic_entered)
    except RegisteredStudent.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': ' Student not found with this CNIC number.'
        }, status=404)

    check_and_apply_arrears(student)

    challans = Challan.objects.filter(student=student).order_by('-challan_generation_date')

    challans_data = []
    for challan in challans:
        if challan.payment_status == 'PAID' or challan.status.upper() == 'PAID':
            status = 'PAID'
        else:
            status = 'UNPAID'

        challans_data.append({
            'challan_number': challan.challan_number,
            'amount': str(challan.challan_amount),
            'due_date': challan.due_date.strftime('%d/%m/%Y') if challan.due_date else 'N/A',
            'generation_date': challan.challan_generation_date.strftime('%d/%m/%Y') if challan.challan_generation_date else 'N/A',
            'status': status,
            'disciplines': challan.disciplines or 'N/A',
            'semesters': challan.semesters or 'N/A',
            'session': student.scheme_of_study.session.year if student.scheme_of_study and student.scheme_of_study.session else 'N/A',
            'has_file': bool(challan.challan_file),
        })

    program_name = 'N/A'
    if student.scheme_of_study and student.scheme_of_study.program:
        program_name = student.scheme_of_study.program.heading

    return JsonResponse({
        'success': True,
        'student_name': student.name,
        'cnic': student.cnic_no,
        'roll_number': student.college_roll_no,
        'program': program_name,
        'challans': challans_data,
        'total_challans': len(challans_data)
    })


@csrf_exempt
def view_challan_html(request, challan_number):
    try:
        challan = get_object_or_404(Challan, challan_number=challan_number)

        check_and_apply_arrears(challan.student)
        challan.refresh_from_db()

        if challan.html_content:
            return HttpResponse(challan.html_content, content_type='text/html')
        elif challan.challan_file:
            return HttpResponse(challan.challan_file.read(), content_type='text/html')
        else:
            return HttpResponse('Challan content not available', status=404)

    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


def view_challan(request):
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/view_challan.html', {'active_logo': active_logo})


def search_challan(request):
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/search_challan.html', {'active_logo': active_logo})


@csrf_exempt
def get_my_challans(request):
    if 'student_id' not in request.session:
        return JsonResponse({
            'success': False,
            'message': 'You are not logged in. Please log in first.'
        }, status=401)

    try:
        student = RegisteredStudent.objects.get(id=request.session['student_id'])
    except RegisteredStudent.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please log in again.'
        }, status=401)

    check_and_apply_arrears(student)

    challans = Challan.objects.filter(
        student=student
    ).order_by('-challan_generation_date', '-challan_generation_time')

    challans_data = []
    for challan in challans:
        is_paid = (
            challan.payment_status == 'PAID' or
            challan.status.upper() == 'PAID'
        )

        challans_data.append({
            'challan_number': challan.challan_number,
            'amount': str(challan.challan_amount),
            'due_date': challan.due_date.strftime('%d/%m/%Y') if challan.due_date else 'N/A',
            'generation_date': challan.challan_generation_date.strftime('%d/%m/%Y') if challan.challan_generation_date else 'N/A',
            'status': 'PAID' if is_paid else 'UNPAID',
            'disciplines': challan.disciplines or 'N/A',
            'semesters': challan.semesters or 'N/A',
        })

    program_name = 'N/A'
    if student.scheme_of_study and student.scheme_of_study.program:
        program_name = student.scheme_of_study.program.heading

    return JsonResponse({
        'success': True,
        'student_name': student.name,
        'roll_number': student.college_roll_no,
        'program': program_name,
        'challans': challans_data,
        'total_challans': len(challans_data),
    })


# ─────────────────────────────────────────────────────────────────────────────
# CHALLAN UPDATE
# ─────────────────────────────────────────────────────────────────────────────

def update_challan(request):
    active_logo = Logo.objects.filter(is_active=True).first()
    return render(request, 'feeapp/update_challan.html', {'active_logo': active_logo})


@csrf_exempt
def get_challan_data(request, challan_number):
    try:
        challan = Challan.objects.get(challan_number=challan_number)

        return JsonResponse({
            'challan_number': challan.challan_number,
            'amount': str(challan.challan_amount),
            'due_date': challan.due_date.strftime('%Y-%m-%d') if challan.due_date else '',
            'status': challan.status
        })
    except Challan.DoesNotExist:
        return JsonResponse({'error': 'Challan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def update_challan_api(request):
    try:
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request path: {request.path}")
        print(f"DEBUG: Content-Type: {request.content_type}")

        if not request.body:
            return JsonResponse({
                'error': 'Empty request body'
            }, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {str(e)}")
            print(f"DEBUG: Request body: {request.body}")
            return JsonResponse({
                'error': 'Invalid JSON format in request body'
            }, status=400)

        challan_number = data.get('challanNumber', '').strip()
        amount = data.get('amount', '').strip()
        due_date_str = data.get('dueDate', '').strip()
        status = data.get('status', '').strip()

        print(f"DEBUG: Received data - challan: {challan_number}, amount: {amount}, due_date: {due_date_str}, status: {status}")

        if not challan_number:
            return JsonResponse({
                'error': 'Challan number is required.'
            }, status=400)

        if not amount and not due_date_str and not status:
            return JsonResponse({
                'error': 'Please provide at least one field to update: amount, due date, or status.'
            }, status=400)

        try:
            challan = Challan.objects.get(challan_number__iexact=challan_number)
            print(f"DEBUG: Found challan: {challan.challan_number}")
        except Challan.DoesNotExist:
            print(f"DEBUG: Challan not found: {challan_number}")
            sample_challans = list(Challan.objects.values_list('challan_number', flat=True)[:5])
            print(f"DEBUG: Sample challans in DB: {sample_challans}")
            return JsonResponse({
                'error': f'Challan {challan_number} not found in database.'
            }, status=404)
        except Exception as e:
            print(f"DEBUG: Error querying challan: {str(e)}")
            return JsonResponse({
                'error': f'Database error: {str(e)}'
            }, status=500)
        is_paid = (
            challan.payment_status == 'PAID' or
            challan.status.upper() == 'PAID'
        )
        if is_paid:
            print(f"DEBUG: Challan {challan_number} is already PAID. Update blocked.")
            return JsonResponse({
                'error': 'This challan is already PAID. No updates are allowed on a paid challan.'
            }, status=400)

        updated_fields = []

        if amount:
            try:
                amount_decimal = Decimal(amount)
                if amount_decimal <= 0:
                    return JsonResponse({
                        'error': 'Amount must be greater than zero.'
                    }, status=400)
                challan.challan_amount = amount_decimal
                if challan.payment_status != 'PAID':
                    challan.remaining_amount = amount_decimal
                updated_fields.append(f'Amount: Rs.{amount_decimal}')
                print(f"DEBUG: Updated amount to {amount_decimal}")
            except (ValueError, TypeError) as e:
                print(f"DEBUG: Amount error: {str(e)}")
                return JsonResponse({
                    'error': f'Invalid amount: {str(e)}'
                }, status=400)

        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                challan.due_date = due_date
                updated_fields.append(f'Due Date: {due_date.strftime("%d/%m/%Y")}')
                print(f"DEBUG: Updated due date to {due_date}")
            except ValueError as e:
                print(f"DEBUG: Due date error: {str(e)}")
                return JsonResponse({
                    'error': f'Invalid due date format: {str(e)}'
                }, status=400)

        if status:
            status_upper = status.upper()
            if status_upper not in ['PAID', 'UNPAID']:
                return JsonResponse({
                    'error': 'Status must be either "Paid" or "Unpaid".'
                }, status=400)
            challan.status = status
            updated_fields.append(f'Status: {status}')
            print(f"DEBUG: Updated status to {status}")

            if status_upper == 'PAID':
                challan.payment_status = 'PAID'
                challan.remaining_amount = 0
            else:
                challan.payment_status = 'UNPAID'
                if challan.challan_amount:
                    challan.remaining_amount = challan.challan_amount

        try:
            with transaction.atomic():
                student = challan.student

                updated_html = regenerate_challan_html_after_update(
                    challan=challan,
                    student=student,
                    new_amount=float(challan.challan_amount),
                    new_due_date=challan.due_date,
                    new_status=challan.status
                )

                challan.html_content = updated_html
                challan.challan_file.save(
                    f"{challan.challan_number}.html",
                    ContentFile(updated_html.encode('utf-8')),
                    save=False
                )

                challan.save()
                print(f"DEBUG: Successfully saved challan {challan.challan_number}")
        except Exception as e:
            print(f"DEBUG: Save error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'error': f'Failed to save changes: {str(e)}'
            }, status=500)

        fields_text = ', '.join(updated_fields)
        return JsonResponse({
            'message': f'Challan {challan.challan_number} updated successfully! Updated: {fields_text}'
        })

    except Exception as e:
        print(f'DEBUG: Unexpected error: {str(e)}')
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)


def regenerate_challan_html_after_update(challan, student, new_amount, new_due_date, new_status):
    try:
        active_logo = get_active_logo()
        college_name = active_logo.college_name if active_logo else "Government Graduate College, Civil Lines Sheikhupura"
        logo_base64 = get_logo_base64()
        formatted_due_date = new_due_date.strftime('%d/%m/%Y')
        session_year = student.scheme_of_study.session.year if student.scheme_of_study else 'N/A'

        fee_table_rows = ""
        for fee_head in challan.challanfeehead_set.all():
            fee_table_rows += f"<tr><td>{fee_head.fee_head_account.fee_head_name}</td><td>{float(fee_head.amount):,.2f}</td></tr>\n"

        status_label = ""
        if new_status.upper() == 'PAID':
            status_label = '<div style="text-align:center;color:green;font-weight:bold;font-size:14px;margin:4px 0;">STATUS: PAID</div>'

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fee Challan - {challan.challan_number}</title>
    <meta charset="UTF-8">
    <style>
        @page {{ size: 297mm 210mm; margin: 5mm; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Times New Roman', serif; font-size: 14px; background: #fff; }}
        .page-container {{ width: 100%; display: flex; flex-direction: row; gap: 15px; justify-content: left; align-items: flex-start; }}
        .challan-copy {{ width: 460px; min-height: 800px; max-height: 850px; border: 2px solid black; padding: 15px; box-sizing: border-box; background: white; overflow: hidden; display: flex; flex-direction: column; flex-shrink: 0; }}
        .copy-label {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #1e3a8a; flex-shrink: 0; }}
        .header-section {{ display: flex; align-items: center; justify-content: left; gap: 8px; margin-bottom: 4px; flex-shrink: 0; }}
        .logo-container {{ width: 35px; height: 35px; border-radius: 50%; overflow: hidden; display: flex; align-items: left; justify-content: left; }}
        .logo-container img {{ width: 100%; height: 100%; border-radius: 50%; }}
        .college-name {{ font-weight: bold; font-size: 14px; margin: 0; }}
        .challan-number {{ text-align: right; font-size: 12px; margin: 3px 0; flex-shrink: 0; }}
        .program-info {{ text-align: center; font-size: 12px; margin: 2px 0; flex-shrink: 0; }}
        .challan-copy hr {{ border: none; border-top: 1px solid black; margin: 5px 0; flex-shrink: 0; }}
        .student-info {{ font-size: 13px; margin: 3px 0; flex-shrink: 0; }}
        .date-box {{ text-align: right; font-size: 12px; margin: 1px 0; flex-shrink: 0; }}
        .fee-details {{ font-size: 12px; margin: 10px 0; flex-shrink: 0; }}
        .fee-details strong {{ font-size: 12px; display: block; margin-bottom: 5px; }}
        .fee-table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
        .fee-table th {{ border: 1px solid black; padding: 5px; text-align: center; background-color: #f0f0f0; font-weight: bold; }}
        .fee-table td {{ border: 1px solid black; padding: 5px 8px; word-wrap: break-word; text-align: center; }}
        .fee-table td:first-child {{ width: 60%; }} .fee-table td:last-child {{ width: 40%; }}
        .amount-box {{ text-align: right; font-size: 12px; margin: 10px 0; font-weight: bold; flex-shrink: 0; }}
        .instructions {{ border: 2px solid black; padding: 8px; font-size: 12px; margin: 1px 0; line-height: 1.4; flex-shrink: 0; background-color: white; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        .footer-note {{ font-style: italic; font-size: 11px; margin: 5px 0; flex-shrink: 0; }}
        .signature-line {{ font-size: 12px; margin-top: auto; padding-top: 10px; flex-shrink: 0; }}
        @media print {{
            .page-container {{ display: table !important; width: 100% !important; border-collapse: separate; border-spacing: 2mm; }}
            .challan-copy {{ display: table-cell !important; width: 460mm !important; min-height: auto !important; max-height: 220mm !important; padding: 3mm !important; vertical-align: top; border: 1.5px solid black; }}
            .instructions {{ border: 2px solid black; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="page-container">

        <div class="challan-copy">
            <div class="copy-label">Student Copy</div>
            {status_label}
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box"><strong>Total Amount: Rs. {new_amount:,.2f}</strong></div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">Bank Copy</div>
            {status_label}
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box"><strong>Total Amount: Rs. {new_amount:,.2f}</strong></div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">College Copy</div>
            {status_label}
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box"><strong>Total Amount: Rs. {new_amount:,.2f}</strong></div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM orany Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

    </div>
</body>
</html>"""

        return html_content

    except Exception as e:
        print(f"Error regenerating HTML: {str(e)}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# AUTOMATIC ARREARS SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

def check_and_apply_arrears(student):
    today = datetime.now().date()

    base_challans = Challan.objects.filter(
        student=student,
        original_total_amount__isnull=False
    ).exclude(
        challan_number__contains='-'
    )

    for base_challan in base_challans:
        installments = Installment.objects.filter(
            original_challan=base_challan
        ).order_by('installment_number')

        if installments.count() < 2:
            continue

        inst_1 = None
        inst_2 = None
        for inst in installments:
            if inst.installment_number == 1:
                inst_1 = inst
            elif inst.installment_number == 2:
                inst_2 = inst

        if not inst_1 or not inst_2:
            continue

        if inst_1.status == 'UNPAID' and inst_1.due_date < today:
            second_challan = inst_2.installment_challan

            original_inst2_amount = float(inst_2.amount)
            arrears_amount = float(inst_1.amount)
            expected_total = original_inst2_amount + arrears_amount
            current_second_amount = float(second_challan.challan_amount)

            if current_second_amount >= expected_total:
                continue

            try:
                with transaction.atomic():
                    new_total = original_inst2_amount + arrears_amount

                    second_challan.challan_amount = new_total
                    second_challan.remaining_amount = new_total

                    updated_html = regenerate_challan_html_with_arrears(
                        challan=second_challan,
                        student=student,
                        original_inst2_amount=original_inst2_amount,
                        arrears_amount=arrears_amount,
                        new_total=new_total,
                        first_challan_number=inst_1.installment_challan.challan_number
                    )

                    second_challan.html_content = updated_html
                    second_challan.challan_file.save(
                        f"{second_challan.challan_number}.html",
                        ContentFile(updated_html.encode('utf-8')),
                        save=False
                    )
                    second_challan.save()

                    print(f"ARREARS APPLIED: Challan {second_challan.challan_number} | "
                          f"Arrears from {inst_1.installment_challan.challan_number}: Rs.{arrears_amount} | "
                          f"New Total: Rs.{new_total}")

            except Exception as e:
                print(f"ERROR applying arrears for challan {second_challan.challan_number}: {str(e)}")
                import traceback
                print(traceback.format_exc())


def regenerate_challan_html_with_arrears(challan, student, original_inst2_amount, arrears_amount, new_total, first_challan_number):
    try:
        active_logo = get_active_logo()
        college_name = active_logo.college_name if active_logo else "Government Graduate College, Civil Lines Sheikhupura"
        logo_base64 = get_logo_base64()
        formatted_due_date = challan.due_date.strftime('%d/%m/%Y') if challan.due_date else ''
        session_year = student.scheme_of_study.session.year if student.scheme_of_study else ''

        fee_table_rows = ""
        for fh in challan.challanfeehead_set.all():
            fee_table_rows += f"<tr><td>{fh.fee_head_account.fee_head_name}</td><td>{float(fh.amount):,.2f}</td></tr>\n"
        fee_table_rows += f"<tr><td><strong>Arrears (from Challan {first_challan_number})</strong></td><td><strong>{arrears_amount:,.2f}</strong></td></tr>\n"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fee Challan - {challan.challan_number} (with Arrears)</title>
    <meta charset="UTF-8">
    <style>
        @page {{ size: 297mm 210mm; margin: 5mm; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Times New Roman', serif; font-size: 14px; background: #fff; }}
        .page-container {{ width: 100%; display: flex; flex-direction: row; gap: 15px; justify-content: left; align-items: flex-start; }}
        .challan-copy {{ width: 460px; min-height: 800px; max-height: 850px; border: 2px solid black; padding: 15px; box-sizing: border-box; background: white; overflow: hidden; display: flex; flex-direction: column; flex-shrink: 0; }}
        .copy-label {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #1e3a8a; flex-shrink: 0; }}
        .header-section {{ display: flex; align-items: center; justify-content: left; gap: 8px; margin-bottom: 4px; flex-shrink: 0; }}
        .logo-container {{ width: 35px; height: 35px; border-radius: 50%; overflow: hidden; display: flex; align-items: left; justify-content: left; }}
        .logo-container img {{ width: 100%; height: 100%; border-radius: 50%; }}
        .college-name {{ font-weight: bold; font-size: 14px; margin: 0; }}
        .challan-number {{ text-align: right; font-size: 12px; margin: 3px 0; flex-shrink: 0; }}
        .program-info {{ text-align: center; font-size: 12px; margin: 2px 0; flex-shrink: 0; }}
        .challan-copy hr {{ border: none; border-top: 1px solid black; margin: 5px 0; flex-shrink: 0; }}
        .student-info {{ font-size: 13px; margin: 3px 0; flex-shrink: 0; }}
        .date-box {{ text-align: right; font-size: 12px; margin: 1px 0; flex-shrink: 0; }}
        .fee-details {{ font-size: 12px; margin: 10px 0; flex-shrink: 0; }}
        .fee-details strong {{ font-size: 12px; display: block; margin-bottom: 5px; }}
        .fee-table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
        .fee-table th {{ border: 1px solid black; padding: 5px; text-align: center; background-color: #f0f0f0; font-weight: bold; }}
        .fee-table td {{ border: 1px solid black; padding: 5px 8px; word-wrap: break-word; text-align: center; }}
        .fee-table td:first-child {{ width: 60%; }} .fee-table td:last-child {{ width: 40%; }}
        .amount-box {{ text-align: right; font-size: 12px; margin: 10px 0; font-weight: bold; flex-shrink: 0; }}
        .instructions {{ border: 2px solid black; padding: 8px; font-size: 12px; margin: 1px 0; line-height: 1.4; flex-shrink: 0; background-color: white; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        .footer-note {{ font-style: italic; font-size: 11px; margin: 5px 0; flex-shrink: 0; }}
        .signature-line {{ font-size: 12px; margin-top: auto; padding-top: 10px; flex-shrink: 0; }}
        @media print {{
            .page-container {{ display: table !important; width: 100% !important; border-collapse: separate; border-spacing: 2mm; }}
            .challan-copy {{ display: table-cell !important; width: 460mm !important; min-height: auto !important; max-height: 240mm !important; padding: 3mm !important; vertical-align: top; border: 1.5px solid black; }}
            .instructions {{ border: 2px solid black; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="page-container">

        <div class="challan-copy">
            <div class="copy-label">Student Copy - Final Installment</div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
            <strong>Installment Due Amount: Rs. {original_inst2_amount:,.2f}</strong><br>
            <strong>Total Due Amount: Rs. {new_total:,.2f}</strong>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">Bank Copy - Final Installment</div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
    <strong>Installment Due Amount: Rs. {original_inst2_amount:,.2f}</strong><br>
    <strong>Total Due Amount: Rs. {new_total:,.2f}</strong>
</div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">College Copy - Final Installment</div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
    <strong>Installment Due Amount: Rs. {original_inst2_amount:,.2f}</strong><br>
    <strong>Total Due Amount: Rs. {new_total:,.2f}</strong>
</div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

    </div>
</body>
</html>"""

        return html_content

    except Exception as e:
        print(f"Error in regenerate_challan_html_with_arrears: {str(e)}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# INSTALLMENT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@ensure_csrf_cookie
@login_required(login_url='clerk_login')
def manage_installment(request):
    active_logo = Logo.objects.filter(is_active=True).first()
    if request.method == 'POST':

        if 'cnic' in request.POST and 'challan_num' in request.POST and 'create_installments' not in request.POST:
            cnic_input = request.POST.get('cnic', '').strip()
            challan_input = request.POST.get('challan_num', '').strip()

            cnic_normalized = re.sub(r'\D', '', cnic_input)

            try:
                student = RegisteredStudent.objects.get(cnic_no=cnic_normalized)
                print(f"DEBUG: Found student: {student.name}")

                base_challan_num = challan_input.split('-')[0]
                challan = Challan.objects.get(
                    challan_number=base_challan_num,
                    student=student
                )
                print(f"DEBUG: Found challan: {challan.challan_number}")

                if challan.original_total_amount is None:
                    challan.original_total_amount = challan.challan_amount
                    challan.save()

                existing_installs = Installment.objects.filter(
                    original_challan=challan
                ).order_by('installment_number')

                if existing_installs.count() >= 2:
                    messages.error(request, "Both installments already created!")
                    return redirect('manage_installment')

                original_total = float(challan.original_total_amount)
                paid_so_far = sum(float(inst.amount) for inst in existing_installs)
                current_remaining = original_total - paid_so_far

                program_name = 'N/A'
                if student.scheme_of_study and student.scheme_of_study.program:
                    program_name = student.scheme_of_study.program.heading

                context = {
                    'screen': 'screen2',
                    'student': {
                        'student_name': student.name,
                        'cnic_student': student.cnic_no,
                        'college_roll_number': student.college_roll_no,
                        'program': {'ProgramName': program_name}
                    },
                    'challan': challan,
                    'existing_installs': existing_installs,
                    'remaining': current_remaining,
                    'cnic_input': cnic_input,
                    'challan_input': challan_input,
                    'active_logo': active_logo,
                }

                return render(request, 'feeapp/manage-installment.html', context)

            except RegisteredStudent.DoesNotExist:
                messages.error(request, "Student not found with this CNIC!")
            except Challan.DoesNotExist:
                messages.error(request, "Challan not found or does not belong to this student!")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                print(f"DEBUG: Error: {str(e)}")
                import traceback
                print(traceback.format_exc())

            return redirect('manage_installment')

        elif 'create_installments' in request.POST:
            challan_num = request.POST.get('challan_num')
            first_amount = request.POST.get('first_amount', '').strip()
            first_due_date_str = request.POST.get('first_due_date', '').strip()
            second_due_date_str = request.POST.get('second_due_date', '').strip()
            cnic_input = request.POST.get('cnic_original', '')
            challan_input = request.POST.get('challan_original', challan_num)

            if not first_amount or not first_due_date_str or not second_due_date_str:
                messages.error(request, "Please fill all required fields!")
                return redirect('manage_installment')

            try:
                first_amount = Decimal(first_amount)
                if first_amount <= 0:
                    messages.error(request, "First installment amount must be greater than zero!")
                    return redirect('manage_installment')

                first_due_date = datetime.strptime(first_due_date_str, '%Y-%m-%d').date()
                second_due_date = datetime.strptime(second_due_date_str, '%Y-%m-%d').date()

                today = datetime.now().date()
                if first_due_date < today:
                    messages.error(request, "First installment due date cannot be in the past!")
                    return redirect('manage_installment')
                if second_due_date < today:
                    messages.error(request, "Second installment due date cannot be in the past!")
                    return redirect('manage_installment')

                if first_due_date.weekday() in [5, 6]:
                    messages.error(request, "First installment due date cannot be Saturday or Sunday!")
                    return redirect('manage_installment')
                if second_due_date.weekday() in [5, 6]:
                    messages.error(request, "Second installment due date cannot be Saturday or Sunday!")
                    return redirect('manage_installment')

                if second_due_date <= first_due_date:
                    messages.error(request, "Second installment due date must be after first installment!")
                    return redirect('manage_installment')

                challan = Challan.objects.get(challan_number=challan_num)
                student = challan.student

                clerk = None
                if request.user.is_authenticated:
                    try:
                        clerk = Clerk.objects.get(user=request.user)
                    except Clerk.DoesNotExist:
                        pass

                with transaction.atomic():
                    original_total = float(challan.original_total_amount or challan.challan_amount)

                    first_amount_float = float(first_amount)
                    second_amount_float = original_total - first_amount_float

                    if second_amount_float <= 0:
                        messages.error(request, "First installment cannot be equal to or greater than total amount!")
                        return redirect('manage_installment')

                    if not challan.original_total_amount:
                        challan.original_total_amount = original_total

                    challan.challan_amount = first_amount_float
                    challan.due_date = first_due_date
                    challan.payment_status = 'PARTIALLY_PAID'
                    challan.download_status = 'PENDING'
                    challan.remaining_amount = second_amount_float

                    if clerk:
                        challan.created_by_clerk = clerk

                    updated_html = regenerate_challan_html_with_new_amount(
                        challan=challan,
                        student=student,
                        new_amount=first_amount_float,
                        new_due_date=first_due_date,
                        remaining_amount=second_amount_float
                    )

                    challan.html_content = updated_html
                    challan.challan_file.save(
                        f"{challan_num}.html",
                        ContentFile(updated_html.encode('utf-8')),
                        save=False
                    )
                    challan.save()

                    Installment.objects.create(
                        original_challan=challan,
                        installment_challan=challan,
                        installment_number=1,
                        amount=first_amount_float,
                        due_date=first_due_date,
                    )

                    second_challan_num = f"{challan_num}-2"
                    second_challan = create_installment_challan(
                        original_challan=challan,
                        student=student,
                        installment_amount=Decimal(str(second_amount_float)),
                        installment_due_date=second_due_date,
                        new_challan_number=second_challan_num,
                        installment_label="Final Installment",
                        remaining_amount=0
                    )

                    if clerk:
                        second_challan.created_by_clerk = clerk
                        second_challan.save()

                    Installment.objects.create(
                        original_challan=challan,
                        installment_challan=second_challan,
                        installment_number=2,
                        amount=second_amount_float,
                        due_date=second_due_date,
                    )

                    challan.payment_status = 'PARTIALLY_PAID'
                    challan.save(update_fields=['payment_status'])

                messages.success(request, "Both installments created successfully!")

                all_installments = Installment.objects.filter(
                    original_challan=challan
                ).order_by('installment_number')

                program_name = 'N/A'
                if student.scheme_of_study and student.scheme_of_study.program:
                    program_name = student.scheme_of_study.program.heading

                context = {
                    'screen': 'screen3',
                    'student': {
                        'student_name': student.name,
                        'cnic_student': student.cnic_no,
                        'college_roll_number': student.college_roll_no,
                        'program': {'ProgramName': program_name}
                    },
                    'challan': challan,
                    'all_installments': all_installments,
                    'original_total': original_total,
                    'remaining': 0,
                    'cnic_input': cnic_input,
                    'challan_input': challan_input,
                    'active_logo': active_logo,
                }
                return render(request, 'feeapp/manage-installment.html', context)

            except Exception as e:
                messages.error(request, f"Error creating installments: {str(e)}")
                print(f"DEBUG: Error: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return redirect('manage_installment')

    return render(request, 'feeapp/manage-installment.html', {'screen': 'screen1', 'active_logo': active_logo, })


def regenerate_challan_html_with_new_amount(challan, student, new_amount, new_due_date, remaining_amount):
    try:
        active_logo = get_active_logo()
        college_name = active_logo.college_name if active_logo else "Government Graduate College, Civil Lines Sheikhupura"
        logo_base64 = get_logo_base64()
        formatted_due_date = new_due_date.strftime('%d/%m/%Y')
        session_year = student.scheme_of_study.session.year if student.scheme_of_study else 'N/A'

        fee_table_rows = ""
        for fee_head in challan.challanfeehead_set.all():
            fee_table_rows += f"<tr><td>{fee_head.fee_head_account.fee_head_name}</td><td>{float(fee_head.amount):,.2f}</td></tr>\n"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fee Challan - {challan.challan_number}</title>
    <meta charset="UTF-8">
    <style>
        @page {{ size: 297mm 210mm; margin: 5mm; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Times New Roman', serif; font-size: 14px; background: #fff; }}
        .page-container {{ width: 100%; display: flex; flex-direction: row; gap: 15px; justify-content: left; align-items: flex-start; }}
        .challan-copy {{ width: 460px; min-height: 800px; max-height: 850px; border: 2px solid black; padding: 15px; box-sizing: border-box; background: white; overflow: hidden; display: flex; flex-direction: column; flex-shrink: 0; }}
        .copy-label {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #1e3a8a; flex-shrink: 0; }}
        .header-section {{ display: flex; align-items: center; justify-content: left; gap: 8px; margin-bottom: 4px; flex-shrink: 0; }}
        .logo-container {{ width: 35px; height: 35px; border-radius: 50%; overflow: hidden; display: flex; align-items: left; justify-content: left; }}
        .logo-container img {{ width: 100%; height: 100%; border-radius: 50%; }}
        .college-name {{ font-weight: bold; font-size: 14px; margin: 0; }}
        .challan-number {{ text-align: right; font-size: 12px; margin: 3px 0; flex-shrink: 0; }}
        .program-info {{ text-align: center; font-size: 12px; margin: 2px 0; flex-shrink: 0; }}
        .challan-copy hr {{ border: none; border-top: 1px solid black; margin: 5px 0; flex-shrink: 0; }}
        .student-info {{ font-size: 13px; margin: 3px 0; flex-shrink: 0; }}
        .date-box {{ text-align: right; font-size: 12px; margin: 1px 0; flex-shrink: 0; }}
        .fee-details {{ font-size: 12px; margin: 10px 0; flex-shrink: 0; }}
        .fee-details strong {{ font-size: 12px; display: block; margin-bottom: 5px; }}
        .fee-table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
        .fee-table th {{ border: 1px solid black; padding: 5px; text-align: center; background-color: #f0f0f0; font-weight: bold; }}
        .fee-table td {{ border: 1px solid black; padding: 5px 8px; word-wrap: break-word; text-align: center; }}
        .fee-table td:first-child {{ width: 60%; }} .fee-table td:last-child {{ width: 40%; }}
        .amount-box {{ text-align: right; font-size: 12px; margin: 10px 0; font-weight: bold; flex-shrink: 0; }}
        .instructions {{ border: 2px solid black; padding: 8px; font-size: 12px; margin: 1px 0; line-height: 1.4; flex-shrink: 0; background-color: white; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        .footer-note {{ font-style: italic; font-size: 11px; margin: 5px 0; flex-shrink: 0; }}
        .signature-line {{ font-size: 12px; margin-top: auto; padding-top: 10px; flex-shrink: 0; }}
        .remaining-amount {{ font-weight: bold; }}
        @media print {{
            .page-container {{ display: table !important; width: 100% !important; border-collapse: separate; border-spacing: 2mm; }}
            .challan-copy {{ display: table-cell !important; width: 460mm !important; min-height: auto !important; max-height: 240mm !important; padding: 3mm !important; vertical-align: top; border: 1.5px solid black; }}
            .instructions {{ border: 2px solid black; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
    </style>
</head
<body>
    <div class="page-container">

        <div class="challan-copy">
            <div class="copy-label">Student Copy - First Installment </div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Installment Due Amount: Rs. {new_amount:,.2f}</strong><br>
                <span class="remaining-amount">Remaining Amount: Rs. {remaining_amount:,.2f}</span>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or ''}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">Bank Copy - First Installment </div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Installment Due Amount: Rs. {new_amount:,.2f}</strong><br>
                <span class="remaining-amount">Remaining Amount: Rs. {remaining_amount:,.2f}</span>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or ''}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">College Copy - First Installment </div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{challan.disciplines} - {challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Installment Due Amount: Rs. {new_amount:,.2f}</strong><br>
                <span class="remaining-amount">Remaining Amount: Rs. {remaining_amount:,.2f}</span>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or ''}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

    </div>
</body>
</html>"""

        return html_content

    except Exception as e:
        print(f"Error regenerating HTML: {str(e)}")
        raise


def create_installment_challan(original_challan, student, installment_amount, installment_due_date, new_challan_number, installment_label, remaining_amount):
    try:
        active_logo = get_active_logo()
        college_name = active_logo.college_name if active_logo else "Government Graduate College, Civil Lines, Sheikhupura"
        logo_base64 = get_logo_base64()

        if isinstance(installment_due_date, str):
            due_date_obj = datetime.strptime(installment_due_date, '%Y-%m-%d').date()
        else:
            due_date_obj = installment_due_date

        formatted_due_date = due_date_obj.strftime('%d/%m/%Y')
        session_year = student.scheme_of_study.session.year if student.scheme_of_study else 'N/A'

        fee_table_rows = ""
        for fee_head in original_challan.challanfeehead_set.all():
            fee_table_rows += f"<tr><td>{fee_head.fee_head_account.fee_head_name}</td><td>{float(fee_head.amount):,.2f}</td></tr>\n"
        new_onelink_number = OneLinkService.generate_consumer_number(student, float(installment_amount))

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fee Challan - {new_challan_number}</title>
    <meta charset="UTF-8">
    <style>
        @page {{ size: 297mm 210mm; margin: 5mm; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Times New Roman', serif; font-size: 14px; background: #fff; }}
        .page-container {{ width: 100%; display: flex; flex-direction: row; gap: 15px; justify-content: left; align-items: flex-start; }}
        .challan-copy {{ width: 460px; min-height: 800px; max-height: 850px; border: 2px solid black; padding: 15px; box-sizing: border-box; background: white; overflow: hidden; display: flex; flex-direction: column; flex-shrink: 0; }}
        .copy-label {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #1e3a8a; flex-shrink: 0; }}
        .header-section {{ display: flex; align-items: center; justify-content: left; gap: 8px; margin-bottom: 4px; flex-shrink: 0; }}
        .logo-container {{ width: 35px; height: 35px; border-radius: 50%; overflow: hidden; display: flex; align-items: left; justify-content: left; }}
        .logo-container img {{ width: 100%; height: 100%; border-radius: 50%; }}
        .college-name {{ font-weight: bold; font-size: 14px; margin: 0; }}
        .challan-number {{ text-align: right; font-size: 12px; margin: 3px 0; flex-shrink: 0; }}
        .program-info {{ text-align: center; font-size: 12px; margin: 2px 0; flex-shrink: 0; }}
        .challan-copy hr {{ border: none; border-top: 1px solid black; margin: 5px 0; flex-shrink: 0; }}
        .student-info {{ font-size: 13px; margin: 3px 0; flex-shrink: 0; }}
        .date-box {{ text-align: right; font-size: 12px; margin: 1px 0; flex-shrink: 0; }}
        .fee-details {{ font-size: 12px; margin: 10px 0; flex-shrink: 0; }}
        .fee-details strong {{ font-size: 12px; display: block; margin-bottom: 5px; }}
        .fee-table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
        .fee-table th {{ border: 1px solid black; padding: 5px; text-align: center; background-color: #f0f0f0; font-weight: bold; }}
        .fee-table td {{ border: 1px solid black; padding: 5px 8px; word-wrap: break-word; text-align: center; }}
        .fee-table td:first-child {{ width: 60%; }} .fee-table td:last-child {{ width: 40%; }}
        .amount-box {{ text-align: right; font-size: 12px; margin: 10px 0; font-weight: bold; flex-shrink: 0; }}
        .instructions {{ border: 2px solid black; padding: 8px; font-size: 12px; margin: 1px 0; line-height: 1.4; flex-shrink: 0; background-color: white; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        .footer-note {{ font-style: italic; font-size: 11px; margin: 5px 0; flex-shrink: 0; }}
        .signature-line {{ font-size: 12px; margin-top: auto; padding-top: 10px; flex-shrink: 0; }}
        .remaining-amount {{ font-weight: bold; }}
      @media print {{
            .page-container {{ display: table !important; width: 100%!important; border-collapse: separate; border-spacing: 2mm; }}
            .challan-copy {{ display: table-cell !important; width: 460mm !important; min-height: auto !important; max-height: 240mm !important; padding: 3mm !important; vertical-align: top; border: 1.5px solid black; }}
            .instructions {{ border: 2px solid black; white-space: nowrap; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="page-container">

        <div class="challan-copy">
            <div class="copy-label">Student Copy - {installment_label}</div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {new_challan_number}</div>
            <div class="program-info">{original_challan.disciplines} - {original_challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Installment Due Amount: Rs. {float(installment_amount):,.2f}</strong><br>
                <span class="remaining-amount">Remaining After This: Rs. {float(remaining_amount) if remaining_amount else 0:,.2f}</span>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {new_onelink_number}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">Bank Copy - {installment_label}</div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {new_challan_number}</div>
            <div class="program-info">{original_challan.disciplines} - {original_challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Installment Due Amount: Rs. {float(installment_amount):,.2f}</strong><br>
                <span class="remaining-amount">Remaining After This: Rs. {float(remaining_amount) if remaining_amount else 0:,.2f}</span>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {new_onelink_number}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________ &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stamp: _________</div>
        </div>

        <div class="challan-copy">
            <div class="copy-label">College Copy - {installment_label}</div>
            <div class="header-section">
                <div class="logo-container"><img src="{logo_base64}" alt="Logo"></div>
                <span class="college-name">{college_name}</span>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {new_challan_number}</div>
            <div class="program-info">{original_challan.disciplines} - {original_challan.semesters} - Session {session_year}</div>
            <hr>
            <div class="student-info"><strong>Student:</strong> {student.name} | <strong>Roll No:</strong> {student.college_roll_no} | <strong>Shift:</strong> {student.status.title()}</div>
            <div class="date-box"><strong>Due Date:</strong> {formatted_due_date}</div>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead><tr><th>Fee Head</th><th>Amount (Rs.)</th></tr></thead>
                    <tbody>{fee_table_rows}</tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Installment Due Amount: Rs. {float(installment_amount):,.2f}</strong><br>
                <span class="remaining-amount">Remaining After This: Rs. {float(remaining_amount) if remaining_amount else 0:,.2f}</span>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {new_onelink_number}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM or any Banking channel is not verifiable.</div>
            <div class="signature-line">Cashier: _________&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Stamp: _________</div>
        </div>

    </div>
</body>
</html>"""
        new_onelink_number = OneLinkService.generate_consumer_number(student, float(installment_amount))
        new_challan = Challan.objects.create(
            challan_number=new_challan_number,
            due_date=due_date_obj,
            challan_amount=float(installment_amount),
            status='UNPAID',
            payment_status='UNPAID',
            remaining_amount=float(remaining_amount) if remaining_amount else 0,
            challan_generation_date=datetime.now().date(),
            student=student,
            disciplines=original_challan.disciplines,
            semesters=original_challan.semesters,
            html_content=html_content,
            original_total_amount=float(original_challan.original_total_amount),
            download_status='SUSPENDED',
            one_bill_number=new_onelink_number
        )

        for fee_head in original_challan.challanfeehead_set.all():
            ChallanFeeHead.objects.create(
                fee_head_account=fee_head.fee_head_account,
                challan=new_challan,
                amount=fee_head.amount,
                date_of_generation=datetime.now().date()
            )

        new_challan.challan_file.save(
            f"{new_challan_number}.html",
            ContentFile(html_content.encode('utf-8'))
        )
        return new_challan

    except Exception as e:
        print(f"Error creating installment challan: {str(e)}")
        raise


def save_installment(request):
    if request.method == 'POST':
        cnic = request.POST.get('cnic')
        challan = request.POST.get('challan')
        original_amount = request.POST.get('original_amount')

        amt1 = request.POST.get('amt1')
        amt2 = request.POST.get('amt2')

        due1 = request.POST.get('due1')
        due2 = request.POST.get('due2')

        remaining_amount = float(original_amount) - (float(amt1 or 0) + float(amt2 or 0))

        messages.success(request, 'Installment plan saved successfully!')

        return render(request, 'feeapp/manage-installment.html', {
            'screen': 'screen3',
            'cnic': cnic,
            'challan': challan,
            'original_amount': original_amount,
            'installment1_amount': amt1,
            'installment1_due_date': due1,
            'installment2_amount': amt2,
            'installment2_due_date': due2,
            'remaining_amount': remaining_amount,
        })

    return redirect('manage_installment')


# ─────────────────────────────────────────────────────────────────────────────
# CHALLAN SUMMARY & FUND REPORT
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='clerk_login')
def challan_summary(request):
    is_admin = request.user.is_superuser or request.user.is_staff

    clerk = None
    clerk_name = ''
    clerk_id = ''

    try:
        clerk = Clerk.objects.get(user=request.user)
        clerk_name = clerk.clerk_name
        clerk_id = clerk.clerk_id
    except Clerk.DoesNotExist:
        if is_admin:
            clerk_name = request.user.get_full_name() or request.user.email
            clerk_id = 'ADMIN'
        else:
            from django.contrib.auth import logout as auth_logout
            auth_logout(request)
            return redirect('clerk_login')

    active_logo = Logo.objects.filter(is_active=True).first()

    login_history = ClerkLoginHistory.objects.select_related('user').order_by('-date', '-login_time')

    activity_history = ClerkActivityHistory.objects.select_related('clerk').filter(
        first_challan_number__isnull=False
    ).exclude(
        first_challan_number=''
    ).order_by('-date', '-time')

    all_programs = Programs.objects.all().order_by('heading')
    all_course_groups = CourseGroup.objects.all().order_by('name')

    all_semesters = (
        [f'Semester {i}' for i in range(1, 9)] +
        ['Year 1', 'Year 2']
    )

    context = {
        'active_logo':       active_logo,
        'clerk_name':        clerk_name,
        'clerk_id':          clerk_id,
        'login_history':     login_history,
        'activity_history':  activity_history,
        'all_programs':      all_programs,
        'all_course_groups': all_course_groups,
        'all_semesters':     all_semesters,
        'is_admin':          is_admin,
    }

    return render(request, 'feeapp/challan_summary.html', context)


@login_required(login_url='clerk_login')
def fund_report_api(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET request required.'}, status=405)

    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str   = request.GET.get('date_to', '').strip()
    program_id    = request.GET.get('program_id', '').strip()
    shift         = request.GET.get('shift', '').strip()
    group_id      = request.GET.get('group_id', '').strip()
    semester      = request.GET.get('semester', '').strip()

    try:
        qs = Challan.objects.all().select_related(
            'student',
            'student__scheme_of_study',
            'student__scheme_of_study__program',
            'student__scheme_of_study__session',
            'student__scheme_of_study__course_group',
        ).prefetch_related(
            'challanfeehead_set__fee_head_account'
        )

        filter_parts = []

        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            qs = qs.filter(challan_generation_date__gte=date_from)
            filter_parts.append('From: ' + date_from.strftime('%d/%m/%Y'))

        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            qs = qs.filter(challan_generation_date__lte=date_to)
            filter_parts.append('To: ' + date_to.strftime('%d/%m/%Y'))

        if program_id:
            qs = qs.filter(student__scheme_of_study__program_id=int(program_id))
            try:
                prog = Programs.objects.get(id=int(program_id))
                filter_parts.append(prog.heading)
            except Programs.DoesNotExist:
                pass

        if shift:
            qs = qs.filter(student__status=shift.lower())
            filter_parts.append(shift.title() + ' Shift')

        if group_id:
            qs = qs.filter(student__scheme_of_study__course_group_id=int(group_id))
            try:
                grp = CourseGroup.objects.get(id=int(group_id))
                filter_parts.append(grp.name)
            except CourseGroup.DoesNotExist:
                pass

        if semester:
            qs = qs.filter(semesters__icontains=semester)
            filter_parts.append(semester)

        filter_summary = ', '.join(filter_parts) if filter_parts else 'All Records'

        all_challans_list = list(qs)

        filtered_challans = [
            c for c in all_challans_list
            if '-' not in c.challan_number
        ]

        paid_challans = [
            c for c in filtered_challans
            if (c.payment_status == 'PAID' or c.status.upper() == 'PAID')
        ]
        unpaid_challans = [
            c for c in filtered_challans
            if not (c.payment_status == 'PAID' or c.status.upper() == 'PAID')
        ]

        def build_groups(challan_list):
            grouped = {}
            grand_total = 0

            for challan in challan_list:
                student = challan.student
                sos = student.scheme_of_study if student else None

                program_name = sos.program.heading    if sos and sos.program      else ''
                discipline   = sos.course_group.name  if sos and sos.course_group else (challan.disciplines or '')
                shift_val    = student.status.title() if student                  else ''
                sem_val      = challan.semesters or ''

                key = (program_name, discipline, shift_val, sem_val)

                if key not in grouped:
                    grouped[key] = {
                        'program':     program_name,
                        'discipline':  discipline,
                        'shift':       shift_val,
                        'semester':    sem_val,
                        'fee_heads':   {},
                        'group_total': 0,
                    }

                if challan.original_total_amount:
                    challan_amount = float(challan.original_total_amount)
                else:
                    challan_amount = float(challan.challan_amount)

                grand_total                 += challan_amount
                grouped[key]['group_total'] += challan_amount

                for fh_link in challan.challanfeehead_set.all():
                    fee_name   = fh_link.fee_head_account.fee_head_name
                    fee_amount = float(fh_link.amount)

                    if fee_name not in grouped[key]['fee_heads']:
                        grouped[key]['fee_heads'][fee_name] = {
                            'total_amount':  0,
                            'challan_count': 0,
                        }

                    grouped[key]['fee_heads'][fee_name]['total_amount']  += fee_amount
                    grouped[key]['fee_heads'][fee_name]['challan_count'] += 1

            groups_list = []
            for key, data in sorted(grouped.items()):
                groups_list.append({
                    'program':     data['program'],
                    'discipline':  data['discipline'],
                    'shift':       data['shift'],
                    'semester':    data['semester'],
                    'fee_heads': [
                        {
                            'fee_head_name':  name,
                            'total_amount':   round(info['total_amount'], 2),
                            'challan_count':  info['challan_count'],
                        }
                        for name, info in data['fee_heads'].items()
                    ],
                })

            return groups_list, round(grand_total, 2)

        paid_groups,   paid_grand_total   = build_groups(paid_challans)
        unpaid_groups, unpaid_grand_total = build_groups(unpaid_challans)

        return JsonResponse({
            'paid_groups':        paid_groups,
            'paid_grand_total':   paid_grand_total,
            'paid_count':         len(paid_challans),
            'unpaid_groups':      unpaid_groups,
            'unpaid_grand_total': unpaid_grand_total,
            'unpaid_count':       len(unpaid_challans),
            'filter_summary':     filter_summary,
        })

    except ValueError as e:
        return JsonResponse({'error': 'Invalid filter value: ' + str(e)}, status=400)
    except Exception as e:
        import traceback
        print('fund_report_api error:', str(e))
        print(traceback.format_exc())
        return JsonResponse({'error': 'Server error: ' + str(e)}, status=500)