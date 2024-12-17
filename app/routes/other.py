import datetime
from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify
from ..models import db, Plus_ones, Organizations,Docs
from werkzeug.utils import secure_filename
import io
import os
from flask import jsonify
import datetime
from ..utils.role_check import role_required
from ..utils.ai_part import allowed_file
from ..utils.other import generate_demo_data
from ..utils.email_notification import notifications
from flask import Blueprint

other_bpt = Blueprint('other', __name__)

@other_bpt.route('/image/<int:id>')
def get_image(id):
    image = Organizations.query.get(id)
    return send_file(io.BytesIO(image.orglogo), mimetype='image/jpeg')


# @app.route('/questiondetail',methods=['GET'])
# def ques():
#     return render_template('QuestionDetails.html') 


@other_bpt.route('/<int:question_id>/plusone', methods=["POST"])
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



@other_bpt.route('/upload', methods=['POST'])
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
        file_path = os.path.join(other_bpt.config['UPLOAD_FOLDER'], filename)
        
        # Save the file to the local storage
        try:
            os.makedirs(other_bpt.config['UPLOAD_FOLDER'], exist_ok=True)
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
            return redirect(url_for('user.login'))  # Replace with the desired redirect
        except Exception as e:
            flash(f"Failed to save file details to database: {e}")
            db.session.rollback()
            return redirect(request.url)
    else:
        flash('Invalid file format. Only PDF files are allowed.')
        return redirect(request.url)


@other_bpt.route('/dashboard/admin')
def admin_dashboard():
    data = generate_demo_data()
    return render_template('admin_dashboard.html', data=data)


@other_bpt.route('/logout')
def logout():
    session.pop('user_id',None)
    session.pop('org_id',None)
    return redirect(url_for('user.login'))

@other_bpt.route("/trigger/<string:redirect_url>/<string:message_title>/<string:message_body>")
def trigger_notification(redirect_url, message_title, message_body):
    # Flash the message with the provided title and body
    flash(['Background process completed!', 'success', message_title, message_body])
    try:
        # Redirect to the specified route
        return redirect(url_for(redirect_url))
    except Exception as e:
        # Handle invalid redirect URL gracefully
        return f"Error: {e}", 400

# @app.route('/check_notification/<int:question_id>', methods=['GET'])
# def check_notification(question_id):
#     print("Checking notification for question ID:", question_id)
#     if question_id in notification_data:
#         # Return the notification data and remove it after sending
#         return jsonify(notification_data.pop(question_id))
#     return jsonify({"status": "pending"})

@other_bpt.route('/check_notifications')
def check_notifications():
    if notifications:
        # Pop the first notification from the list
        notification = notifications.pop(0)
        return jsonify({"notifications": [notification]})
    else:
        # If there are no notifications, return an empty list
        return jsonify({"notifications": []})