import datetime
from flask import render_template, request, redirect, url_for, flash, session
from ..models import db, User, Questions, Plus_ones, Answers, Votes, Keywords
import random
from langchain_community.llms.ollama import Ollama
import humanize
import random
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import threading
import random
from ..utils.role_check import role_required
from ..utils.ai_part import lemmatize_text, is_abusive, keybertmodel
from ..utils.email_notification import notifications
from flask import Blueprint
from concurrent.futures import ThreadPoolExecutor
from flask import current_app

QA_bpt = Blueprint('question_and_answer', __name__)
executor = ThreadPoolExecutor(max_workers=5)

@QA_bpt.route('/questions', methods=['GET', 'POST', 'DELETE', 'PUT'])
def questions():

    if request.method=='POST': # Add the question
        question=request.form.get('question')
        question=questions(question=question,userid=session['user_id'].first(), plus_one=0, official_answer="")
        db.session.add(question)
        db.session.commit()
        flash(['Question added successfully','success'])
        return redirect(url_for('question_and_answer.questions'))
    

    elif request.method=='DELETE': # Delete the question
        question_id=request.form.get('question_id')
        if question_id is None:
            flash('Please fill the required fields')
            return redirect(url_for('question_and_answer.questions'))
        question=questions.query.filter_by(questionid=question_id).first()
        db.session.delete(question)
        db.session.commit()
        flash(['Question deleted successfully','success'])
        return redirect(url_for('question_and_answer.questions'))
    

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
    
    
@QA_bpt.route('/answer_delete/<int:answerid>', methods=['GET'])
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
    return redirect(url_for('question_and_answer.questions_details', question_id=question_id))


@QA_bpt.route('/questions_details/<int:question_id>', methods=['GET', 'POST'])
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
            return redirect(url_for('question_and_answer.questions'))
        
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
        return redirect(url_for('question_and_answer.questions_details', question_id=question_id))
            

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


@QA_bpt.route('/ask_question', methods=["GET", "POST"])
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
            return redirect(url_for('question_and_answer.ask_question'))

        # Basic validation
        if not title or not body or not tags:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('question_and_answer.ask_question'))
        
        # Get organization ID
        org_id = User.query.filter_by(userid=session.get('user_id')).first().organization

        # Process tags
        tag_objects = [tag.strip() for tag in tags.split(',')]

        # Save the question in the database
        new_question = Questions(
            questionid=random_id,
            question_title=title,
            question_detail=body,
            date=datetime.datetime.now(),
            official_answer="",
            userid=session.get('user_id'),
            tags=tag_objects,
            orgid=org_id
        )

        db.session.add(new_question)
        db.session.commit()

        # Submit the task to the executor with the app context
        with current_app.app_context():
            executor.submit(ask_question_function, random_id, org_id, title, body, tag_objects)

        flash('Your question is being posted in the background!', 'success')
        return redirect(url_for('question_and_answer.questions'))

    return render_template('AskQuestion.html', nav="Ask Question")


@QA_bpt.route('/questions_delete/<int:question_id>',methods=['GET'])
@role_required('user')
def questions_delete(question_id):
    user=User.query.filter_by(userid=session['user_id']).first()
    question=Questions.query.filter_by(questionid=question_id).first()
    if question.userid!=user.userid:
        flash('You are not authorized to delete this question')
        return redirect(url_for('user.myquestions'))
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
    return redirect(url_for('user.myquestions'))


def ask_question_function(question_id, org_id, title, body, tags):
    print("Thread started")
    try:
        # Explicitly set the app context within the thread
        with current_app.app_context():  # Ensure app context is available in background thread
            # Generate AI response
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "You are a helpful assistant. Please respond to user queries."),
                    ("user", f"Answer the Question: {title} {body} from tag {' '.join(tags)}")
                ]
            )
            llm = Ollama(model="llama3.2")
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser

            # AI response
            response = chain.invoke({"title": title, "body": body, "tags": ' '.join(tags)})

            # Check if AI response is toxic
            is_toxic, details = is_abusive(response)
            if not is_toxic:
                answer = response

                # Extract keywords
                extracted_keywords = [keyword[0] for keyword in keybertmodel.extract_keywords(answer)] + tags

                # Save the answer to the database
                new_answer = Answers(
                    answer=answer,
                    questionid=question_id,
                    userid=2,  # Adjust as needed
                    upvotes=0,
                    downvotes=0,
                    marked_as_official=False,
                    date=datetime.datetime.now(),
                )

                # Mark question as AI-answered
                question = Questions.query.filter_by(questionid=question_id).first()
                if question:
                    question.ai_answer = True

                # Update or add keywords
                for key in extracted_keywords:
                    key_lower = lemmatize_text(key.lower())
                    keyword_record = Keywords.query.filter_by(keyword=key_lower).first()
                    if keyword_record:
                        keyword_record.count += 1
                    else:
                        new_keyword = Keywords(
                            keyword=key_lower,
                            organization=org_id,
                            count=1,
                        )
                        db.session.add(new_keyword)

                # Commit changes
                db.session.add(new_answer)
                db.session.commit()

                print("AI answered the question successfully.")
            else:
                print("AI response is toxic:", details)

    except Exception as e:
        print("Error in ask_question_function:", str(e))
    finally:
        print("Thread ended")
        notification = {
            "title": "AI Response",
            "body": "Your question has been answered by AI.",
            "redirect_url": '/questions'
        }
        notifications.append(notification)