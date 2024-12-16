import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from sqlalchemy import distinct
from app import app
from functools import wraps
from models import db, User, Questions, Plus_ones, Answers,Votes,Organizations,Moderators,Labels,Invites,Keywords, Docs
import random
import ollama
import re
import humanize
from transformers import BertTokenizer, BertModel
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import torch
import io
import random
import os
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
from keybert import KeyBERT
import json
import datetime
from datetime import timedelta
import random
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from transformers import pipeline

ALLOWED_EXTENSIONS = {'pdf'}

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

model = KeyBERT('distilbert-base-nli-mean-tokens')

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')


def generate_demo_data():
    # Generate sample time-series data for the past 30 days
    dates = [(datetime.datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30)]
    
    return {
        'user_metrics': {
            'total_users': 1250,
            'active_users': 890,
            'new_users_today': 25
        },
        'content_metrics': {
            'total_questions': 3450,
            'total_answers': 12340,
            'ai_answers': 5670
        },
        'trending_tags': [
            {'name': 'Python', 'count': 450},
            {'name': 'JavaScript', 'count': 380},
            {'name': 'React', 'count': 320},
            {'name': 'Flutter', 'count': 290},
            {'name': 'Docker', 'count': 250}
        ],
        'time_series_data': {
            'dates': dates,
            'questions': [random.randint(10, 50) for _ in range(30)],
            'answers': [random.randint(30, 100) for _ in range(30)]
        },
        'top_questions': [
            {'title': 'How to implement LinkedList in Rust?', 'views': 1200, 'answers': 5},
            {'title': 'Best practices for React hooks', 'views': 980, 'answers': 8},
            {'title': 'Python async vs threading', 'views': 850, 'answers': 6},
            {'title': 'Docker container networking', 'views': 720, 'answers': 4},
            {'title': 'Flutter state management', 'views': 690, 'answers': 7}
        ],
        'moderation_stats': {
            'flagged_content': 23,
            'pending_reviews': 12,
            'resolved_today': 45
        }
    }



def get_bert_embedding(text):
    """
    Generate BERT embedding for the given text.
    """
    inputs = bert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = bert_model(**inputs)
    # Use the mean of the last hidden state as the embedding
    embedding = outputs.last_hidden_state.mean(dim=1).detach().numpy()
    return embedding


# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

def lemmatize_text(text):
    words = word_tokenize(text)
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
    return " ".join(lemmatized_words)

# Load a pre-trained text classification pipeline for toxicity detection
def load_toxicity_model():
    """
    Initializes and returns a pre-trained NLP pipeline for toxicity detection
    with hardware acceleration.
    """
    # Detect device (mps for Apple Silicon, cuda for NVIDIA, cpu fallback)
    device = 0 if torch.cuda.is_available() else -1  # cuda if available
    if not torch.cuda.is_available() and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"  # Use MPS if available

    return pipeline("text-classification", model="unitary/toxic-bert", tokenizer="unitary/toxic-bert", device=device)

def is_abusive(content, threshold=0.5, max_token_length=512):
    # Load the toxicity detection model
    toxicity_detector = load_toxicity_model()

    # Split content into chunks of max_token_length
    content_chunks = [content[i:i+max_token_length] for i in range(0, len(content), max_token_length)]

    abusive = False
    all_predictions = []

    for chunk in content_chunks:
        predictions = toxicity_detector(chunk)
        all_predictions.extend(predictions)

        # Check if the chunk is abusive
        if any(pred["label"].lower() == "toxic" and pred["score"] >= threshold for pred in predictions):
            abusive = True
            break  # Stop processing further if any chunk is abusive

    return abusive, all_predictions

def role_required(roles=None):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # Common variables
            user_id = session.get('user_id')
            org_id = session.get('org_id')

            # Ensure roles is iterable
            roles_to_check = roles if isinstance(roles, (list, tuple)) else [roles]

            # Role-specific checks
            if "organization" in roles_to_check and org_id:
                organization = Organizations.query.filter_by(orgid=org_id).first()
                if organization:
                    return func(*args, **kwargs)

            if "moderator" in roles_to_check and user_id:
                moderator = User.query.filter_by(userid=user_id).first()
                if moderator and moderator.role == "moderator":
                    return func(*args, **kwargs)

            if "user" in roles_to_check and user_id:
                user = User.query.filter_by(userid=user_id).first()
                if user:
                    return func(*args, **kwargs)

            # If no matching role, deny access
            flash("You do not have permission to access this page.")
            return redirect(url_for('login'))
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
    flash(['Welcome to AIQuest','success','Welcome'])
    return render_template('Landingpage.html',nav="Welcome")


