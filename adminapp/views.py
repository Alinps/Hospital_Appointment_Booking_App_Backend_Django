from django.http import JsonResponse
from django.contrib.auth import authenticate,login
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404, render,redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from .models import User,Doctor,Appoinment
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from .serializer import DoctorSerializer,AppointmentSerializer
from datetime import datetime,date, timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone 



def adminlogin(request):
    error = ""
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request,email=email,password=password)
        if user is not None and user.is_admin:
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
        return redirect('doctorview',id=data.id)
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

#Signup
@api_view(['POST'])
@permission_classes((AllowAny,))
def Signup(request):
    email = request.data.get("email")
    password = request.data.get("password")
    name = request.data.get("name")
    dob = request.data.get("dob")
    address = request.data.get("address")
    contact_no = request.data.get("contact_no")
    gender = request.data.get("gender")

    if not name or not email or not password:
        return Response({'message': 'Name, email, and password are required'}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'message': 'Email already exists'}, status=400)

    user = User.objects.create_user(email=email, password=password)
    user.name = name
    user.dob = dob
    user.address = address
    user.contact_no = contact_no
    user.gender = gender
    user.save()

    return JsonResponse({'message': 'User created successfully'}, status=201)



#Login
@api_view(['POST'])
@permission_classes((AllowAny,))
def Login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'message': 'Email and password are required'}, status=400)

    
    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response({'message': 'Invalid email or password'}, status=401)

    if not user.is_active:
        return Response({'message': 'User account is disabled'}, status=403)
    
    token, created = Token.objects.get_or_create(user=user)

    
    return JsonResponse({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'token': token.key,
            'name' : user.name,
            'email': user.email
        }
    }, status=200)
    
    
    
    
    
#Change password    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user  

    current_password = request.data.get('currentPassword')
    new_password = request.data.get('newPassword')
    confirm_password = request.data.get('confirmPassword')

    
    if not current_password or not new_password or not confirm_password:
        return Response({'message': 'All fields are required'}, status=400)

    
    if not user.check_password(current_password):
        return Response({'message': 'Current password is incorrect'}, status=400)

    
    if new_password != confirm_password:
        return Response({'message': 'New passwords do not match'}, status=400)

    
    user.set_password(new_password)
    user.save()

    return Response({'message': 'Password changed successfully'}, status=200)







#doctorlist
@api_view(['GET'])
@csrf_exempt
@permission_classes((IsAuthenticated,))
def doctorlist(request):
    doctors = Doctor.objects.all()
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)





#appointment booking
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def appointmentbooking(request):
    doctor_id = request.data.get('doctor')
    date_str = request.data.get('date')
    time_str = request.data.get('time')
    
    if not doctor_id or not date or not time_str:
        return Response({'error':'All feilds are required'},status=400)
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        user = request.user
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # .date() added here
        appointment_time = datetime.strptime(time_str, "%H:%M").time()
        
        Appoinment.objects.create(
            doctor = doctor,
            user = user,
            date = appointment_date,
            time = appointment_time
        )
        
        return Response({'message':'Appointment booked'}, status=201)
    except ValueError as e:
        return Response({'error': 'Invalid date or time format'}, status=400)
    except Doctor.DoesNotExist:
        return Response({'error':'Doctor not found'}, status=404)
    except Response as e:
        return Response({'error':str(e)}, status=500)
    
    
 #list appoinmnt   
@api_view(['GET'])
@csrf_exempt
@permission_classes((IsAuthenticated,))
def myappointments(request):
    appointment = Appoinment.objects.all()
    serializer = AppointmentSerializer(appointment, many=True)
    return Response(serializer.data)



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


    
    
    
#logout
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Logout(request):
    try:
        # Delete the user's token to log them out
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'}, status=200)
    except Exception as e:
        return Response({'message': 'Error during logout'}, status=500)