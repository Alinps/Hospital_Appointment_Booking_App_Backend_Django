# Hospital Appointment Booking Platform (Backend)

A Django + Django REST Framework backend for managing doctors, patient profiles, and appointment booking.

This project supports:
- Admin web pages for doctor and appointment management
- Token-based API authentication for users
- Doctor availability scheduling with 30-minute slot generation
- Appointment booking, cancellation, and rescheduling
- Cloudinary-based media storage (doctor images and avatars)
- Basic operational middleware (request logging + global rate limiting)

## Tech Stack
- Python
- Django 4.2+
- Django REST Framework
- Token Authentication (`rest_framework.authtoken`)
- PostgreSQL via `dj-database-url`
- Cloudinary (media storage)
- WhiteNoise (static file serving)
- Gunicorn (production server)

## Project Structure

```text
Hospital_Appointment_Booking_App_Backend_Django/
├── manage.py
├── requirements.txt
├── procfile
├── app.log
├── backend/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── middlewares/
│       ├── logging_middleware.py
│       └── rate_limit.py
├── adminapp/
│   ├── models.py
│   ├── serializer.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       ├── adminlogin.html
│       ├── doctormanagement.html
│       ├── doctoradd.html
│       ├── doctorupdate.html
│       ├── doctorview.html
│       ├── doctor_availability_add.html
│       ├── doctor_availability_list.html
│       ├── todaysappointment.html
│       ├── history.html
│       ├── patientHistory.html
│       └── report.html
└── media/
    ├── avatar/
    └── images/
```

## Core Modules

### `backend/`
- Global Django configuration and app wiring.
- Includes custom middleware:
  - `RequestLoggingMiddleware`: logs request/response details and timing.
  - `GlobalRateLimitMiddleware`: in-memory per-user / per-IP request limiting.

### `adminapp/models.py`
Main domain models:
- `User` (custom auth model using email as `USERNAME_FIELD`)
- `Doctor`
- `Appoinment` (spelling in code is `Appoinment`)
- `DoctorAvailability`

### `adminapp/views.py`
Contains both:
- Admin template-rendered views (session-based admin login/management)
- API endpoints (DRF function-based views with token auth)

### `adminapp/serializer.py`
Serializers for:
- Doctors
- Appointment list and rescheduling validation
- User profile data

## URL & Endpoint Overview

### Admin Web Routes (Template Views)
- `GET/POST /` - admin login
- `/todaysappointment/` - today/upcoming/past appointments
- `/doctormanagement/` - doctor listing for admin
- `/doctorview/<id>/` - doctor detail page
- `/doctorupdate/<id>` - doctor update page
- `/doctoradd/` - add new doctor
- `/doctor/delete/<id>` - delete doctor (`POST`)
- `/doctor/<doctor_id>/availability/add/` - add doctor schedule
- `/doctor/<doctor_id>/availability/` - view doctor schedules
- `/availability/delete/<id>/` - delete availability (`POST`)
- `/history/` - all appointments history
- `/patients/history/<id>` - per-patient history
- `/report/` - monthly aggregated appointment report

### API Routes (JSON)
- `GET /health_check/` - uptime/health ping
- `POST /signup` - user registration
- `POST /login/` - user login + token issue
- `POST /logout/` - token delete/logout
- `POST /changepassword/` - change password
- `GET /doctorlist/` - paginated doctor list (`search`, `department`, `page`)
- `GET /doctordetail/<doctor_id>` - doctor summary
- `GET /doctor/<doctor_id>/slots/?date=YYYY-MM-DD` - available 30-minute slots
- `POST /appointmentbooking/` - book appointment
- `GET /myappointments/` - user’s appointments
- `DELETE /cancelappointment/<id>/` - cancel appointment
- `PUT /appointments/<pk>/reschedule/` - reschedule appointment
- `GET/PUT /profile/` - fetch/update user profile

## Authentication & Authorization
- Default API auth: token authentication
- Most API routes require authenticated users (`IsAuthenticated`)
- Public routes: `/health_check/`, `/signup`, `/login/`, slot lookup route
- Admin panel uses Django session login and checks `is_admin`

## Environment Variables
Create a `.env` file in project root and define:
- `SECRET_KEY`
- `DEBUG` (`True` or `False`)
- `ALLOWED_HOSTS` (comma-separated)
- `DATABASE_URL`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

## Local Setup
1. Clone this repository to your local machine to get started quickly.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up `.env` with required values.
5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Create a super/admin user (if needed):
   ```bash
   python manage.py createsuperuser
   ```
7. Start development server:
   ```bash
   python manage.py runserver
   ```
8. To run the frontend, please navigate to the frontend repository on my GitHub and clone it to your local machine.
   [Frontend Repository](https://github.com/Alinps/Hospital_Appointment_Booking_App_Frontend-React.js-.git)
## Deployment Notes
- `procfile` runs Gunicorn:
  - `web: gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3`
- WhiteNoise is enabled for static assets in middleware.
- Cloudinary is configured as the default media storage backend.
- Global rate limiting uses local memory cache (single-instance friendly, not distributed).

## Logging
- App logs are written to `app.log`.
- Logger configuration includes console + file handlers.
- Custom app logger name used in views: `appointment_app`.

## Important Notes
- Model/class naming typo exists in code: `Appoinment` instead of `Appointment`.
- Some supporting files (`tests.py`, `admin.py`, `signals.py`) are currently minimal/commented.
- Template/UI and API coexist in the same Django app (`adminapp`).