# NOTE: Organization dashboard
@app.route('/dashboard/organization')
@role_required('organization')
def organization_dashboard():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]

    pdf_files = Docs.query.filter_by(orgid=session['org_id']).all()
    pdf_files_serialized = [doc.serializer() for doc in pdf_files]
    all_invites = []
    # top 5 user having role user and moderator
    top_5_user = Invites.query.filter(Invites.registered == True).order_by(Invites.date.desc()).limit(5).all()
    top_5_moderator = Invites.query.filter(Invites.registered == False).order_by(Invites.date.desc()).limit(5).all()
    for invite in top_5_user:
        all_invites.append(invite.serializer())
    for invite in top_5_moderator:
        all_invites.append(invite.serializer())

    total_users=User.query.filter_by(organization=session['org_id']).count()
    user = User.query.filter_by(organization=session['org_id']).all()
    total_answers=0
    total_questions=Questions.query.filter_by(orgid=session['org_id']).count()
    for user in user:
        total_answers = total_answers+Answers.query.filter_by(userid=user.userid).count()
    content={'total_users':total_users,'total_questions':total_questions,'total_answers':total_answers}

    return render_template(
                            'OrganizationDashboard.html',
                            data=generate_demo_data(),
                            questions=questions,
                            invites=all_invites,
                            nav="Organization Dashboard",
                            content=content,
                            pdf_files=pdf_files_serialized
                        )



# NOTE: 
@app.route('/dashboard/moderator')
@role_required('moderator')
def moderator_dashboard():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]

    return render_template('ModeratorDashboard.html', questions=questions,nav="Moderator Dashboard")

@app.route('/mark_as_official/<int:answerid>', methods=['get'])
@role_required('moderator')
def mark_as_official(answerid):
    answer = Answers.query.get(answerid)
    answer.marked_as_official = True
    Questions.query.filter_by(questionid=answer.questionid).first().official_answer = answer.answer

    db.session.commit()
    flash(['Answer marked as official','success'])
    return redirect(url_for('questions_details', question_id=answer.questionid))

@app.route('/unmark_as_official/<int:answerid>', methods=['get'])
@role_required('moderator')
def unmark_as_official(answerid):
    answer = Answers.query.get(answerid)
    answer.marked_as_official = False
    if len(Answers.query.filter_by(questionid=answer.questionid,marked_as_official=True).all())>=1:
        Questions.query.filter_by(questionid=answer.questionid).first().official_answer = Answers.query.filter_by(questionid=answer.questionid,marked_as_official=True).first().answer
    else:
        Questions.query.filter_by(questionid=answer.questionid).first().official_answer = ""

    db.session.commit()
    flash(['Answer unmarked as official','success'])
    return redirect(url_for('questions_details', question_id=answer.questionid))

@app.route('/dashboard/user')
@role_required("user")
def user_dashboard():

    questions=Questions.query.filter_by(userid=session['user_id']).order_by(Questions.date.desc()).limit(5).all()
    questions=[question.serializer() for question in questions]
    

    # questions = [
    #     {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
    #     {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
    #     {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    # ]
    
    return render_template('user_dashboard.html', questions=questions,nav="User Dashboard")


@app.route('/invite_user',methods=["POST"])
@role_required('organization')
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
        return render_template('emailinvite.html',email=email,code=code,role=role,register_url=register_url,browser_url=None)
    # email user
    else:
        register_url=url_for('register', code="1234 5678 9012 3456",email="demo@gmail.com", _external=True)
        browser_url = url_for('invitedmail', code="1234 5678 9012 3456",email="demo@gmail.com",role="admin", _external=True)
        return render_template('emailinvite.html',email="demo@gmail.com",code="1234 5678 9012 3456",role="admin",register_url=register_url,browser_url=browser_url)


@app.route('/UserManager')
@role_required('organization')
def userManager():
    invites = Invites.query.all()
    print(datetime.datetime.now())
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(characters) for _ in range(16))
    print(code)
    all_invites = []
    for invite in invites:
        all_invites.append(invite.serializer())
    return render_template('OrgUserManager.html',invites=all_invites,nav="User Manager")


