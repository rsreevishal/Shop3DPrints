from django.urls import path, include
from api.views import *

urlpatterns = [
    path('', index, name='index'),
    path('about-us', standard_view('landing/about-us.html'), name='about-us'),
    path('faq', standard_view('landing/faq.html'), name='faq'),
    path(r'courses-offered/<str:category_id>', courses_offered, name='courses-offered'),
    path('course-details/<int:course_id>', course_details, name='course-details'),
    path('teach-with-us', standard_view('landing/teach-with-us.html'), name='teach-with-us'),
    path('book-trial', standard_view('landing/book-trial.html'), name='book-trial'),
    path('reg-form', instructor_reg_form, name='reg-form'),
    path('student', redirect_view('student-courses'), name='student'),
    path('student/course/<int:course_id>', student_course, name='student-course'),
    path('student/courses', student_courses, name='student-courses'),
    path('student/profile', student_profile, name='student-profile'),
    path('student/progress', student_progress, name='student-progress'),
    path('student/schedule/<int:user_id>', CalendarView.as_view(), name='student-schedule'),
    path('student/payment', student_payment_details, name='student-payment'),
    path('instructor', instructor_base, name='instructor'),
    path('instructor/<int:instructor_id>/class/schedule/<int:enrollment_id>', InstructorCalendarView.as_view(),
         name='instructor-class-schedule'),
    path('instructor/<int:instructor_id>/classes', instructor_classes, name='instructor-classes'),
    path('instructor/<int:instructor_id>/profile/edit/', update_instructor, name='instructor-profile-edit'),
    path('instructor/<int:instructor_id>/class/material', instructor_material, name='instructor-class-material'),
    path('instructor/<int:instructor_id>/class/assignment', instructor_student_assignment,
         name='instructor-class-assignment'),
    path('instructor/<int:instructor_id>/class/student/works/<int:enrollment_id>', instructor_student_works,
         name='instructor-student-works'),
    path('instructor/<int:instructor_id>/event/<int:event_id>/edit/status', update_event_status,
         name='event_edit_status'),
    path('api/login', login, name='login'),
    path('api/register', register, name='register'),
    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('api/logout', logout, name='logout'),
    path('api/checkout', checkout, name='checkout'),
    path('api/checkout_monthly_payment', checkout_monthly_payment, name="checkout_monthly_payment"),
    path('api/checkout-webhook', checkout_webhook, name='checkout-webhook'),
    path('api/query', email_query, name='query'),
    path('api/password_reset/', include('django_rest_passwordreset.urls'), name='password_reset'),
    path('api/instructor_register', instructor_register, name="instructor_register"),
    path('api/instructor/<int:instructor_id>/update/skills/', instructor_skill_update, name='instructor_skill_update'),
    path('event/new', update_event, name='event_new'),
    path('event/edit/<int:event_id>', update_event, name='event_edit'),
    path('set_timezone/', set_timezone, name='set_timezone')
]
