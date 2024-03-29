from django.contrib import admin

# Register your models here.
from courses.models import Course, Lesson, Instructor, Learner, Question, Choice, Submission



class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5
    
class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 5

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 5
    show_change_link = True

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'grade', 'course')
    inlines = [ChoiceInline]

# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']

class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


# <HINT> Register Question and Choice models here

admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question,QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission)