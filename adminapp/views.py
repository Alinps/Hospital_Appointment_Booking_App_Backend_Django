from django.http import JsonResponse
from django.contrib.auth import authenticate,login
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404, render,redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from .models import User,Doctor,Appoinment,DoctorAvailability
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from .serializer import DoctorSerializer,AppointmentSerializer,AppointmentReschedulSerializer,UserSerializer
from datetime import datetime,date, timedelta, timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone 
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Doctor, DoctorAvailability
from django.shortcuts import render, redirect
import time
import logging
logger = logging.getLogger("appointment_app")






def adminlogin(request):
    start_time = time.time()
    error = ""

    # GET request
    if request.method == "GET":
        logger.info("Admin login page accessed")
        return render(request, 'adminlogin.html')

    #  POST request
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        ip = request.META.get("REMOTE_ADDR")

        logger.info(f"Admin login attempt | email={email} | ip={ip}")

        try:
            if not email or not password:
                logger.warning(f"Admin login failed: missing fields | email={email}")
                return render(
                    request,
                    'adminlogin.html',
                    {"error": "Email and password required"}
                )

            user = authenticate(request, email=email, password=password)

            if user is None:
                logger.warning(f"Admin login failed: invalid credentials | email={email}")
                return render(
                    request,
                    'adminlogin.html',
                    {"error": "Invalid credentials"}
                )

            if not user.is_admin: # type: ignore
                logger.warning(f"Admin login failed: not admin | user_id={user.id}") # type: ignore
                return render(
                    request,
                    'adminlogin.html',
                    {"error": "Not an admin account"}
                )

            #  Success
            login(request, user)

            duration = time.time() - start_time

            logger.info(
                f"Admin login success | user_id={user.id} " # type: ignore
                f"| email={email} | duration={duration:.2f}s"
            )

            return redirect('todaysappointment')

        except Exception as e:
            logger.error(
                f"Admin login error | email={email} | error={str(e)}"
            )

            return render(
                request,
                'adminlogin.html',
                {"error": "Internal server error"}
            )
        
            
    



def todaysappointment(request):
    start_time = time.time()
    user = request.user

    selected_date = request.GET.get('date')
    now = timezone.now()

    logger.info(
        f"Today's appointment view accessed | user_id={user.id} "
        f"| selected_date={selected_date}"
    )

    try:
        # Filter appointments
        if selected_date:
            appointments = Appoinment.objects.filter(date=selected_date)
        else:
            today = date.today()
            appointments = Appoinment.objects.filter(date=today)

        #  Past & upcoming
        past_appointments = Appoinment.objects.filter(
            date__lt=now.date()
        ).order_by('-date')

        upcoming_appointments = Appoinment.objects.filter(
            date__gte=now.date()
        ).order_by('date')

        #  Counts for logging
        total_today = appointments.count()
        total_past = past_appointments.count()
        total_upcoming = upcoming_appointments.count()

        duration = time.time() - start_time

        logger.info(
            f"Today's appointment success | user_id={user.id} "
            f"| today_count={total_today} | past_count={total_past} "
            f"| upcoming_count={total_upcoming} "
            f"| duration={duration:.2f}s"
        )

        context = {
            'appointment': appointments,
            'selected_date': selected_date or date.today().isoformat(),
            'past_appointments': past_appointments,
            'upcoming_appointments': upcoming_appointments,
        }

        return render(request, 'todaysappointment.html', context)

    except Exception as e:
        logger.error(
            f"Today's appointment error | user_id={user.id} | error={str(e)}"
        )

        return render(
            request,
            'todaysappointment.html',
            {"error": "Internal server error"}
        )






def doctormanagement(request):
    start_time = time.time()
    user = request.user

    logger.info(f"Doctor management view accessed | user_id={user.id}")

    try:
        
        if not user.is_authenticated or not user.is_admin:
            logger.warning(f"Unauthorized access to doctor management | user_id={user.id}")
            return redirect('adminlogin')

        data = Doctor.objects.all()
        count = data.count()

        duration = time.time() - start_time

        logger.info(
            f"Doctor management success | user_id={user.id} "
            f"| total_doctors={count} | duration={duration:.2f}s"
        )

        return render(request, 'doctormanagement.html', {'data': data})

    except Exception as e:
        logger.error(
            f"Doctor management error | user_id={user.id} | error={str(e)}"
        )

        return render(
            request,
            'doctormanagement.html',
            {'error': 'Internal server error'}
        )







def doctordelete(request, id):
    start_time = time.time()
    user = request.user

    logger.info(f"Doctor delete request | user_id={user.id} | doctor_id={id}")

    
    if request.method != 'POST':
        logger.warning(
            f"Doctor delete failed: invalid method | user_id={user.id} | method={request.method}"
        )
        return redirect('doctormanagement')

    
    if not user.is_authenticated or not user.is_admin:
        logger.warning(
            f"Unauthorized doctor delete attempt | user_id={user.id} | doctor_id={id}"
        )
        return redirect('adminlogin')

    try:
        doctor = get_object_or_404(Doctor, id=id)

        doctor_name = doctor.name

        doctor.delete()

        duration = time.time() - start_time

        logger.info(
            f"Doctor deleted | doctor_id={id} | doctor_name={doctor_name} "
            f"| deleted_by={user.id} | duration={duration:.2f}s"
        )

        return redirect('doctormanagement')

    except Exception as e:
        logger.error(
            f"Doctor delete error | user_id={user.id} | doctor_id={id} | error={str(e)}"
        )
        return redirect('doctormanagement')








def doctorview(request, id):
    start_time = time.time()
    user = request.user

    logger.info(f"Doctor view request | user_id={user.id} | doctor_id={id}")

    
    if not user.is_authenticated or not user.is_admin:
        logger.warning(
            f"Unauthorized doctor view access | user_id={user.id} | doctor_id={id}"
        )
        return redirect('adminlogin')

    try:
        doctor = get_object_or_404(Doctor, id=id)

        duration = time.time() - start_time

        logger.info(
            f"Doctor view success | doctor_id={id} | doctor_name={doctor.name} "
            f"| user_id={user.id} | duration={duration:.2f}s"
        )

        return render(request, 'doctorview.html', {'data': doctor})

    except Exception as e:
        logger.error(
            f"Doctor view error | user_id={user.id} | doctor_id={id} | error={str(e)}"
        )

        return render(
            request,
            'doctorview.html',
            {'error': 'Internal server error'}
        )

    





def doctorupdate(request, id):
    start_time = time.time()
    user = request.user

    logger.info(f"Doctor update view accessed | user_id={user.id} | doctor_id={id}")

    
    if not user.is_authenticated or not user.is_admin:
        logger.warning(
            f"Unauthorized doctor update access | user_id={user.id} | doctor_id={id}"
        )
        return redirect('adminlogin')

    try:
        data = get_object_or_404(Doctor, id=id)

        if request.method == "POST":
            
            old_data = {
                "name": data.name,
                "department": data.department,
                "qualification": data.qualification,
                "experience": data.experience,
            }

            # New values
            new_name = request.POST.get('name')
            new_department = request.POST.get('department')
            new_qualification = request.POST.get('qualification')
            new_experience = request.POST.get('experience')

            # Apply updates
            data.name = new_name
            data.department = new_department
            data.qualification = new_qualification
            data.experience = new_experience

            image_updated = False
            if 'image' in request.FILES:
                data.image = request.FILES['image']
                image_updated = True

            data.save()

            duration = time.time() - start_time

            logger.info(
                f"Doctor updated | doctor_id={id} | updated_by={user.id} "
                f"| old={old_data} "
                f"| new={{'name': new_name, 'department': new_department}} "
                f"| image_updated={image_updated} "
                f"| duration={duration:.2f}s"
            )

            return redirect('doctorview', id=data.id) # type: ignore

        return render(request, 'doctorupdate.html', {'data': data})

    except Exception as e:
        logger.error(
            f"Doctor update error | user_id={user.id} | doctor_id={id} | error={str(e)}"
        )

        return render(
            request,
            'doctorupdate.html',
            {'error': 'Internal server error'}
        )
        



