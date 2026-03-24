from adminapp import views
from django.urls import path
from django.conf import settings

from django.conf.urls.static import static

urlpatterns = [
    path('', views.adminlogin,name="adminlogin"), # type: ignore
    path('todaysappointment/',views.todaysappointment,name="todaysappointment"),
    path('doctormanagement/',views.doctormanagement,name="doctormanagement"),
    path('doctorview/<int:id>/',views.doctorview,name='doctorview'),
    path('doctorupdate/<int:id>',views.doctorupdate,name='doctorupdate'),
    path('doctoradd/',views.doctoradd,name='doctoradd'),
    path('history/',views.history,name='history'),
    path('report/',views.report,name='report'),
    path('doctor/delete/<int:id>',views.doctordelete,name="delete_doctor"), # type: ignore
    path('patients/history/<int:id>',views.patientHistory,name="patient_history"),
    path('doctor/<int:doctor_id>/availability/add/', views.doctor_availability_add, name='doctor_availability_add'),
path('doctor/<int:doctor_id>/availability/', views.doctor_availability_list, name='doctor_availability_list'),
path('availability/delete/<int:id>/', views.doctor_availability_delete, name='doctor_availability_delete'),

    
    
    
    
    
    path('signup',views.Signup, name='signup'),
    path('login/',views.Login, name='login'),
    path('changepassword/',views.change_password, name='changepassword'),
    path('doctorlist/',views.doctorlist, name='doctorlist'),
    path('appointmentbooking/',views.appointmentbooking, name='appointmentbooking'),
    path('myappointments/',views.myappointments, name='myappointments'),
    path('cancelappointment/<int:id>/',views.cancelappointment, name='cancelappointment'),
     path('logout/',views.Logout, name='logout'),
     path('appointments/<int:pk>/reschedule/',views.reschedule_appointment,name="appointment-reschedule"),
     path('profile/',views.profile_view,name="profile"),
     path('doctor/<int:doctor_id>/slots/',views.get_available_slots,name="available_slots"),
     path('doctordetail/<int:doctor_id>',views.doctor_detail)
    
    
]
# urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)