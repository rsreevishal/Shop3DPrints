from django.contrib import admin

from api.models import *

admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(ExamGrade)
admin.site.register(Exam)
admin.site.register(Instructor)
admin.site.register(ProjectSubmission)
admin.site.register(Project)
admin.site.register(Purchase)
admin.site.register(Student)
admin.site.register(Subcategory)
admin.site.register(Speciality)
admin.site.register(SpecialityLevel)
admin.site.register(InstructorSpeciality)
admin.site.register(AvailableDays)
admin.site.register(AvailableTimes)
admin.site.register(CourseTimeSlot)
admin.site.register(InstructorTimeSlot)
admin.site.register(CourseInstructor)