def doctoradd(request):
    start_time = time.time()
    user = request.user

    logger.info(f"Doctor add view accessed | user_id={user.id}")

    
    if not user.is_authenticated or not user.is_admin:
        logger.warning(f"Unauthorized doctor add attempt | user_id={user.id}")
        return redirect('adminlogin')

    try:
        if request.method == 'POST':
            name = request.POST.get('name')
            department = request.POST.get('department')
            qualification = request.POST.get('qualification')
            experience = request.POST.get('experience')
            image = request.FILES.get('image')

            
            if not name or not department:
                logger.warning(
                    f"Doctor add failed: missing required fields | user_id={user.id}"
                )
                return render(
                    request,
                    'doctoradd.html',
                    {'error': 'Name and department are required'}
                )

            doctor = Doctor.objects.create(
                name=name,
                department=department,
                qualification=qualification,
                experience=experience,
                image=image
            )

            duration = time.time() - start_time

            logger.info(
                f"Doctor created | doctor_id={doctor.id} | name={name} " # type: ignore
                f"| department={department} | created_by={user.id} "
                f"| image_uploaded={bool(image)} "
                f"| duration={duration:.2f}s"
            )

            return redirect('/doctormanagement')

        return render(request, 'doctoradd.html')

    except Exception as e:
        logger.error(
            f"Doctor add error | user_id={user.id} | error={str(e)}"
        )

        return render(
            request,
            'doctoradd.html',
            {'error': 'Internal server error'}
        )







def doctor_availability_add(request, doctor_id):
    start_time = time.time()
    user = request.user

    logger.info(
        f"Availability add view accessed | user_id={user.id} | doctor_id={doctor_id}"
    )

    
    if not user.is_authenticated or not user.is_admin:
        logger.warning(
            f"Unauthorized availability add attempt | user_id={user.id} | doctor_id={doctor_id}"
        )
        return redirect('adminlogin')

    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)

        if request.method == "POST":
            day_of_week = request.POST.get("day_of_week")
            start_time_val = request.POST.get("start_time")
            end_time_val = request.POST.get("end_time")

            logger.info(
                f"Availability add attempt | doctor_id={doctor_id} "
                f"| day={day_of_week} | start={start_time_val} | end={end_time_val}"
            )

            #  Validation
            if not all([day_of_week, start_time_val, end_time_val]):
                logger.warning(
                    f"Availability add failed: missing fields | doctor_id={doctor_id}"
                )
                return render(request, "doctor_availability_add.html", {
                    "doctor": doctor,
                    "error": "All fields are required"
                })

            
            if start_time_val >= end_time_val:
                logger.warning(
                    f"Availability add failed: invalid time range | doctor_id={doctor_id}"
                )
                return render(request, "doctor_availability_add.html", {
                    "doctor": doctor,
                    "error": "Start time must be before end time"
                })

            availability = DoctorAvailability.objects.create(
                doctor=doctor,
                day_of_week=day_of_week,
                start_time=start_time_val,
                end_time=end_time_val
            )

            duration = time.time() - start_time

            logger.info(
                f"Availability created | availability_id={availability.id} " # type: ignore
                f"| doctor_id={doctor_id} | day={day_of_week} "
                f"| start={start_time_val} | end={end_time_val} "
                f"| created_by={user.id} | duration={duration:.2f}s"
            )

            return redirect('doctorview', id=doctor.id) # type: ignore

        return render(request, "doctor_availability_add.html", {
            "doctor": doctor
        })

    except Exception as e:
        logger.error(
            f"Availability add error | user_id={user.id} "
            f"| doctor_id={doctor_id} | error={str(e)}"
        )

        return render(
            request,
            "doctor_availability_add.html",
            {"error": "Internal server error"}
        )



