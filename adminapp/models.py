from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None): 
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):  
        user = self.create_user(email, password)
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):  
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    
    dob = models.DateField(null=True, blank=True)  
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    contact_no = models.CharField(max_length=15, null=True, blank=True)  
    address = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    
    
    
    
class Doctor(models.Model):
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    qualification = models.CharField(max_length=255)
    experience = models.IntegerField()
    image = models.FileField(upload_to='images/',null=True,blank=True)
    
    def str(self):
        return self.name
    
    
class Appoinment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    
    class Meta:
        unique_together=["doctor","date","time"]
    
    def str(self):
        return f"Appointment with Dr. {self.doctor.name} on {self.date}at{self.time}"
    
    
    #profile model (extends user safely)
class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    phone=models.CharField(max_length=15,blank=True)
    gender=models.CharField(max_length=10,blank=True)
    dob=models.DateField(null=True,blank=True)
    address=models.TextField(blank=True)
    avatar=models.ImageField(upload_to="avatar/",null=True,blank=True)
        
    def __str__(self):
            return self.user.username