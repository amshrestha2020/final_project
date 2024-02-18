from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import math
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'courses/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("courses:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'courses/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('courses:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'courses/user_login_bootstrap.html', context)
    else:
        return render(request, 'courses/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('courses:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'courses/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'courses/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='courses:course_details', args=(course.id,)))

def extract_answers_request(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    return submitted_anwsers

def extract_answers_submisison(submission):
    submitted_anwsers = []
    for choice in submission.choices.all():
            choice_id = choice.id
            submitted_anwsers.append(choice_id)
    return submitted_anwsers




def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    if user.is_authenticated:
        enrollment = Enrollment.objects.get(user=user, course=course)
        my_submission = Submission.objects.create(enrollment=enrollment)
        submitted_anwsers=extract_answers_request(request)
        for submitted_anwser in submitted_anwsers:
            my_submission.choices.add(Choice.objects.get(id=submitted_anwser))
    context = {"course_id":course_id,"submission.id":my_submission.id}
    return show_exam_result(request, course_id, my_submission.id)


def show_exam_result(request, course_id, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    course = get_object_or_404(Course, pk=course_id)
    selected_choices_id_list=extract_answers_submisison(submission)
    questions=Question.objects.filter(course=course.id)
    context = {}
    context["submission"]=submission
    context["course"]=course
    context["total_score"]=0.0
    context['score']=0.0
    context["questions"]=[]
    for question in questions:
        question_dict={}
        classification=question.classification(selected_choices_id_list)
        question_dict["text"]=question.text
        context["total_score"]=context["total_score"]+question.grade
        context['score']=context['score']+question.grade/len(question.choices_correct_ids())*max(0,
            len(classification["selected_and_true"])-
            2*len(classification["selected_but_false"]))
        question_dict["choices"]=[]
        for choice_id in classification["selected_and_true"]:
            question_dict["choices"].append({"status":"selected_and_true","text":Choice.objects.get(id=choice_id).text})
        for choice_id in classification["selected_but_false"]:
            question_dict["choices"].append({"status":"selected_but_false","text":Choice.objects.get(id=choice_id).text}) 
        for choice_id in classification["not_selected_but_true"]:
            question_dict["choices"].append({"status":"not_selected_but_true","text":Choice.objects.get(id=choice_id).text})
        for choice_id in classification["not_selected_and_false"]:
            question_dict["choices"].append({"status":"not_selected_and_false","text":Choice.objects.get(id=choice_id).text})
        if len(classification["not_selected_but_true"])>0:
            question_dict["choices"].append({"status":"missing"})
        context["questions"].append(question_dict)
    context["total_per_cent"]=context['score']/context["total_score"]
    print(str(context['score'])+"/"+str(context["total_score"]))
    print(context)
    return render(request, 'courses/exam_result_bootstrap.html', context)

