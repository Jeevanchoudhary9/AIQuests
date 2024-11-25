import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import distinct
from app import app
from functools import wraps
from models import db, User, Profile, Questions, answers, plus_ones
import random


def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner


def manager_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        if User.query.filter_by(userid=session['user_id']).first().role!="manager":
            flash('You are not authorized to access this page')
            return redirect(url_for('homepage'))
        return func(*args, **kwargs)
    return inner


@app.route('/home')
# @auth_required
def homepage():
    return render_template('index.html',user=User.query.filter_by(userid=session['user_id']).first(),nav="dashboard")


@app.route('/')
# @auth_required
def index():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]

    return render_template('home.html', questions=questions)
    # return render_template('home.html')


@app.route('/profile')
@auth_required
def profile():
    profile=(User.query.filter_by(userid=session['user_id']).first()).profileid
    return render_template('profile.html',profile=Profile.query.filter_by(profileid=profile).first(),user=User.query.filter_by(userid=session['user_id']).first(),nav="profile")


@app.route('/profile',methods=["POST"])
@auth_required
def profile_post():
    user=User.query.filter_by(userid=session['user_id']).first()
    address=request.form.get('address')
    cpassword=request.form.get('cpassword')
    npassword=request.form.get('npassword')
    profile=Profile.query.filter_by(profileid=user.profileid).first()

    if address is None :
        flash('Please fill the required fields')
        return redirect(url_for('profile'))
    elif address!='' and cpassword=='' and npassword=='':
        profile.address=address
        db.session.commit()
    elif address!='' or cpassword!='' or npassword!='':
        if not user.check_password(cpassword):
            flash('Please check your password and try again.')
            return redirect(url_for('profile'))
        if npassword == cpassword:
            flash('New password cannot be same as old password')
            return redirect(url_for('profile'))
        else:
            user.password=npassword
            profile.address=address
            db.session.commit()
    flash(['Profile updated successfully','success'])
    return redirect(url_for('profile'))


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login', methods=["POST"])
def login_post():
    username=request.form.get('email')
    password=request.form.get('password')

    if username=='' or password=='':
        flash('Please fill the required fields')
        return redirect(url_for('login'))
    
    user=User.query.filter_by(uname=username).first()
    print(username,password)
    if not user:
        flash('Please check your username and try again.')
        return redirect(url_for('login'))
    if not user.check_password(password):
        flash('Please check your password and try again.')
        return redirect(url_for('login'))
    #after successful login   
    session['user_id']=user.userid
    return redirect(url_for('index'))



@app.route('/register',methods=["GET"])
def register():
    return render_template('register.html')


@app.route('/register',methods=["POST"])
def register_post():
    firstname=request.form.get('first_name')
    lastname=request.form.get('last_name')
    email=request.form.get('email')
    password=request.form.get('password')
    username=email

    if username is None or password is None or email is None :
        flash('Please fill the required fields')
        return redirect(url_for('register'))
    
    if User.query.filter_by(uname=username).first():
        flash('Username already exists')
        return redirect(url_for('register'))
    
    def user(username, password, role="customer",Profileid=None):
        return User(uname=username,password=password,profileid=Profileid,role=role)
    
    profile=Profile(firstname=firstname,lastname=lastname,email=email)
    db.session.add(profile)
    db.session.commit()
    pid=Profile.query.filter_by(firstname=firstname,lastname=lastname,email=email).first().profileid
    user=user(username,password,Profileid=pid)
    db.session.add(user)
    db.session.commit()
    flash(['You have successfully registered','success'])
    
    return redirect(url_for('login'))

@app.route('/questiondetail',methods=['GET'])
def ques():
    return render_template('QuestionDetails.html') 