def doctor_availability_list(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    availability = DoctorAvailability.objects.filter(doctor=doctor)

    return render(request, "doctor_availability_list.html", {
        "doctor": doctor,
        "availability": availability
    })









def doctor_availability_delete(request, id):
    start_time = time.time()
    user = request.user

    logger.info(f"Availability delete request | user_id={user.id} | availability_id={id}")

    
    if request.method != "POST":
        logger.warning(
            f"Availability delete failed: invalid method | user_id={user.id} | method={request.method}"
        )
        return redirect('doctor_availability_list')

    
    if not user.is_authenticated or not user.is_admin:
        logger.warning(
            f"Unauthorized availability delete attempt | user_id={user.id} | availability_id={id}"
        )
        return redirect('adminlogin')

    try:
        availability = get_object_or_404(DoctorAvailability, id=id)

        doctor_id = availability.doctor.id # type: ignore
        doctor_name = availability.doctor.name
        day = availability.day_of_week
        start_time_val = availability.start_time
        end_time_val = availability.end_time

        availability.delete()

        duration = time.time() - start_time

        logger.info(
            f"Availability deleted | availability_id={id} | doctor_id={doctor_id} "
            f"| doctor_name={doctor_name} | day={day} "
            f"| start={start_time_val} | end={end_time_val} "
            f"| deleted_by={user.id} | duration={duration:.2f}s"
        )

        return redirect('doctor_availability_list', doctor_id=doctor_id)

    except Exception as e:
        logger.error(
            f"Availability delete error | user_id={user.id} | availability_id={id} | error={str(e)}"
        )

        return redirect('doctor_availability_list', doctor_id=doctor_id)




        


def history(request):
    logger.info(f"REQUEST → {request.method} {request.path}")

    data = Appoinment.objects.all()
    count = data.count()

    logger.info(f"Fetched {count} appointments from database")

    response = render(request, 'history.html', {"data": data})

    logger.info(f"RESPONSE ← {request.method} {request.path} | Status: 200")

    return response





def patientHistory(request, id):
    logger.info(f"REQUEST → {request.method} {request.path} | user_id={id}")

    start_time = time.time()

    try:
        queryset = (
            Appoinment.objects
            .filter(user__id=id)
            .order_by('-date')
        )

        # Force evaluation
        history_list = list(queryset)

        query_time = time.time() - start_time

        logger.info(f"Patient history query executed in {query_time:.4f}s")
        logger.info(f"Fetched {len(history_list)} records for user_id={id}")

        if not history_list:
            logger.warning(f"No history found for user_id={id}")

        response = render(request, 'patientHistory.html', {
            "data": history_list
        })

        logger.info(f"RESPONSE ← {request.method} {request.path} | Status: 200")

        return response

    except Exception:
        logger.exception(f"ERROR fetching patient history | user_id={id}")

        return render(request, 'patientHistory.html', {
            "data": [],
            "error": "Unable to load patient history."
        })


def report(request):
    logger.info(f"REQUEST → {request.method} {request.path}")

    start_time = time.time()

    try:
        queryset = (
            Appoinment.objects
            .annotate(month=TruncMonth('date'))
            .values('month', 'doctor__name', 'doctor__department')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        
        report_list = list(queryset)

        query_time = time.time() - start_time
        logger.info(f"Report query executed in {query_time:.4f}s")
        logger.info(f"Generated {len(report_list)} report rows")

        if report_list:
            top = report_list[0]
            logger.debug(
                f"Top → Doctor: {top['doctor__name']} | "
                f"Dept: {top['doctor__department']} | "
                f"Month: {top['month']} | Total: {top['total']}"
            )
        else:
            logger.warning("Report returned empty dataset")

        response = render(request, "report.html", {
            "report_data": report_list
        })

        logger.info(f"RESPONSE ← {request.method} {request.path} | Status: 200")
        return response

    except Exception:
        
        logger.exception("ERROR generating report")

        return render(request, "report.html", {
            "report_data": [],
            "error": "Unable to generate report at the moment."
        })




#-------------------------------API----------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def wakeup(request):
    try:

        logger.info(
            f"Wakeup ping received"
        )

        return JsonResponse({
            "status": "ok",
            "message": "Server is awake"
        })

    except Exception as e:
        logger.exception(
            f"Wakeup error | error={str(e)}"
        )
        return JsonResponse({
            "status": "error",
            "message": "Server failed"
        }, status=500)

#Signup
@api_view(['POST'])
@permission_classes((AllowAny,))
def Signup(request):
    logger.info("Signup request received")

    email = request.data.get("email")
    password = request.data.get("password")
    name = request.data.get("name")
    dob = request.data.get("dob")
    address = request.data.get("address")
    contact_no = request.data.get("contact_no")
    gender = request.data.get("gender")

    
    logger.info(f"Signup attempt for email={email}, name={name}")

    if not name or not email or not password:
        logger.warning("Signup failed: Missing required fields")
        return Response(
            {'message': 'Name, email, and password are required'},
            status=400
        )

    if User.objects.filter(email=email).exists():
        logger.warning(f"Signup failed: Email already exists ({email})")
        return Response(
            {'message': 'Email already exists'},
            status=400
        )

    try:
        user = User.objects.create_user(  # type: ignore
            email=email,
            password=password
        )

        user.name = name
        user.dob = dob
        user.address = address
        user.contact_no = contact_no
        user.gender = gender
        user.save()

        logger.info(f"User created successfully: id={user.id}, email={email}")

        return Response(
            {'message': 'User created successfully'},
            status=201
        )

    except Exception as e:
        logger.error(f"Signup error for email={email}: {str(e)}")

        return Response(
            {'error': 'Internal server error'},
            status=500
        )





@api_view(['POST'])
@permission_classes((AllowAny,))
def Login(request):
    logger.info("Login request received")

    email = request.data.get('email')
    password = request.data.get('password')

    
    logger.info(f"Login attempt for email={email}")

    if not email or not password:
        logger.warning("Login failed: Missing email or password")
        return Response(
            {'message': 'Email and password are required'},
            status=400
        )

    try:
        user = authenticate(request, email=email, password=password)

        if user is None:
            logger.warning(f"Login failed: Invalid credentials for email={email}")
            return Response(
                {'message': 'Invalid email or password'},
                status=401
            )

        if not user.is_active:
            logger.warning(f"Login failed: Inactive user email={email}")
            return Response(
                {'message': 'User account is disabled'},
                status=403
            )

        token, created = Token.objects.get_or_create(user=user)

        logger.info(
            f"Login successful: user_id={user.id}, email={email}, new_token={created}" # type: ignore
        )

        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id, # type: ignore
                'token': token.key,   
                'name': user.name, # type: ignore
                'email': user.email
            }
        }, status=200)

    except Exception as e:
        logger.error(f"Login error for email={email}: {str(e)}")

        return Response(
            {'error': 'Internal server error'},
            status=500
        )
    
    
    
    
    
