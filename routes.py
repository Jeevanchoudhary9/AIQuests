import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from sqlalchemy import distinct
from app import app
from functools import wraps
from models import db, User, Questions, Plus_ones, Answers,Votes,Organizations,Moderators,Labels,Invites
import random
import ollama
import re
import humanize
# from transformers import BertTokenizer, BertModel
from werkzeug.security import generate_password_hash, check_password_hash
import torch
import io
import random
import string
from functools import wraps
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import threading
from flask import jsonify

# tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
# model = BertModel.from_pretrained('bert-base-uncased')

# def get_bert_embedding(text):
#     """
#     Generate BERT embedding for the given text.
#     """
#     inputs = bert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
#     outputs = bert_model(**inputs)
#     # Use the mean of the last hidden state as the embedding
#     embedding = outputs.last_hidden_state.mean(dim=1).detach().numpy()
#     return embedding


def role_required(role=None):
    """
    A decorator to ensure the user is authenticated and optionally has a specific role.
    :param role: (Optional) The required role to access the route. If None, return the role of the current user.
    """
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to continue')
                return redirect(url_for('index'))
            
            user = User.query.filter_by(userid=session['user_id']).first()
            if not user:
                flash('User not found. Please login again.')
                return redirect(url_for('index'))
            
            if role:
                if user.role != role:
                    flash('You are not authorized to access this page')
                    return redirect(url_for('index'))
            else:
                # Pass the user's role to the wrapped function
                kwargs['user_role'] = user.role
            
            return func(*args, **kwargs)
        return inner
    return decorator


def send_email(to_email, subject, html_content,attachment=None):
    # Gmail SMTP server details
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Gmail SMTP port

    # Sender's Gmail address and password
    sender_email = 'ai.aiquest@gmail.com' #enter your email
    sender_password = 'stpa vqvq oqog fykk' #enter code > you can get it at https://myaccount.google.com/apppasswords or search for "app password" in google account > create a new app code > format "wxyz wxyz wxyz wxyz" > enter it here

    # Create a MIME multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    if attachment:
        # Attach file
        # part = MIMEBase('application', 'octet-stream')
        # part.set_payload(open(attachment, 'rb').read())
        # encoders.encode_base64(part)
        # part.add_header('Content-Disposition', f'attachment; filename={attachment}')
        # msg.attach(part)

        pdf_part = MIMEApplication(attachment, _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename='report.pdf')
        msg.attach(pdf_part)


    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html','utf-8'))

    

    # Connect to Gmail's SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Start TLS encryption
    server.login(sender_email, sender_password)  # Login to Gmail

    # Send email
    server.sendmail(sender_email, to_email, msg.as_string())

    # Close SMTP connection
    server.quit()


# NOTE: This route takes to landing page
@app.route('/')
def index():
    return render_template('Landingpage.html')


# NOTE: Organization dashboard
@app.route('/dashboard/organization')
def organization_dashboard():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]

    return render_template('OrganizationDashboard.html', questions=questions)


# NOTE: 
@app.route('/dashboard/moderator')
@role_required('moderator')
def moderator_dashboard():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]

    return render_template('expert_dahboard.html', questions=questions)


@app.route('/dashboard/user')
@role_required('user')
def user_dashboard():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]
    
    return render_template('user_dashboard.html', questions=questions)


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

    # Format the code as XXXX XXXX XXXX XXXX
    code = ' '.join([code[i:i+4] for i in range(0, len(code), 4)])

    print(email,role,code)
    invite = Invites(email=email,role=role,code=code,orgid=orgid,date=date)
    db.session.add(invite)
    db.session.commit()
    flash(['Invited successfully','success'])
    register_url=url_for('register', code=code,email=email, _external=True)
    browser_url = url_for('invitedmail', code=code,email=email,role=role, _external=True)
    print(register_url)

    # email sent part 
    email = email
    print(email)
    subject = "You've been invited to join AIQuest"

    body = render_template('emailinvite.html',email=email,code=code,role=role,register_url=register_url,browser_url=browser_url)

    # Start a new thread to send the email
    # thread = threading.Thread(target=send_email, args=(email, subject, body))
    # thread.start()
    flash(['Mail sent successfully','success'])

    return redirect(url_for('userManager'))