@app.route('/questions', methods=['GET', 'POST', 'DELETE', 'PUT'])
def questions():

    if request.method=='POST': # Add the question
        question=request.form.get('question')
        if question is None:
            flash('Please fill the required fields')
            return redirect(url_for('questions'))
        question=questions(question=question,userid=session['user_id'].first(), plus_one=0, official_answer="")
        db.session.add(question)
        db.session.commit()
        flash(['Question added successfully','success'])
        return redirect(url_for('questions'))
    

    elif request.method=='DELETE': # Delete the question
        question_id=request.form.get('question_id')
        if question_id is None:
            flash('Please fill the required fields')
            return redirect(url_for('questions'))
        question=questions.query.filter_by(questionid=question_id).first()
        db.session.delete(question)
        db.session.commit()
        flash(['Question deleted successfully','success'])
        return redirect(url_for('questions'))
    

    elif request.method=='PUT': # Plus one the question
        # Plus one
        question_id=request.form.get('question_id')
        # If already plus one remove plus one
        if plus_ones.query.get(question_id = int(question_id), userid = int(session['user_id'])):
            plus_ones.query.filter_by(question_id = int(question_id), userid = int(session['user_id'])).delete()
            questions.query.filter_by(questionid=question_id).first().plus_one-=1
            db.session.commit()
            
    

    else: # Get all questions
        questions = Questions.query.all()
        serialized_questions = [question.serialize() for question in questions]
        print(serialized_questions)
        return render_template('questions.html')
    

@auth_required
@app.route('/ask_question', methods=["GET", "POST"])
def ask_question():
    if request.method == "POST":
        # Get form data
        title = request.form.get('title')
        body = request.form.get('body')
        tags = request.form.get('tags')

        # Basic validation to check if all fields are filled
        if not title or not body or not tags:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('ask_question'))
        
        # Optional: Process and store tags (you may choose to split them by commas or space)
        tag_list = tags.split()
        tag_objects = []
        

        # Create and save the question
        new_question = Questions(
            question_title=title,
            question_detail=body,
            date=datetime.datetime.now(),
            # Assuming you have a user object from the session or passed in
            userid=session.get('user_id'),  # You can adjust this based on your authentication

        )

        db.session.add(new_question)
        db.session.commit()

        flash(['Your question has been posted successfully!', 'success'])
        return redirect(url_for('ask_question'))  # Redirect to the same page or another page

    return render_template('AskQuestion.html') 



@app.route('/answers', methods=['GET', 'POST', 'DELETE', 'PUT'])
def answers():
    
        if request.method=='POST': # Add the answer
            question_id=request.form.get('question_id')
            answer=request.form.get('answer')
            if question_id is None or answer is None:
                flash('Please fill the required fields')
                return redirect(url_for('questions'))
            answer=answers(answer=answer,questionid=question_id,userid=session['user_id'].first(), upvotes=0, downvotes=0)
            db.session.add(answer)
            db.session.commit()
            flash(['Answer added successfully','success'])
            return redirect(url_for('questions'))
        
        elif request.method=='DELETE': # Delete the answer
            answer_id=request.form.get('answer_id')
            if answer_id is None:
                flash('Please fill the required fields')
                return redirect(url_for('questions'))
            answer=answers.query.filter_by(answerid=answer_id).first()
            db.session.delete(answer)
            db.session.commit()
            flash(['Answer deleted successfully','success'])
            return redirect(url_for('questions'))
        
        elif request.method=='PUT': # Vote the answer
            answer_id=request.form.get('answer_id')
            vote = request.form.get('vote') # +1 for upvote and -1 for downvote, +10 for official answer
            answer=answers.query.filter_by(answerid=answer_id).first()

            if vote == 1:
                answer.upvotes+=1

            elif vote == 10:
                answer.marked_as_official=True
                question = questions.query.filter_by(questionid=answer.questionid).first()
                question.official_answer = answer.answer

            elif vote == -1:
                answer.downvotes+=1

            db.session.commit()
            flash(['Voted successfully','success'])
            return redirect(url_for('questions'))



@app.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('login'))

