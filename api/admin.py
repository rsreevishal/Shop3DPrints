from django.contrib import admin

from api.models import Course, Enrollment, ExamGrade, Exam, Instructor, ProjectSubmission, Project, Student

admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(ExamGrade)
admin.site.register(Exam)
admin.site.register(Instructor)
admin.site.register(ProjectSubmission)
admin.site.register(Project)
admin.site.register(Student)