#Change password    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user

    logger.info(f"Password change request received for user_id={user.id}, email={user.email}")

    current_password = request.data.get('currentPassword')
    new_password = request.data.get('newPassword')
    confirm_password = request.data.get('confirmPassword')

    # Validate input
    if not current_password or not new_password or not confirm_password:
        logger.warning(f"Password change failed (missing fields) user_id={user.id}")
        return Response({'message': 'All fields are required'}, status=400)

    # Check current password
    if not user.check_password(current_password):
        logger.warning(f"Password change failed (wrong current password) user_id={user.id}")
        return Response({'message': 'Current password is incorrect'}, status=400)

    # Check new password match
    if new_password != confirm_password:
        logger.warning(f"Password change failed (password mismatch) user_id={user.id}")
        return Response({'message': 'New passwords do not match'}, status=400)

    try:
        user.set_password(new_password)
        user.save()

        logger.info(f"Password changed successfully for user_id={user.id}")

        return Response({'message': 'Password changed successfully'}, status=200)

    except Exception as e:
        logger.error(f"Password change error for user_id={user.id}: {str(e)}")

        return Response({'error': 'Internal server error'}, status=500)







#doctorlist
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def doctorlist(request):
    start_time = time.time()

    department = request.GET.get("department")
    search = request.GET.get("search")

    logger.info(
        f"Doctor list request received | user_id={request.user.id} "
        f"| search={search} | department={department}"
    )

    try:
        queryset = Doctor.objects.all().order_by("id")

        # Search filter
        if search:
            queryset = queryset.filter(name__icontains=search)

        #  Department filter
        if department:
            queryset = queryset.filter(department__iexact=department)

        total_count = queryset.count()

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10

        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = DoctorSerializer(paginated_queryset, many=True)

        duration = time.time() - start_time

        logger.info(
            f"Doctor list success | user_id={request.user.id} "
            f"| total={total_count} | returned={len(serializer.data)} "
            f"| page={request.GET.get('page', 1)} "
            f"| time={duration:.2f}s"
        )

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        logger.error(
            f"Doctor list error | user_id={request.user.id} | error={str(e)}"
        )

        return Response(
            {"error": "Internal server error"},
            status=500
        )