@app.route('/inivtedmail')
def invitedmail(email=None,code=None,role=None):
    email = request.args.get('email')
    code = request.args.get('code')
    role = request.args.get('role')
    print(email,code,role)
    # browser user
    if not (email is None and code is None and role is None):
        register_url=url_for('register', code=code,email=email, _external=True)
        print(register_url)
        return render_template('emailinvite.html',email=email,code=code,role=role,register_url=register_url,browser_url=None)
    # email user
    else:
        register_url=url_for('register', code="1234 5678 9012 3456",email="demo@gmail.com", _external=True)
        browser_url = url_for('invitedmail', code="1234 5678 9012 3456",email="demo@gmail.com",role="admin", _external=True)
        print(register_url)
        return render_template('emailinvite.html',email="demo@gmail.com",code="1234 5678 9012 3456",role="admin",register_url=register_url,browser_url=browser_url)



@app.route('/UserManager')
def userManager():
    invites = Invites.query.all()
    print(datetime.datetime.now())
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(characters) for _ in range(16))
    print(code)
    all_invites = []
    for invite in invites:
        all_invites.append(invite.serializer())
    return render_template('OrgUserManager.html',invites=all_invites)


@app.route('/UserManager', methods=['POST'])
def UserManager():
    try:
        # Get JSON data
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        if not data.get('email'):
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        if not data.get('orgid'):
            return jsonify({'success': False, 'message': 'Organization ID is required'}), 400
        if not data.get('role'):
            return jsonify({'success': False, 'message': 'Role is required'}), 400
        if not data.get('code'):
            return jsonify({'success': False, 'message': 'Code is required'}), 400
        if data.get('new_password') != data.get('confirm_password'):
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        try:
            orgid=str(Organizations.query.filter_by(orgid=data.get('orgid')).first().orgid)
        except:
            return jsonify({'success': False, 'message': 'Organization not found'}), 404
        if data.get('orgid') != orgid:
            return jsonify({'success': False, 'message': 'Organization not found'}), 404
        if data.get('registered') == 'False' and data.get('new_password') is not None or data.get('confirm_password') is not None:
            return jsonify({'success': False, 'message': 'Password is not required for unregistered users'}), 400
        if data.get('id') is None:
            return jsonify({'success': False, 'message': 'ID is required'}), 400
        
        if data.get('registered') == 'True':
            user = User.query.filter_by(userid=data['id']).first()
            user.email = data.get('email')
            user.orgid = data.get('orgid')
            invite = Invites.query.filter_by(inviteid=data['id']).first()
            invite.email = data.get('email')
            invite.role = data.get('role')
            invite.orgid = data.get('orgid')
            
            if data.get('new_password'):
                user.password = generate_password_hash(data.get('new_password'))

        elif data.get('registered') == 'False':
            invite = Invites.query.filter_by(inviteid=data['id']).first()
            invite.email = data.get('email')
            invite.role = data.get('role')
            invite.orgid = data.get('orgid')
            
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/UserManager', methods=['DELETE'])
def UserManager_delete():
    print(request.get_json())
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    if not data.get('inviteid'):
        return jsonify({'success': False, 'message': 'ID is required'}), 400
    if not data.get('registered'):
        return jsonify({'success': False, 'message': 'Registered status is required'}), 400
    if data.get('registered') == 'True':
        try:
            user = User.query.filter_by(email=data['email']).first()
            db.session.delete(user)
            db.session.commit()
        except:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
    elif data.get('registered') == 'False':
        invite = Invites.query.filter_by(inviteid=data['inviteid']).first()
        db.session.delete(invite)
        db.session.commit()

    return jsonify({'success': True})


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if role == 'user':
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.passhash, password):
                session['user_id'] = user.userid
                if user.role == 'moderator':
                    flash('Moderator login successful!')
                    return redirect(url_for('moderator_dashboard'))
                elif user.role == 'user':
                    flash('User login successful!')
                    return redirect(url_for('user_dashboard'))
            organization = Organizations.query.filter_by(orgemail=email).first()
            if organization:
                flash('Try switching to organization login')
            else:
                flash('Invalid user credentials. Please try again.')


        elif role == 'organization':
            organization = Organizations.query.filter_by(orgemail=email).first()
            if organization and check_password_hash(organization.orgpassword, password):
                session['org_id'] = organization.orgid
                flash('Organization login successful!')
                return redirect(url_for('dashboard'))
            flash('Invalid organization credentials. Please try again.')

    return render_template('login.html')

