
import sys
from django.utils.timezone import now
from django.template.defaultfilters import default
try:
    from django.db import models
except Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

from django.conf import settings
import uuid


# Instructor model
class Instructor(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField()

    def __str__(self):
        return self.user.username


# Learner model
class Learner(models.Model):
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    STUDENT = 'student'
    DEVELOPER = 'developer'
    DATA_SCIENTIST = 'data_scientist'
    DATABASE_ADMIN = 'dba'
    OCCUPATION_CHOICES = [
        (STUDENT, 'Student'),
        (DEVELOPER, 'Developer'),
        (DATA_SCIENTIST, 'Data Scientist'),
        (DATABASE_ADMIN, 'Database Admin')
    ]
    occupation = models.CharField(
        null=False,
        max_length=20,
        choices=OCCUPATION_CHOICES,
        default=STUDENT
    )
    social_link = models.URLField(max_length=200)

    def __str__(self):
        return self.user.username + "," + \
               self.occupation


# Course model
class Course(models.Model):
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    name = models.CharField(null=False, max_length=30, default='online course')
    image = models.ImageField(upload_to='course_images/')
    description = models.CharField(max_length=1000)
    pub_date = models.DateField(null=True)
    instructors = models.ManyToManyField(Instructor)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment')
    total_enrollment = models.IntegerField(default=0)
    is_enrolled = False

    def __str__(self):
        return "Name: " + self.name + "," + \
               "Description: " + self.description


# Lesson model
class Lesson(models.Model):
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    title = models.CharField(max_length=200, default="title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()


# Enrollment model
class Enrollment(models.Model):
    AUDIT = 'audit'
    HONOR = 'honor'
    BETA = 'BETA'
    COURSE_MODES = [
        (AUDIT, 'Audit'),
        (HONOR, 'Honor'),
        (BETA, 'BETA')
    ]
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(max_length=5, choices=COURSE_MODES, default=AUDIT)
    rating = models.FloatField(default=5.0)

class Question(models.Model):
    '''Used to persist question content for a course'''
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    text = models.CharField(max_length=200)
    grade=models.FloatField(default=1.0)
    course= models.ForeignKey(Course, on_delete=models.CASCADE)
    def choices_correct_ids(self):
        selected_list=[]
        for correct in self.choice_set.filter(is_correct=True):
            selected_list.append(correct.id)
        return selected_list
    
    def choices_not_correct_ids(self):
        selected_list=[]
        for correct in self.choice_set.filter(is_correct=False):
            selected_list.append(correct.id)
        return selected_list
    
    def choices_ids(self):
        selected_list=[]
        for correct in self.choice_set.all():
            selected_list.append(correct.id)
        return selected_list
        
    def classification(self, selected_ids):
        classification = {"selected_but_false":[],
                          "selected_and_true":[],
                          "not_selected_and_false":[],
                          "not_selected_but_true":[]}     
        selected_ids =   [id for id in selected_ids if id in   self.choices_ids()]
        not_selected_id = [id for id in self.choices_ids() if id not in set(selected_ids)]
        
        classification["selected_but_false"] = [id for id in selected_ids if id  in set(self.choices_not_correct_ids())]
        classification["selected_and_true"] = [id for id in selected_ids if id  in set(self.choices_correct_ids())]
        classification["not_selected_and_false"] = [id for id in not_selected_id if id  in set(self.choices_not_correct_ids())]
        classification["not_selected_but_true"] = [id for id in not_selected_id if id  in set(self.choices_correct_ids())]
        return classification
    
    def is_get_score(self, selected_ids):
        all_answers = self.choice_set.filter(is_correct=True).count()
        selected_correct = self.choice_set.filter(is_correct=True, id__in=selected_ids).count()
        selected_not_correct =self.choice_set.filter(is_correct=False, id__in=selected_ids).count()
        if all_answers == selected_correct and selected_not_correct == 0:
            return True
        else:
            return False      
    
class Choice(models.Model):
    ''' Used to persist choice content for a question '''
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    text = models.CharField(max_length=200) 
    is_correct = models.BooleanField(default=False) 
    question= models.ForeignKey(Question, on_delete=models.CASCADE) 
    
class Submission(models.Model): 
    ''' Used to link an enrollment to multiples choices''' 
    id=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    enrollment=models.ForeignKey(Enrollment, on_delete=models.CASCADE) 
    choices = models.ManyToManyField(Choice)
    