@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_slots(request, doctor_id):
    start_time = time.time()

    date_str = request.GET.get('date')

    logger.info(
        f"Slots request received | doctor_id={doctor_id} | date={date_str}"
    )

    if not date_str:
        logger.warning(f"Slots failed: missing date | doctor_id={doctor_id}")
        return Response({'error': 'Date is required'}, status=400)

    try:
        doctor = Doctor.objects.get(id=doctor_id)
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # get schedule
        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=appointment_date.weekday()
        ).first()

        if not availability:
            logger.info(
                f"No availability | doctor_id={doctor_id} | date={date_str}"
            )
            return Response({'slots': []})

        #  generate slots
        slots = []
        current = datetime.combine(appointment_date, availability.start_time)
        end = datetime.combine(appointment_date, availability.end_time)

        while current < end:
            slots.append(current.time())
            current += timedelta(minutes=30)

        #get booked slots
        booked = Appoinment.objects.filter(
            doctor=doctor,
            date=appointment_date
        ).values_list('time', flat=True)

        #  remove booked
        available = [
            s.strftime("%H:%M")
            for s in slots
            if s not in booked
        ]

        duration = time.time() - start_time

        logger.info(
            f"Slots success | doctor_id={doctor_id} | date={date_str} "
            f"| total_slots={len(slots)} | booked={len(booked)} "
            f"| available={len(available)} | time={duration:.2f}s"
        )

        return Response({'slots': available})

    except Doctor.DoesNotExist:
        logger.warning(f"Slots failed: doctor not found | doctor_id={doctor_id}")
        return Response({'error': 'Doctor not found'}, status=404)

    except ValueError:
        logger.warning(f"Slots failed: invalid date format | date={date_str}")
        return Response({'error': 'Invalid date format'}, status=400)

    except Exception as e:
        logger.error(
            f"Slots error | doctor_id={doctor_id} | date={date_str} | error={str(e)}"
        )
        return Response({'error': 'Internal server error'}, status=500)






