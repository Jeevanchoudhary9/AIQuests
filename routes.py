import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from sqlalchemy import distinct
from app import app
from functools import wraps
from models import db, User, Questions, Plus_ones, Answers,Votes,Organizations,Moderators,Labels,Invites
import random
import ollama
import re
import humanize
from transformers import BertTokenizer, BertModel
import torch
import io
import random
import string

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def get_bert_embedding(text):
    """
    Generate BERT embedding for the given text.
    """
    inputs = bert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = bert_model(**inputs)
    # Use the mean of the last hidden state as the embedding
    embedding = outputs.last_hidden_state.mean(dim=1).detach().numpy()
    return embedding


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



@app.route('/')
def land():
    return render_template('Landingpage.html')

@app.route('/home')
# @auth_required
def index():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]


    return render_template('home.html', questions=questions)
    # return render_template('home.html')


@app.route('/UserManager')
def userManager():
    invites = Invites.query.all()
    return render_template('OrgUserManager.html',invites=invites)

@app.route('/invite_user',methods=["POST"])
def inviteUser():
    email = request.form.get('email')
    role = request.form.get('role')
    orgid = 1
    date = datetime.datetime.now()

    if email is None or role is None:
        flash('Please fill the required fields')
        return redirect(url_for('userManager'))
    elif Invites.query.filter_by(email=email).first():
        flash('Email already exists')
        return redirect(url_for('userManager'))

    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(characters) for _ in range(16))
    print(email,role,code)
    invite = Invites(email=email,role=role,code=code,orgid=orgid,date=date)
    db.session.add(invite)
    db.session.commit()


    return render_template('OrgUserManager.html')


# @app.route('/profile')
# @auth_required
# def profile():
#     profile=(User.query.filter_by(userid=session['user_id']).first()).profileid
#     return render_template('profile.html',profile=Profile.query.filter_by(profileid=profile).first(),user=User.query.filter_by(userid=session['user_id']).first(),nav="profile")


# @app.route('/profile',methods=["POST"])
# @auth_required
# def profile_post():
#     user=User.query.filter_by(userid=session['user_id']).first()
#     address=request.form.get('address')
#     cpassword=request.form.get('cpassword')
#     npassword=request.form.get('npassword')
#     profile=Profile.query.filter_by(profileid=user.profileid).first()

#     if address is None :
#         flash('Please fill the required fields')
#         return redirect(url_for('profile'))
#     elif address!='' and cpassword=='' and npassword=='':
#         profile.address=address
#         db.session.commit()
#     elif address!='' or cpassword!='' or npassword!='':
#         if not user.check_password(cpassword):
#             flash('Please check your password and try again.')
#             return redirect(url_for('profile'))
#         if npassword == cpassword:
#             flash('New password cannot be same as old password')
#             return redirect(url_for('profile'))
#         else:
#             user.password=npassword
#             profile.address=address
#             db.session.commit()
#     flash(['Profile updated successfully','success'])
#     return redirect(url_for('profile'))


@app.route('/login')
def login():
    return render_template('Login.html')


@app.route('/login', methods=["POST"])
def login_post():
    username=request.form.get('email')
    password=request.form.get('password')

    if username=='' or password=='':
        flash('Please fill the required fields')
        return redirect(url_for('login'))
    
    user=User.query.filter_by(username=username).first()
    org=Organizations.query.filter_by(orgemail=username).first()
    print(username,password)
    if not user and not org:
        flash('Please check your username and try again.')
        return redirect(url_for('login'))
    if not user.check_password(password) and not org.check_password(password):
        flash('Please check your password and try again.')
        return redirect(url_for('login'))
    #after successful login   
    session['user_id']=user.userid
    return redirect(url_for('index'))



@app.route('/register',methods=["GET"])
def register():
    return render_template('register.html')

@app.route('/register/organization',methods=["GET"])
def orgregister():
    return render_template('organizationRegister.html')

@app.route('/image/<int:id>')
def get_image(id):
    image = Organizations.query.get(id)
    return send_file(io.BytesIO(image.orglogo), mimetype='image/jpeg')

