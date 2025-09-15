from rest_framework import serializers
from adminapp.models import Doctor
from adminapp.models import Appoinment

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