@app.route('/UserManager', methods=['POST'])
@role_required('organization')
def UserManager():
    try:
        # Get JSON data
        data = request.get_json()
        print(data)
        print(type(data.get('registered')))
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
            print('True')
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
            print('False')
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
@role_required('organization')
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
    if session.get('user_id'):
        if User.query.filter_by(userid=session.get('user_id')).first().role == 'moderator':
            return redirect(url_for('moderator_dashboard'))
        return redirect(url_for('user_dashboard'))
    if session.get('org_id'):
        return redirect(url_for('organization_dashboard'))
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if role == 'user':
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.passhash, password):
                session['user_id'] = user.userid
                if user.role == 'moderator':
                    flash(['Moderator login successful!', 'success'])
                    return redirect(url_for('moderator_dashboard'))
                elif user.role == 'user':
                    flash(['User login successful!', 'success'])
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
                flash(['Organization login successful!','success'])
                return redirect(url_for('organization_dashboard'))
            flash('Invalid organization credentials. Please try again.')

    return render_template('login.html',nav="Login")


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
        role=Invites.query.filter_by(code=invitecode).first().role

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
                  email=email,passhash=generate_password_hash(password),organization=orgid,role=role)
        invite.registered = True
        db.session.add(user)
        db.session.commit()
        flash(['You have successfully registered','success'])
        
        return redirect(url_for('login'))

    return render_template('register.html',code=code,email=email,nav="User Register")


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

    return render_template('organizationRegister.html',nav="Organization Register")


@app.route('/image/<int:id>')
def get_image(id):
    image = Organizations.query.get(id)
    return send_file(io.BytesIO(image.orglogo), mimetype='image/jpeg')


# @app.route('/questiondetail',methods=['GET'])
# def ques():
#     return render_template('QuestionDetails.html') 

@app.route('/questions', methods=['GET', 'POST', 'DELETE', 'PUT'])
def questions():

    if request.method=='POST': # Add the question
        question=request.form.get('question')
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
    

    # elif request.method=='PUT': # Plus one the question
    #     # Plus one
    #     question_id=request.form.get('question_id')
    #     # If already plus one remove plus one
    #     if plus_ones.query.get(question_id = int(question_id), userid = int(session['user_id'])):
    #         plus_ones.query.filter_by(question_id = int(question_id), userid = int(session['user_id'])).delete()
    #         questions.query.filter_by(questionid=question_id).first().plus_one-=1
    #         db.session.commit()
            
    

    else: # Get all questions
        question_whole=[]
        questions = Questions.query.order_by(Questions.date.desc()).all()
        for question in questions:
            question_whole.append(question.serializer())
        return render_template('questions.html',questions=question_whole,nav="All Questions")
    
@app.route('/answer_delete/<int:answerid>', methods=['GET'])
@role_required(['admin', 'moderator'])
def answer_delete(answerid):
    answer = Answers.query.get(answerid)
    official_ans=answer.answer
    question_id = answer.questionid
    db.session.delete(answer)
    db.session.commit()

    if Questions.query.filter_by(questionid=question_id).first().official_answer == official_ans:
        if len(Answers.query.filter_by(questionid=question_id,marked_as_official=True).all())>=1:
            Questions.query.filter_by(questionid=question_id).first().official_answer = Answers.query.filter_by(questionid=question_id,marked_as_official=True).order_by(Answers.date.desc()).first().answer
        else:
            Questions.query.filter_by(questionid=question_id).first().official_answer = ""

    db.session.commit()

    flash(['Answer deleted successfully','success'])
    return redirect(url_for('questions_details', question_id=question_id))


