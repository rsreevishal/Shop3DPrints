from django.urls import path

from api.views import standard_view

urlpatterns = [
    path('', standard_view('index.html'), name='index'),
    path('about-us', standard_view('about-us.html'), name='about-us'),
    path('faq', standard_view('faq.html'), name='faq'),
    path('courses-offered', standard_view('courses-offered.html'), name='courses-offered'),
    path('course-details', standard_view('course-details.html'), name='course-details'),
    path('teach-with-us', standard_view('teach-with-us.html'), name='teach-with-us'),
    path('book-trial', standard_view('book-trial.html'), name='book-trial'),
    # Template: path('template_name', standard_view('template_name.html'), name='template_name')
]
