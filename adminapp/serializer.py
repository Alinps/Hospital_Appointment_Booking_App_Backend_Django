from rest_framework import serializers
from adminapp.models import Doctor
from adminapp.models import Appointment
from django.utils.timezone import now
from django.contrib.auth import get_user_model
User = get_user_model()


class DoctorSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')

        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        return None
        
class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    department = serializers.CharField(source='doctor.department', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'doctor_name', 'department', 'user', 'date','time']  # Include relevant fields



class AppointmentReschedulSerializer(serializers.ModelSerializer):
    class Meta:
        model=Appointment
        fields=("date","time")
    def validate(self,data):
        appointment=self.instance
        new_date=data.get("date")
        new_time=data.get("time")
        
        #past date check
        if new_date < now().date():
            raise serializers.ValidationError("Cannot reschedule to a past date.")
        
        #Conflict check
        conflict = Appointment.objects.filter(
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
    avatar = serializers.SerializerMethodField()

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

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None