from django.urls import path

from api.views import *

urlpatterns = [
    path('', index, name='index'),
    path('about-us', standard_view('landing/about-us.html'), name='about-us'),
    path('faq', standard_view('landing/faq.html'), name='faq'),
    path('courses-offered', standard_view('landing/courses-offered.html'), name='courses-offered'),
    path('course-details', standard_view('landing/course-details.html'), name='course-details'),
    path('teach-with-us', standard_view('landing/teach-with-us.html'), name='teach-with-us'),
    path('book-trial', standard_view('landing/book-trial.html'), name='book-trial'),
    path('student', standard_view('student/student.html'), name='student'),
    # Template: path('template_name', standard_view('template_name.html'), name='template_name')
]