@app.route('/register/organization',methods=["POST"])
def orgregister_post():
    orgname = request.form.get('orgname')
    orgemail = request.form.get('orgemail')
    orgphone = request.form.get('orgphone')
    orgpassword = request.form.get('orgpassword')
    confirmpassword = request.form.get('confirmpassword')
    orgwebsite = request.form.get('orgwebsite')
    orgtype = request.form.get('orgtype')
    orgdesc = request.form.get('orgdesc')
    created_at = datetime.datetime.now()
    orglogo = request.files['orglogo'].read()


    print(orgname,orglogo,orgemail,orgphone,orgpassword,confirmpassword,orgwebsite,orgtype,orgdesc,created_at)

    if orgname is None or orgemail is None or orgpassword is None or confirmpassword is None or orgwebsite is None:
        flash('Please fill the required fields')
        return redirect(url_for('orgregister'))
    elif orgpassword!=confirmpassword:
        flash('Passwords do not match')
        return redirect(url_for('orgregister'))
    elif Organizations.query.filter_by(orgemail=orgemail).first():
        flash('Email already exists')
        return redirect(url_for('orgregister'))
    else:
        organization=Organizations(orgname=orgname,orglogo=orglogo,orgemail=orgemail,orgphone=orgphone,orgpassword=orgpassword,orgwebsite=orgwebsite,orgtype=orgtype,orgdesc=orgdesc,created_at=created_at)
        db.session.add(organization)
        db.session.commit()
        flash(['You have successfully registered','success'])
        return redirect(url_for('login'))


@app.route('/register',methods=["POST"])
def register_post():
    firstname=request.form.get('first_name')
    lastname=request.form.get('last_name')
    email=request.form.get('email')
    password=request.form.get('password')
    confirmpassword=request.form.get('confirmpassword')
    username=request.form.get('username')
    invitecode=request.form.get('invitecode')

    if username is None or password is None or email is None or  firstname is None or lastname is None or invitecode is None:
        flash('Please fill the required fields')
        return redirect(url_for('register'))
    
    if password!=confirmpassword:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('register'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists')
        return redirect(url_for('register'))
    
    if not Invites.query.filter_by(code=invitecode).first():
        flash('Invalid invite code')
        return redirect(url_for('register'))
    
    invite = Invites.query.filter_by(code=invitecode).first()
    if invite.email != email:
        flash('Email does not match the invite code')
        return redirect(url_for('register'))
    
    orgid=invite.orgid
    
    user=User(firstname=firstname,lastname=lastname,username=username,email=email,password=password,organization=orgid)
    invite.registered = True
    db.session.add(user)
    db.session.commit()
    flash(['You have successfully registered','success'])
    
    return redirect(url_for('login'))

# @app.route('/questiondetail',methods=['GET'])
# def ques():
#     return render_template('QuestionDetails.html') 

# @app.route('/questions', methods=['GET', 'POST', 'DELETE', 'PUT'])
# def questions():

#     if request.method=='POST': # Add the question
#         question=request.form.get('question')
#         question=questions(question=question,userid=session['user_id'].first(), plus_one=0, official_answer="")
#         db.session.add(question)
#         db.session.commit()
#         flash(['Question added successfully','success'])
#         return redirect(url_for('questions'))
    

#     elif request.method=='DELETE': # Delete the question
#         question_id=request.form.get('question_id')
#         if question_id is None:
#             flash('Please fill the required fields')
#             return redirect(url_for('questions'))
#         question=questions.query.filter_by(questionid=question_id).first()
#         db.session.delete(question)
#         db.session.commit()
#         flash(['Question deleted successfully','success'])
#         return redirect(url_for('questions'))
    

#     elif request.method=='PUT': # Plus one the question
#         # Plus one
#         question_id=request.form.get('question_id')
#         # If already plus one remove plus one
#         if plus_ones.query.get(question_id = int(question_id), userid = int(session['user_id'])):
#             plus_ones.query.filter_by(question_id = int(question_id), userid = int(session['user_id'])).delete()
#             questions.query.filter_by(questionid=question_id).first().plus_one-=1
#             db.session.commit()
            
    

#     else: # Get all questions
#         question_whole=[]
#         questions = Questions.query.all()
#         for question in questions:
#             question_whole.append(question.serializer())
#         print(question_whole)
#         return render_template('questions.html',questions=question_whole)
    
# @app.route('/questions_details/<int:question_id>', methods=['GET', 'POST'])
# def questions_details(question_id):

#     if request.method=='POST':
#         answer=request.form.get('answer_body')
#         isAnsOfficial = True if request.form.get('official_status') == "yes" else False
        
#         if answer is None:
#             flash('Please fill the required fields')
#             return redirect(url_for('questions'))
        
#         newAnswer=answers(answer=answer, questionid=question_id, userid=session['user_id'],
#                        upvotes=0, downvotes=0, marked_as_official=isAnsOfficial, date=datetime.datetime.now())
#         db.session.add(newAnswer)
#         db.session.commit()

#         if isAnsOfficial:
#             question = Questions.query.filter_by(questionid=question_id).first()
#             question_text = question.question_title + ' ' + question.question_detail
#             question.official_answer = answers.query.filter_by(questionid=question_id, marked_as_official=True).first().answerid

#             # Generate BERT embedding for the question text
#             inputs = tokenizer(question_text, return_tensors='pt', truncation=True, padding=True)
#             with torch.no_grad():
#                 outputs = model(**inputs)
#                 embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

#             # Create the official answer entry
#             official_entry = OfficialAnswer(
#                 questionid=question_id,
#                 embedding=str(embedding),
#                 question_text=question_text,
#                 answer_text=answer
#             )
#             db.session.add(official_entry)
#             db.session.commit()


#         flash(['Answer added successfully','success'])
#         return redirect(url_for('questions'))
            

#     else: # Get all questions
#         questions=Questions.query.filter_by(questionid=question_id).first()
#         print(questions.serializer())
        
#         timestamp = questions.date

#         # Get the current time
#         now = datetime.datetime.now()

#         # Calculate the relative time
#         relative_time = humanize.naturaltime(now - timestamp)
#         user_question=User.query.filter_by(userid=questions.userid).first()

#         answer_all=answers.query.filter_by(questionid=question_id).all()
#         answers_list=[]
#         for answer in answer_all:
#             answers_list.append(answer.serializer())
#         print(answers_list)

#         return render_template('QuestionDetails.html',question=questions.serializer(),relative_time=relative_time,user_question=user_question,answers=answers_list)


# @auth_required
@app.route('/ask_question', methods=["GET", "POST"])
def ask_question():

    if request.method == "POST":
        # Get form data
        title = request.form.get('title')
        body = request.form.get('body')
        tags = request.form.get('tags')

        question=request.form.get('question')
        prompt = "Answer the given question: " + title + body + "from" + tags + ' in format {"question": "The same question", "answer": "Your answer"} the answer should be in the format {"question": "The same question", "answer": "Your answer"}'
        response = ollama.generate(model='llama3.2', prompt=prompt)
        print(response["response"])
        
        # Parse json
        regex = r'{"question": "(.*?)", "answer": "(.*?)"}'
        matches = re.findall(regex, response["response"])
        print(matches)
        answer = matches[0]

        # Basic validation to check if all fields are filled
        if not title or not body or not tags:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('ask_question'))
        
        # Optional: Process and store tags (you may choose to split them by commas or space)
        tag_list = tags.split()
        tag_objects = []
        for tag in tag_list:
            tag_objects.append(tag)
        
        random_id = random.randint(1000, 9999)

        # Create and save the question
        new_question = Questions(
            questionid = random_id,
            question_title=title,
            question_detail=body,
            date=datetime.datetime.now(),
            official_answer="",
            userid=session.get('user_id'),
            tags =tag_objects
        )

        new_answer = Answers(
            answer=answer[1],
            questionid = random_id,
            userid=2,
            upvotes=0,
            downvotes=0,
            marked_as_official=False,
            date=datetime.datetime.now()
        )

        db.session.add(new_question)
        db.session.add(new_answer)
        db.session.commit()

        flash(['Your question has been posted successfully!', 'success'])
        return redirect(url_for('ask_question'))  # Redirect to the same page or another page
    return render_template('AskQuestion.html')


