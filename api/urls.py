from django.urls import path

from api.views import *

urlpatterns = [
    path('', index, name='index'),
    path('about-us', standard_view('landing/about-us.html'), name='about-us'),
    path('faq', standard_view('landing/faq.html'), name='faq'),
    path(r'courses-offered/<str:category_id>', courses_offered, name='courses-offered'),
    path('course-details/<int:course_id>', course_details, name='course-details'),
    path('teach-with-us', standard_view('landing/teach-with-us.html'), name='teach-with-us'),
    path('book-trial', standard_view('landing/book-trial.html'), name='book-trial'),
    path('reg-form', standard_view('landing/reg-form.html'), name='reg-form'),
    path('student', redirect_view('student-courses'), name='student'),
    path('student/course/<int:course_id>', student_course, name='student-course'),
    path('student/courses', student_courses, name='student-courses'),
    path('student/profile', student_profile, name='student-profile'),
    path('student/progress', student_progress, name='student-progress'),
    path('student/schedule', standard_view('student/schedule.html'), name='student-schedule'),
    path('api/login', login, name='login'),
    path('api/register', register, name='register'),
    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('api/logout', logout, name='logout'),
    path('api/checkout', checkout, name='checkout'),
    path('api/checkout-webhook', checkout_webhook, name='checkout-webhook'),
    path('api/query', email_query, name='query'),
    # Template: path('template_name', standard_view('template_name.html'), name='template_name')
]
