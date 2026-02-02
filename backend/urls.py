from adminapp import views
from django.urls import path
from django.conf import settings

from django.conf.urls.static import static

urlpatterns = [
    path('', views.adminlogin,name="adminlogin"),
    path('todaysappointment/',views.todaysappointment,name="todaysappointment"),
    path('doctormanagement/',views.doctormanagement,name="doctormanagement"),
    path('doctorview/<int:id>/',views.doctorview,name='doctorview'),
    path('doctorupdate/<int:id>',views.doctorupdate,name='doctorupdate'),
    path('doctoradd/',views.doctoradd,name='doctoradd'),
    path('history/',views.history,name='history'),
    path('report/',views.report,name='report'),
    path('doctor/delete/<int:id>',views.doctordelete,name="delete_doctor"),
    path('patients/history/<int:id>',views.patientHistory,name="patient_history"),

    
    
    
    
    
    path('signup',views.Signup, name='signup'),
    path('login/',views.Login, name='login'),
    path('changepassword/',views.change_password, name='changepassword'),
    path('doctorlist/',views.doctorlist, name='doctorlist'),
    path('appointmentbooking/',views.appointmentbooking, name='appointmentbooking'),
    path('myappointments/',views.myappointments, name='myappointments'),
    path('cancelappointment/<int:id>/',views.cancelappointment, name='cancelappointment'),
     path('logout/',views.Logout, name='logout'),
     path('appointments/<int:pk>/reschedule/',views.reschedule_appointment,name="appointment-reschedule"),
     path('profile/',views.profile_view,name="profile")
    
    
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)