@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def appointmentbooking(request):
    start_time = time.time()

    doctor_id = request.data.get('doctor')
    date_str = request.data.get('date')
    time_str = request.data.get('time')
    user = request.user

    logger.info(
        f"Booking request received | user_id={user.id} "
        f"| doctor_id={doctor_id} | date={date_str} | time={time_str}"
    )

    if not doctor_id or not date_str or not time_str:
        logger.warning(f"Booking failed: missing fields | user_id={user.id}")
        return Response({'error': 'All fields are required'}, status=400)

    try:
        doctor = Doctor.objects.get(id=doctor_id)

        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appointment_time = datetime.strptime(time_str, "%H:%M").time()

        #Check slot already booked
        if Appoinment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            time=appointment_time
        ).exists():
            logger.warning(
                f"Booking conflict | doctor_id={doctor_id} "
                f"| date={date_str} | time={time_str}"
            )
            return Response({'error': 'Slot already booked'}, status=400)

        # Create appointment
        appointment = Appoinment.objects.create(
            doctor=doctor,
            user=user,
            date=appointment_date,
            time=appointment_time
        )

        duration = time.time() - start_time

        logger.info(
            f"Booking success | appointment_id={appointment.id} " # type: ignore
            f"| user_id={user.id} | doctor_id={doctor_id} "
            f"| time={time_str} | duration={duration:.2f}s"
        )

        return Response({
            'message': 'Appointment booked',
            'appointment_id': appointment.id # type: ignore
        }, status=201)

    except ValueError:
        logger.warning(
            f"Booking failed: invalid date/time | date={date_str} | time={time_str}"
        )
        return Response({'error': 'Invalid date or time format'}, status=400)

    except Doctor.DoesNotExist:
        logger.warning(f"Booking failed: doctor not found | doctor_id={doctor_id}")
        return Response({'error': 'Doctor not found'}, status=404)

    except Exception as e:
        logger.error(
            f"Booking error | user_id={user.id} | doctor_id={doctor_id} | error={str(e)}"
        )
        return Response({'error': 'Internal server error'}, status=500)
    







@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def doctor_detail(request, doctor_id):
    start_time = time.time()

    logger.info(
        f"Doctor detail request received | user_id={request.user.id} | doctor_id={doctor_id}"
    )

    try:
        doctor = Doctor.objects.get(id=doctor_id)

        data = {
            "name": doctor.name,
            "department": doctor.department,
        }

        duration = time.time() - start_time

        logger.info(
            f"Doctor detail success | doctor_id={doctor_id} "
            f"| user_id={request.user.id} | time={duration:.2f}s"
        )

        return Response({"data": data})

    except Doctor.DoesNotExist:
        logger.warning(
            f"Doctor detail failed: not found | doctor_id={doctor_id} "
            f"| user_id={request.user.id}"
        )
        return Response({"error": "Doctor not found"}, status=404)

    except Exception as e:
        logger.error(
            f"Doctor detail error | doctor_id={doctor_id} "
            f"| user_id={request.user.id} | error={str(e)}"
        )
        return Response({"error": "Internal server error"}, status=500)



    
 #list appoinmnt   
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def myappointments(request):
    start_time = time.time()

    user = request.user

    logger.info(f"My appointments request received | user_id={user.id}")

    try:
        appointments = Appoinment.objects.filter(user=user).order_by("-date", "-time")

        serializer = AppointmentSerializer(appointments, many=True)

        duration = time.time() - start_time

        logger.info(
            f"My appointments success | user_id={user.id} "
            f"| count={len(serializer.data)} | time={duration:.2f}s"
        )

        return Response(serializer.data)

    except Exception as e:
        logger.error(
            f"My appointments error | user_id={user.id} | error={str(e)}"
        )

        return Response(
            {"error": "Internal server error"},
            status=500
        )






