from rest_framework import serializers
from adminapp.models import Doctor
from adminapp.models import Appoinment,Profile
from django.utils.timezone import now

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
            raise serializers.ValisationError("Cannot reschedule to a past date.")
        
        #Conflict check
        conflict = Appoinment.objects.filter(
            doctor=appointment.doctor,
            date=new_date,
            time=new_time
        ).exclude(id=appointment.id).exists()
        
        if conflict:
            raise serializers.ValidationError(
                "This time slot is already booked for the doctor."
            )
        return data
    
    
    
class ProfileSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(source="user.email",read_only=True)
    username=serializers.CharField(source="user.username",read_only=True)
    
    class Meta:
        model=Profile
        fields="__all__"