# @app.route('/answers', methods=['GET', 'POST', 'DELETE', 'PUT'])
# def answers_route():
    
#         if request.method=='POST': # Add the answer
#             question_id=request.form.get('question_id')
#             answer=request.form.get('answer')
#             if question_id is None or answer is None:
#                 flash('Please fill the required fields')
#                 return redirect(url_for('questions'))
#             answer=answers(answer=answer,questionid=question_id,userid=session['user_id'].first(), upvotes=0, downvotes=0)
#             db.session.add(answer)
#             db.session.commit()
#             flash(['Answer added successfully','success'])
#             return redirect(url_for('questions'))
        
#         elif request.method=='DELETE': # Delete the answer
#             answer_id=request.form.get('answer_id')
#             if answer_id is None:
#                 flash('Please fill the required fields')
#                 return redirect(url_for('questions'))
#             answer=answers.query.filter_by(answerid=answer_id).first()
#             db.session.delete(answer)
#             db.session.commit()
#             flash(['Answer deleted successfully','success'])
#             return redirect(url_for('questions'))
        
#         elif request.method=='PUT': # Vote the answer
#             answer_id=request.form.get('answer_id')
#             vote = request.form.get('vote') # +1 for upvote and -1 for downvote, +10 for official answer
#             answer=answers.query.filter_by(answerid=answer_id).first()

#             if vote == 1:
#                 answer.upvotes+=1

#             elif vote == 10:
#                 answer.marked_as_official=True
#                 question = questions.query.filter_by(questionid=answer.questionid).first()
#                 question.official_answer = answer.answer

#             elif vote == -1:
#                 answer.downvotes+=1

#             db.session.commit()
#             flash(['Voted successfully','success'])
#             return redirect(url_for('questions'))



# @app.route('/logout')
# def logout():
#     session.pop('user_id',None)
#     return redirect(url_for('login'))