import datetime
from flask import render_template, request, redirect, url_for, flash, session
from ..models import db, User, Questions, Plus_ones, Answers, Votes, Keywords,Organizations
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
from ..utils.hybrid_rag import hybrid_search
from ..utils.simple_rag import search_answer
from flask import current_app
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

QA_bpt = Blueprint('question_and_answer', __name__)
executor = ThreadPoolExecutor(max_workers=5)

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)

@QA_bpt.route('/questions', methods=['GET', 'POST', 'DELETE', 'PUT'])
def questions():

    filter=request.args.get('filter','date')

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

        if filter=="date":
            print("date")
            questions = Questions.query.order_by(Questions.date.desc()).all()
        elif filter=="plus_one":
            print("plus_one")
            questions = Questions.query.order_by(Questions.plus_one.desc()).all()
        elif filter=="plus_one_date":
            questions = Questions.query.order_by(Questions.date.desc(), Questions.plus_one.asc()).all()
        else:
            questions = Questions.query.all()

        for question in questions:
            question_whole.append(question.serializer())
        
        if User.query.filter_by(userid=session.get('user_id')).first():
            role=User.query.filter_by(userid=session.get('user_id')).first().role
        elif Organizations.query.filter_by(orgid=session.get('org_id')).first():
            role='organization'
        else:
            role="user"
        return render_template('questions.html',questions=question_whole,nav="All Questions",role=role,filter=filter)
    
    
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


@QA_bpt.route('/questions_delete/<int:question_id>',methods=['GET'])
@role_required(['user','moderator','organization'])
def questions_delete(question_id):
    user=User.query.filter_by(userid=session['user_id']).first()
    question=Questions.query.filter_by(questionid=question_id).first()
    if question.userid!=user.userid and user.role!='moderator' and user.role!='organization':
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
    if user.role=='moderator' or user.role=='organization':
        return redirect(url_for('moderator.moderator_dashboard'))
    return redirect(url_for('user.myquestions'))


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

        app = current_app._get_current_object()
        executor.submit(ask_question_function, app, random_id, org_id, title, body, tag_objects)

        flash(['Your question is being posted in the background!', 'success'])
        return redirect(url_for('question_and_answer.questions'))

    return render_template('AskQuestion.html', nav="Ask Question", role=User.query.filter_by(userid=session['user_id']).first().role)


def ask_question_function(app, question_id, org_id, title, body, tags):
    try:
        with app.app_context():
            # Perform hybrid and simple RAG search
            hybrid_context = hybrid_search(f"{title} {body}", org_id, score_threshold=0.5)
            simple_context = search_answer(f"{title} {body}", org_id)

            # If no context is found, fetch additional information from Wikipedia
            wiki_context = ""
            if not hybrid_context and not simple_context:
                wiki_context = wiki_tool.run(title + " " + body)

            # Build prompt based on context availability
            base_prompt = f"Answer the Question: {title} {body} using existing context and knowledge.\n"

            if hybrid_context:
                base_prompt += f"Hybrid Search Context:\n{hybrid_context}\n"
            if simple_context:
                base_prompt += f"QA Pair Context:\n{simple_context}\n"
            if wiki_context:
                base_prompt += f"Wikipedia Context:\n{wiki_context}\n"

            if not (hybrid_context or simple_context or wiki_context):
                base_prompt += "No context found. Use general knowledge to answer."

            # Define the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful and accurate AI assistant."),
                ("user", "Answer the following question based on the context:\n{question}")
            ])

            # Initialize the LLM and output parser
            llm = Ollama(model="llama3.2")
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser

            # Invoke the chain with the correct input
            response = chain.invoke({"question": base_prompt})

            # Check toxicity of the response
            is_toxic, details = is_abusive(response)
            if is_toxic:
                print("AI response flagged as toxic:", details)
                return

            # Save the AI-generated response to the database
            extracted_keywords = [keyword[0] for keyword in keybertmodel.extract_keywords(response)] + tags
            new_answer = Answers(
                answer=response,
                questionid=question_id,
                userid=1,  # Replace with dynamic user ID if necessary
                upvotes=0,
                downvotes=0,
                marked_as_official=False,
                date=datetime.datetime.now(),
            )
            db.session.add(new_answer)

            # Update question status and keywords
            question = Questions.query.filter_by(questionid=question_id).first()
            if question:
                question.ai_answer = True

            for key in extracted_keywords:
                key_lower = lemmatize_text(key.lower())
                keyword_record = Keywords.query.filter_by(keyword=key_lower).first()
                if keyword_record:
                    keyword_record.count += 1
                else:
                    db.session.add(Keywords(keyword=key_lower, organization=org_id, count=1))

            db.session.commit()
            print("AI successfully answered and saved the response.")

            # Notification handling (ensure notifications is initialized)
            notifications = []
            notifications.append({
                "title": "AI Response",
                "body": "Your question has been answered by AI.",
                "redirect_url": '/questions'
            })

    except Exception as e:
        print("Error in ask_question_function:", str(e))