#cancel appoimnt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancelappointment(request,id):
    user = request.user
    
    try:
        appointment = Appoinment.objects.get(id=id, user=user)
    except Appoinment.DoesNotExist:
        return Response({"message":'Appointment not found'}, status =404)
    appointment.delete()
    return Response({'message':'Appointment cancelled successfully'},status=200)






    
    




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Logout(request):
    start_time = time.time()
    user = request.user

    logger.info(f"Logout request received | user_id={user.id} | email={user.email}")

    try:
        token = Token.objects.filter(user=user).first()

        if not token:
            logger.warning(f"Logout: token not found | user_id={user.id}")
            return Response({'message': 'Already logged out'}, status=400)

        token.delete()

        duration = time.time() - start_time

        logger.info(
            f"Logout success | user_id={user.id} | duration={duration:.2f}s"
        )

        return Response({'message': 'Logout successful'}, status=200)

    except Exception as e:
        logger.error(
            f"Logout error | user_id={user.id} | error={str(e)}"
        )

        return Response({'message': 'Error during logout'}, status=500)
    





#edit 
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def reschedule_appointment(request, pk):
    start_time = time.time()

    try:
        appointment = get_object_or_404(Appoinment, pk=pk)

        # Permission check
        if request.user != appointment.user and not request.user.is_staff:
            logger.warning(
                f"Unauthorized reschedule attempt | user_id={request.user.id} | appointment_id={pk} | path={request.path}"
            )
            return Response(
                {"error": "You do not have permission to reschedule this appointment"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AppointmentReschedulSerializer(
            appointment,
            data=request.data,
            partial=True
        )

        # Success case
        if serializer.is_valid():
            serializer.save()

            duration = round(time.time() - start_time, 3)

            logger.info(
                f"Appointment rescheduled successfully | user_id={request.user.id} | appointment_id={pk} | updated_fields={list(request.data.keys())} | duration={duration}s"
            )

            return Response(
                {
                    "message": "Appointment rescheduled successfully",
                    "appointment": serializer.data
                },
                status=status.HTTP_200_OK
            )

        # Validation error
        logger.error(
            f"Reschedule validation failed | user_id={request.user.id} | appointment_id={pk} | errors={serializer.errors}"
        )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Unexpected error
    except Exception as e:
        duration = round(time.time() - start_time, 3)

        logger.exception(
            f"Unexpected error in reschedule_appointment | user_id={getattr(request.user, 'id', None)} | appointment_id={pk} | duration={duration}s"
        )

        return Response(
            {"error": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )






    



@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    start_time = time.time()
    user = request.user

    if request.method == "GET":
        logger.info(f"Profile fetch request | user_id={user.id} | email={user.email}")

        try:
            serializer = UserSerializer(user)

            duration = time.time() - start_time

            logger.info(
                f"Profile fetch success | user_id={user.id} | duration={duration:.2f}s"
            )

            return Response(serializer.data)

        except Exception as e:
            logger.error(
                f"Profile fetch error | user_id={user.id} | error={str(e)}"
            )
            return Response({"error": "Internal server error"}, status=500)

    if request.method == "PUT":
        logger.info(f"Profile update request | user_id={user.id}")

        
        safe_fields = {
            "name": request.data.get("full_name"),
            "contact_no": request.data.get("contact_no"),
            "gender": request.data.get("gender"),
        }
        logger.info(f"Profile update data | user_id={user.id} | fields={safe_fields}")

        try:
            serializer = UserSerializer(
                user,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():
                logger.warning(
                    f"Profile update validation failed | user_id={user.id} "
                    f"| errors={serializer.errors}"
                )
                return Response(serializer.errors, status=400)

            serializer.save()

            duration = time.time() - start_time

            logger.info(
                f"Profile update success | user_id={user.id} | duration={duration:.2f}s"
            )

            return Response(serializer.data)

        except Exception as e:
            logger.error(
                f"Profile update error | user_id={user.id} | error={str(e)}"
            )
            return Response({"error": "Internal server error"}, status=500)