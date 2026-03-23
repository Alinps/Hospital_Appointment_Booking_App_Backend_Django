from rest_framework import serializers
from adminapp.models import Doctor
from adminapp.models import Appoinment
from django.utils.timezone import now
from django.contrib.auth import get_user_model
User = get_user_model()
class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'
        
class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    department = serializers.CharField(source='doctor.department', read_only=True)

    class Meta:
        model = Appoinment
        fields = ['id', 'doctor', 'doctor_name', 'department', 'user', 'date','time']  # Include relevant fields



class AppointmentReschedulSerializer(serializers.ModelSerializer):
    class Meta:
        model=Appoinment
        fields=("date","time")
    def validate(self,data):
        appointment=self.instance
        new_date=data.get("date")
        new_time=data.get("time")
        
        #past date check
        if new_date < now().date():
            raise serializers.ValidationError("Cannot reschedule to a past date.")
        
        #Conflict check
        conflict = Appoinment.objects.filter(
            doctor=appointment.doctor, # type: ignore
            date=new_date,
            time=new_time
        ).exclude(id=appointment.id).exists() # type: ignore
        
        if conflict:
            raise serializers.ValidationError(
                "This time slot is already booked for the doctor."
            )
        return data
    
    
    
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="name")

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "dob",
            "gender",
            "contact_no",
            "address",
            "avatar"
        ]