@app.route('/register',methods=["GET", "POST"])
def register(code=None, email=None):

    if request.method == 'GET':
        code = request.args.get('code')
        email = request.args.get('email')
        print(code)
    
    if request.method == 'POST':
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
        
        user=User(firstname=firstname,lastname=lastname,username=username,
                  email=email,passhash=generate_password_hash(password),organization=orgid)
        invite.registered = True
        db.session.add(user)
        db.session.commit()
        flash(['You have successfully registered','success'])
        
        return redirect(url_for('login'))

    return render_template('register.html',code=code,email=email)


@app.route('/register/organization',methods=["GET", "POST"])
def OrganizationRegister():

    if request.method == 'POST':
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
            organization=Organizations(orgname=orgname,orglogo=orglogo,orgemail=orgemail,orgphone=orgphone,
                                       orgpassword=generate_password_hash(orgpassword),orgwebsite=orgwebsite,orgtype=orgtype,orgdesc=orgdesc,created_at=created_at)
            db.session.add(organization)
            db.session.commit()
            flash(['You have successfully registered','success'])
            return redirect(url_for('login'))

    return render_template('organizationRegister.html')


@app.route('/image/<int:id>')
def get_image(id):
    image = Organizations.query.get(id)
    return send_file(io.BytesIO(image.orglogo), mimetype='image/jpeg')


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

@app.route('/<int:answer_id>/vote', methods=["POST"])
def vote(answer_id):
    if request.method != "POST":
        return jsonify({"error": "Invalid request"}), 400

    # Extract form data
    vote_type = int(request.form.get("vote"))  # 1 for upvote, -1 for downvote
    user_id = int(request.form.get("user_id"))  # TODO: Get it from Session ID

    # Fetch existing vote if it exists
    vote_entry = Votes.query.filter_by(answerid=answer_id, userid=user_id).first()

    if vote_entry:
        # Toggle the vote state or remove the vote
        if vote_entry.vote == vote_type:
            vote_entry.vote = 0  # Remove vote if it's the same as current
        else:
            vote_entry.vote = vote_type  # Update to the new vote type

        db.session.commit()
        return jsonify({"message": "Vote updated successfully", "vote": vote_entry.vote})

    # Check if the answer exists
    answer = Answers.query.filter_by(answerid=answer_id).first()
    if not answer:
        return jsonify({"error": "Answer not found"}), 404

    # Create a new vote entry
    new_vote = Votes(
        vote=vote_type,
        questionid=answer.questionid,
        answerid=answer_id,
        userid=user_id,
        date=datetime.datetime.now()
    )
    db.session.add(new_vote)
    db.session.commit()

    return jsonify({
        "message": "Vote created successfully",
        "vote": new_vote.vote,
        "questionid": new_vote.questionid
    })


@app.route('/<int:question_id>/plusone', methods=["POST"])
def plus_one(question_id):
    if request.method == "POST":
        user_id = int(request.form.get("user_id")) # TODO: Get it from Session ID
        
        plusone_entry = Plus_ones.query.filter_by(questionid=question_id, userid=user_id).first()
        
        if plusone_entry:
            db.session.delete(plusone_entry)
            db.session.commit()
            return jsonify({"message": "Plus one removed successfully", "status": "removed"})
        
        else:
            new_plusone = Plus_ones(
                questionid=question_id,
                userid=user_id,
                date=datetime.datetime.now()
            )
            db.session.add(new_plusone)
            db.session.commit()
            return jsonify({"message": "Plus one added successfully", "status": "added"})
    
    return jsonify({"error": "Invalid request"}), 400
    



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



@app.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('login'))