@app.route('/questions_details/<int:question_id>', methods=['GET', 'POST'])
@role_required(['user', 'moderator'])
def questions_details(question_id):

    if request.method=='POST':
        answer=request.form.get('answer')
        if User.query.get(session['user_id']).role=='moderator':
            isAnsOfficial = True if request.form.get('official_status') == "yes" else False
        else:
            isAnsOfficial = False
        
        if answer is None:
            flash('Please fill the required fields')
            return redirect(url_for('questions'))
        
        newAnswer=Answers(answer=answer, questionid=question_id, userid=session['user_id'],
                       upvotes=0, downvotes=0, marked_as_official=isAnsOfficial, date=datetime.datetime.now())
        db.session.add(newAnswer)
        db.session.commit()

        if isAnsOfficial:
            question = Questions.query.filter_by(questionid=question_id).first()
            question.official_answer = answer
            db.session.commit()


            # Generate BERT embedding for the question text
            # inputs = tokenizer(question_text, return_tensors='pt', truncation=True, padding=True)
            # with torch.no_grad():
            #     outputs = model(**inputs)
            #     embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

            # # Create the official answer entry
            # official_entry = OfficialAnswer(
            #     questionid=question_id,
            #     embedding=str(embedding),
            #     question_text=question_text,
            #     answer_text=answer
            # )
            # db.session.add(official_entry)
            # db.session.commit()


        flash(['Answer added successfully','success','Answer Provided'])
        return redirect(url_for('questions_details', question_id=question_id))
            

    else: # Get all questions
        questions=Questions.query.filter_by(questionid=question_id).first()
        
        timestamp = questions.date

        # Get the current time
        now = datetime.datetime.now()

        # Calculate the relative time
        relative_time = humanize.naturaltime(now - timestamp)
        user_question=User.query.filter_by(userid=questions.userid).first()

        answer_all = Answers.query.filter_by(questionid=question_id).order_by(Answers.date.desc()).all()

        answers_list=[]
        for answer in answer_all:
            answers_list.append(answer.serializer())

        return render_template('QuestionDetails.html',question=questions.serializer(),relative_time=relative_time,user_question=user_question,answers=answers_list,nav="Question {}".format(question_id),role=User.query.filter_by(userid=session['user_id']).first().role)


def ask_question_function(question_id, org_id, title, body, tags):
    print("thread running")
    with app.app_context():
        prompt = "Answer the given question: " + title + body + "from tag" + " ".join(tags)
        response = ollama.generate(model='llama3.2', prompt=prompt)

        is_toxic, details = is_abusive(response["response"])
        if not is_toxic:
            answer = response["response"]

            # extracted_keywords = [keyword[0] for keyword in model.extract_keywords(answer)] + tags

            new_answer = Answers(
                answer=answer,
                questionid = question_id,
                userid=2,
                upvotes=0,
                downvotes=0,
                marked_as_official=False,
                date=datetime.datetime.now()
            )

            question = Questions.query.filter_by(questionid=question_id).first()
            question.ai_answer = True


            # for key in extracted_keywords:
            #     if_keyword_exist = Keywords.query.filter_by(keyword=key.lower()).first()
            #     if if_keyword_exist:
            #         if_keyword_exist.count += 1
            #     else:
            #         new_keyword = Keywords(
            #             keyword=lemmatize_text(key.lower()),
            #             organization=org_id,
            #             count=1,
            #         )
            #         db.session.add(new_keyword)
            db.session.add(new_answer)
            db.session.commit()
        print("thread ending")


@app.route('/ask_question', methods=["GET", "POST"])
@role_required('user')
def ask_question():

    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('body')
        tags = request.form.get('tags')
        random_id = random.randint(1000, 9999)

        is_toxic, details = is_abusive(title + ' ' + body + ' ' + tags)

        if is_toxic:
            flash('The question content is toxic/abusive cannot be posted. We apologize for the inconvenience.', 'error')
            return redirect(url_for('ask_question'))

         # Basic validation to check if all fields are filled
        if not title or not body or not tags:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('ask_question'))
        
        org_id = User.query.filter_by(userid=session.get('user_id')).first().organization

        # Optional: Process and store tags (you may choose to split them by commas or space)
        tag_objects = [tag.strip() for tag in tags.split(',')]

        new_question = Questions(
            questionid = random_id,
            question_title=title,
            question_detail=body,
            date=datetime.datetime.now(),
            official_answer="",
            userid=session.get('user_id'),
            tags =tag_objects,
            orgid=org_id
        )

        db.session.add(new_question)
        db.session.commit()

        # Create a new thread to run ask_question_function asynchronously
        thread = threading.Thread(target=ask_question_function, args=(random_id, org_id, title, body, tag_objects))
        print('thread startng')
        thread.start()

        flash(['Your question is being posted in the background!', 'success'])
        return redirect(url_for('questions'))  # Redirect to the same page or another page
    
    return render_template('AskQuestion.html',nav="Ask Question")



@app.route('/myquestions',methods=['GET'])
@role_required('user')
def myquestions():
    questions=Questions.query.filter_by(userid=session['user_id']).order_by(Questions.date.desc()).all()
    questions=[question.serializer() for question in questions]
    return render_template('my_questions.html',questions=questions,nav="My Questions")

