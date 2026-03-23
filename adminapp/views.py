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
import time
import logging
logger = logging.getLogger("appointment_app")




def adminlogin(request):
    error = ""
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request,email=email,password=password)
        if user is not None and user.is_admin: # type: ignore
            login(request,user)
            return redirect('todaysappointment')
        else:
            return render(request,'adminlogin.html',{"error":"Invalid credential or not an admin"})
    return render(request,'adminlogin.html')
        
            
    
def todaysappointment(request):
    selected_date = request.GET.get('date')
    now = timezone.now()
    if selected_date:
        appointments =Appoinment.objects.filter(date=selected_date)
    else:
        today = date.today()
        appointments = Appoinment.objects.filter(date=today)
    past_appointments = Appoinment.objects.filter(date__lt=now.date()).order_by('-date')
    upcoming_appointments = Appoinment.objects.filter(date__gte=now.date()).order_by('date')
    
    context = {
        'appointment':appointments,
        'selected_date':selected_date or date.today().isoformat(),
        'past_appointments':past_appointments,
        'upcoming_appointments':upcoming_appointments,
    }
    return render(request, 'todaysappointment.html',context)





def doctormanagement(request):
    data = Doctor.objects.all()
    return render(request,'doctormanagement.html',{'data':data})




def doctordelete(request,id):
    if request.method == 'POST':
        doctor = get_object_or_404(Doctor,id=id)
        doctor.delete()
        return redirect('doctormanagement')





def doctorview(request,id):
    doctor = get_object_or_404(Doctor, id=id)
    return render(request,'doctorview.html',{'data':doctor})

    


def doctorupdate(request,id):
    data = get_object_or_404(Doctor,id=id)
    if request.method =="POST":
        data.name = request.POST.get('name')
        data.department = request.POST.get('department')
        data.qualification = request.POST.get('qualification')
        data.experience = request.POST.get('experience')
        if 'image' in request.FILES:
            data.image = request.FILES['image']
        data.save()
        return redirect('doctorview',id=data.id) # type: ignore
    return render(request,'doctorupdate.html',{'data':data})
        
    
def doctoradd(request):
    if request.method =='POST':
        name = request.POST.get('name')
        department = request.POST.get('department')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        image = request.FILES.get('image')  #
        print(image)
        
        Doctor.objects.create(
            name=name,
            department=department,
            qualification=qualification,
            experience=experience,
            image=image
        )
        return redirect('/doctormanagement')
    return render(request,'doctoradd.html')



from .models import Doctor, DoctorAvailability
from django.shortcuts import render, redirect, get_object_or_404


def doctor_availability_add(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == "POST":
        day_of_week = request.POST.get("day_of_week")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        if not all([day_of_week, start_time, end_time]):
            return render(request, "doctor_availability_add.html", {
                "doctor": doctor,
                "error": "All fields are required"
            })

        DoctorAvailability.objects.create(
            doctor=doctor,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )

        return redirect('doctorview', id=doctor.id) # type: ignore

    return render(request, "doctor_availability_add.html", {
        "doctor": doctor
    })




def doctor_availability_list(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    availability = DoctorAvailability.objects.filter(doctor=doctor)

    return render(request, "doctor_availability_list.html", {
        "doctor": doctor,
        "availability": availability
    })






def doctor_availability_delete(request, id):
    availability = get_object_or_404(DoctorAvailability, id=id)
    doctor_id = availability.doctor.id # type: ignore

    if request.method == "POST":
        availability.delete()
        return redirect('doctor_availability_list', doctor_id=doctor_id)

    return redirect('doctor_availability_list', doctor_id=doctor_id)




        
def history(request):
    data = Appoinment.objects.all()
    return render(request,'history.html',{"data":data})



def patientHistory(request, id):
    history = Appoinment.objects.filter(user__id=id).order_by('-date')
    return render(request, 'patientHistory.html', {"data": history})

def report(request):
    report_data = (
        Appoinment.objects.annotate(month=TruncMonth('date'))
        .values('month','doctor__name','doctor__department')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    return render(request,'report.html',{"report_data":report_data})




#-------------------------------API----------------------------------------
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
def reschedule_appointment(request,pk):
    appointment=get_object_or_404(Appoinment, pk=pk)

    #permission check
    if request.user!=appointment.user and not request.user.is_staff:
        return Response(
            {"error":"You do not have permission to reschedule this appointment,"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer=AppointmentReschedulSerializer(
        appointment,
        data=request.data,
        partial=True
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message":"Appointment rescheduled successfully",
                "appointment":serializer.data
            },
            status=status.HTTP_200_OK
        )
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







    



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