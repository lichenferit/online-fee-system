from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from feeapp.models import *
from datetime import date, timedelta
from decimal import Decimal
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate database with test data for fee system'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # =====================================================
        # 1. CREATE CLERK ACCOUNT
        # =====================================================
        self.stdout.write('Creating clerk account...')
        try:
            user, created = User.objects.get_or_create(
                email='Hasanraza142@gmail.com',
                defaults={
                    'username': 'hasanraza',
                    'password': make_password('zxc12?12')
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created user: {user.email}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  User already exists: {user.email}'))
            
            clerk, created = Clerk.objects.get_or_create(
                user=user,
                defaults={
                    'clerk_id': 'CLK001',
                    'clerk_name': 'Hasan Raza',
                    'phone_number': '03001234567',
                    'position': 'Fee Clerk',
                    'cnic': '12345-1234567-1',
                    'gender': 'Male'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created clerk: {clerk.clerk_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Clerk already exists: {clerk.clerk_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating clerk: {str(e)}'))
            return

        # =====================================================
        # 2. CREATE PROGRAMS
        # =====================================================
        self.stdout.write('\nCreating programs...')
        programs_data = [
            'BS Computer Science',
            'BS Mathematics',
            'Intermediate (F.Sc)',
            'Bachelor of Arts',
        ]
        
        for prog_name in programs_data:
            prog, created = Programs.objects.get_or_create(
                heading=prog_name,
                defaults={
                    'short_description': f'Program: {prog_name}',
                    'user_id': user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created program: {prog_name}'))

        # =====================================================
        # 3. CREATE COURSE GROUPS
        # =====================================================
        self.stdout.write('\nCreating course groups...')
        programs = Programs.objects.all()
        for program in programs:
            cg, created = CourseGroup.objects.get_or_create(
                name=program.heading,
                program_id=program,
                defaults={
                    'short_description': f'Courses for {program.heading}',
                    'user_id': user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created course group: {cg.name}'))

        # =====================================================
        # 4. CREATE SESSIONS
        # =====================================================
        self.stdout.write('\nCreating sessions...')
        sessions_data = ['2023-2024', '2024-2025', '2025-2026']
        for sess_year in sessions_data:
            sess, created = Session.objects.get_or_create(year=sess_year)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created session: {sess_year}'))

        # =====================================================
        # 5. CREATE SCHEMES OF STUDY
        # =====================================================
        self.stdout.write('\nCreating schemes of study...')
        programs = Programs.objects.all()
        course_groups = CourseGroup.objects.all()
        sessions = Session.objects.all()
        
        for program in programs:
            for cg in course_groups.filter(program_id=program):
                for session in sessions:
                    scheme, created = SchemeOfStudy.objects.get_or_create(
                        program=program,
                        course_group=cg,
                        session=session
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'✅ Created scheme: {scheme}'))

        # =====================================================
        # 6. CREATE PROVINCES AND DISTRICTS
        # =====================================================
        self.stdout.write('\nCreating locations...')
        province, created = Province.objects.get_or_create(province='Punjab')
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created province: Punjab'))
        
        district, created = District.objects.get_or_create(district='Sheikhupura')
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created district: Sheikhupura'))

        # =====================================================
        # 7. CREATE TEST STUDENTS
        # =====================================================
        self.stdout.write('\nCreating test students...')
        
        students_data = [
            {
                'name': 'Ahmed Ali',
                'college_roll_no': 'CS001',
                'cnic_no': '3520112345671',
                'mobile_no': '03001234567',
                'email': 'ahmed@example.com',
            },
            {
                'name': 'Fatima Khan',
                'college_roll_no': 'CS002',
                'cnic_no': '3520112345672',
                'mobile_no': '03001234568',
                'email': 'fatima@example.com',
            },
            {
                'name': 'Hassan Malik',
                'college_roll_no': 'CS003',
                'cnic_no': '3520112345673',
                'mobile_no': '03001234569',
                'email': 'hassan@example.com',
            },
        ]
        
        # Get first scheme for BS Computer Science
        cs_program = Programs.objects.filter(heading__icontains='Computer').first()
        if cs_program:
            cs_scheme = SchemeOfStudy.objects.filter(program=cs_program).first()
            
            if cs_scheme:
                for student_data in students_data:
                    student, created = RegisteredStudent.objects.get_or_create(
                        cnic_no=student_data['cnic_no'],
                        defaults={
                            'status': 'morning',
                            'college_roll_no': student_data['college_roll_no'],
                            'name': student_data['name'],
                            'date_of_birth': date(2000, 1, 1),
                            'mobile_no': student_data['mobile_no'],
                            'email': student_data['email'],
                            'father_name': 'Father Name',
                            'father_cnic': '3520198765432',
                            'father_mobile_no': '03009876543',
                            'father_occupation': 'Business',
                            'permanent_address': 'Test Address, Sheikhupura',
                            'postal_address': 'Test Address, Sheikhupura',
                            'province': province,
                            'district': district,
                            'city': 'Sheikhupura',
                            'gender': 'Male',
                            'religion': 'Islam',
                            'blood_group': 'A+',
                            'marital_status': 'Unmarried',
                            'scheme_of_study': cs_scheme
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'✅ Created student: {student.name}'))

        # =====================================================
        # 8. CREATE FEE HEADS
        # =====================================================
        self.stdout.write('\nCreating fee heads...')
        
        fee_heads_data = [
            {'name': 'Tuition Fee', 'amount': 25000},
            {'name': 'Library Fee', 'amount': 2000},
            {'name': 'Sports Fee', 'amount': 1000},
            {'name': 'Lab Fee', 'amount': 3000},
        ]
        
        for fh_data in fee_heads_data:
            fee_head, created = FeeHead.objects.get_or_create(
                fee_head_name=fh_data['name'],
                defaults={'fee_head_amount': fh_data['amount']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created fee head: {fh_data["name"]}'))
            
            # Link to all programs
            for program in Programs.objects.all():
                FeeHeadProgram.objects.get_or_create(
                    fee_head=fee_head,
                    program=program
                )
        
        # =====================================================
        # 9. CREATE SINGLE CHALLAN
        # =====================================================
        self.stdout.write('\nCreating single challan...')
        
        # Get first student or create one
        student = RegisteredStudent.objects.first()
        
        if not student:
            self.stdout.write(self.style.ERROR("❌ No students found in database. Please create a student first."))
            return
        
        # Generate unique challan number
        last_two = student.college_roll_no[-2:] if len(student.college_roll_no) >= 2 else student.college_roll_no.zfill(2)[-2:]
        challan_number = f"CH{random.randint(10000, 99999)}{last_two}"
        
        # Generate One Bill Number (14 digits)
        onelink_number = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        
        due_date = timezone.now().date() + timedelta(days=30)
        
        # Create challan
        challan = Challan.objects.create(
            challan_number=challan_number,
            student=student,
            program=student.scheme_of_study.program if hasattr(student, 'scheme_of_study') else None,
            session='2024',
            shift=student.status,
            challan_amount=Decimal('30000.00'),
            due_date=due_date,
            one_bill_number=onelink_number,
            disciplines='[1]',
            semesters='[1, 2]',
            status='Active'
        )
        
        # Add fee head
        ChallanFeeHead.objects.create(
            challan=challan,
            fee_head_account_id=1,
            amount=Decimal('30000.00')
        )
        
        self.stdout.write(self.style.SUCCESS("✅ Single challan created successfully!"))
        self.stdout.write(self.style.SUCCESS(f"   Challan Number: {challan_number}"))
        self.stdout.write(self.style.SUCCESS(f"   One Bill Number: {onelink_number}"))
        self.stdout.write(self.style.SUCCESS(f"   Student: {student.name}"))
        self.stdout.write(self.style.SUCCESS(f"   Amount: Rs. 30000.00"))
        self.stdout.write(self.style.SUCCESS(f"   Due Date: {due_date}"))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database population completed successfully!'))