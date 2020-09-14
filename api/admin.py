from django.contrib import admin

from api.models import Student, Course, Exam, Project, ExamGrade, ProjectSubmission

admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Exam)
admin.site.register(ExamGrade)
admin.site.register(Project)
admin.site.register(ProjectSubmission)