@app.route('/questions_delete/<int:question_id>',methods=['GET'])
@role_required('user')
def questions_delete(question_id):
    user=User.query.filter_by(userid=session['user_id']).first()
    question=Questions.query.filter_by(questionid=question_id).first()
    if question.userid!=user.userid:
        flash('You are not authorized to delete this question')
        return redirect(url_for('myquestions'))
    answers=Answers.query.filter_by(questionid=question_id).all()
    plus_ones=Plus_ones.query.filter_by(questionid=question_id).all()
    votes=Votes.query.filter_by(questionid=question_id).all()
    for answer in answers:
        db.session.delete(answer)
    for plus_one in plus_ones:
        db.session.delete(plus_one)
    for vote in votes:
        db.session.delete(vote)
    db.session.delete(question)
    db.session.commit()
    flash(['Question deleted successfully','success'])
    return redirect(url_for('myquestions'))



@app.route('/<int:question_id>/plusone', methods=["POST"])
@role_required('user')
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
    



# @app.route('/answers/<int:question_id>', methods=['GET', 'POST', 'DELETE', 'PUT'])
# @role_required('user')
# def answers_route(question_id):
    
#         if request.method=='POST':
#             answer=request.form.get('answer')
#             official_answer=request.form.get('official_status')
#             if question_id is None or answer is None:
#                 flash('Please fill the required fields')
#                 return redirect(url_for('questions'))
#             is_toxic, details = is_abusive(answer)
#             if is_toxic:
#                 flash('The answer content is toxic/abusive cannot be posted. We apologize for the inconvenience.', 'error')
#                 return redirect(url_for('questions'))
#             if official_answer == 'no':
#                 answer=Answers(answer=answer,questionid=question_id, userid=session['user_id'],
#                             upvotes=0, downvotes=0, date=datetime.datetime.now())
#                 db.session.add(answer)
#                 db.session.commit()
#                 flash(['Answer added successfully','success'])
#                 return redirect(url_for('questions'))
#             else:
#                 question = Questions.query.filter_by(questionid=question_id).first()
#                 question.official_answer = answer
#                 db.session.commit()
#                 flash(['Official answer added successfully','success'])
#                 return redirect(url_for('questions'))
        
#         # elif request.method=='DELETE': # Delete the answer
#         #     answer_id=request.form.get('answer_id')
#         #     if answer_id is None:
#         #         flash('Please fill the required fields')
#         #         return redirect(url_for('questions'))
#         #     answer=answers.query.filter_by(answerid=answer_id).first()
#         #     db.session.delete(answer)
#         #     db.session.commit()
#         #     flash(['Answer deleted successfully','success'])
#         #     return redirect(url_for('questions'))
        
#         elif request.method=='PUT': # Vote the answer
#             answer_id=request.form.get('answer_id')
#             vote = request.form.get('vote') # +1 for upvote and -1 for downvote, +10 for official answer
#             answer=Answers.query.filter_by(answerid=answer_id).first()

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


@app.route('/upvote/<int:question_id>', methods=['POST'])
@role_required('user')
def upvote_question(question_id):

    if not session.get('user_id'):
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    # Fetch the question from the database
    # Plus_ones.query.filter_by(questionid=question_id, userid=session.get('user_id')).first()

    plus_one = Plus_ones.query.filter_by(questionid=question_id, userid=session.get('user_id')).first()
    print(plus_one)
    if plus_one:
        db.session.delete(plus_one)
        Questions.query.filter_by(questionid=question_id).first().plus_one -= 1
        db.session.commit()
        new_count = Plus_ones.query.filter_by(questionid=question_id).count()
        return jsonify({"success": True, "new_count": new_count, "status": False})
    plus_one = Plus_ones(questionid=question_id, userid=session.get('user_id'), date=datetime.datetime.now())
    Questions.query.filter_by(questionid=question_id).first().plus_one += 1
    db.session.add(plus_one)
    db.session.commit()
    new_count = Plus_ones.query.filter_by(questionid=question_id).count()

    return jsonify({"success": True, "new_count": new_count, "status": True})

@app.route('/upvoteans/<int:answer_id>', methods=['POST'])
@role_required('user')
def upvote_answer(answer_id):
    
    if not session.get('user_id'):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    vote = Votes.query.filter_by(answerid=answer_id, userid=session.get('user_id')).first()
    if vote:
        if vote.vote == "1":
            print('upvote')
            return jsonify({"success": False, "message": "You have already voted"}), 403
        else:

            vote.vote = 1
            Answers.query.filter_by(answerid=answer_id).first().upvotes += 1
            Answers.query.filter_by(answerid=answer_id).first().downvotes -= 1
            db.session.commit()
            upvote=Answers.query.filter_by(answerid=answer_id).first().upvotes
            downvote=Answers.query.filter_by(answerid=answer_id).first().downvotes
            return jsonify({"success": True, "upvote": upvote, "downvote": downvote})
    else :
        print("belwo else")
        question_id=Answers.query.filter_by(answerid=answer_id).first().questionid
        vote = Votes(answerid=answer_id, userid=session.get('user_id'), date=datetime.datetime.now(),questionid=question_id, vote=1)
        Answers.query.filter_by(answerid=answer_id).first().upvotes += 1
        db.session.add(vote)
        db.session.commit()
        upvote=Answers.query.filter_by(answerid=answer_id).first().upvotes
        downvote=Answers.query.filter_by(answerid=answer_id).first().downvotes

        return jsonify({"success": True, "upvote": upvote, "downvote": downvote})



@app.route('/downvoteans/<int:answer_id>',methods=['POST'])
@role_required('user')
def downvoteans(answer_id):
    if not session.get('user_id'):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    
    vote = Votes.query.filter_by(answerid=answer_id, userid=session.get('user_id')).first()
    if vote:
        if vote.vote == "-1":
            return jsonify({"success": False, "message": "You have already voted"}), 403
        else:
            vote.vote = -1
            Answers.query.filter_by(answerid=answer_id).first().upvotes -= 1
            Answers.query.filter_by(answerid=answer_id).first().downvotes += 1
            db.session.commit()
            upvote=Answers.query.filter_by(answerid=answer_id).first().upvotes
            downvote=Answers.query.filter_by(answerid=answer_id).first().downvotes
            return jsonify({"success": True, "upvote": upvote, "downvote": downvote})
    else :
        question_id=Answers.query.filter_by(answerid=answer_id).first().questionid
        vote = Votes(answerid=answer_id, userid=session.get('user_id'), date=datetime.datetime.now(),questionid=question_id, vote=-1)
        Answers.query.filter_by(answerid=answer_id).first().downvotes += 1
        db.session.add(vote)
        db.session.commit()
        upvote=Answers.query.filter_by(answerid=answer_id).first().upvotes
        downvote=Answers.query.filter_by(answerid=answer_id).first().downvotes

        return jsonify({"success": True, "upvote": upvote, "downvote": downvote})
    
    # question_id=Answers.query.filter_by(answerid=answer_id).first().questionid
    # vote = Votes(answerid=answer_id, userid=session.get('user_id'), date=datetime.datetime.now(),questionid=question_id, vote=-1)
    # Answers.query.filter_by(answerid=answer_id).first().downvotes += 1
    # db.session.add(vote)
    # db.session.commit()
    # new_count = Votes.query.filter_by(answerid=answer_id).count()

    # print('downvote')
    # return jsonify({"message": "Vote updated successfully", "new_count": "50"})


@app.route('/upload', methods=['POST'])
def upload_file():
    docdesc = request.form.get('docdesc') if request.form.get('docdesc') else ''
    orgid = session.get('org_id')

    # Check if a file is included
    if 'file' not in request.files:
        flash('No file part in the form')
        return redirect(request.url)

    file = request.files['file']
    # Name of the file uploaded
    docname = file.filename

    # If no file is selected
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)

    # Validate and process the file
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file to the local storage
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(file_path)
        except Exception as e:
            flash(f"Failed to save the file: {e}")
            return redirect(request.url)

        # Save file details to the database
        new_doc = Docs(
            docname=docname,
            docdesc=docdesc,
            docpath=file_path,
            orgid=orgid
        )
        try:
            db.session.add(new_doc)
            db.session.commit()
            flash('File successfully uploaded and details saved!')
            return redirect(url_for('login'))  # Replace with the desired redirect
        except Exception as e:
            flash(f"Failed to save file details to database: {e}")
            db.session.rollback()
            return redirect(request.url)
    else:
        flash('Invalid file format. Only PDF files are allowed.')
        return redirect(request.url)


@app.route('/admin/dashboard')
def admin_dashboard():
    data = generate_demo_data()
    return render_template('admin_dashboard.html', data=data)

@app.route('/logout')
def logout():
    session.pop('user_id',None)
    session.pop('org_id',None)
    return redirect(url_for('login'))