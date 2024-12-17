from ..models import db, Questions, Answers, User
from ..utils.role_check import role_required
from flask import session
from flask import render_template, flash, redirect, url_for
from flask import Blueprint
from sqlalchemy import desc,asc
import humanize

moderator_bpt = Blueprint('moderator', __name__)

@moderator_bpt.route('/dashboard/moderator')
@role_required('moderator')
def moderator_dashboard():
    questions=Questions.query.filter_by(orgid=User.query.filter_by(userid = session.get('user_id')).first().organization).order_by(asc(Questions.date)).all()
    answers=[]
    for question in questions:
        answers.append(Answers.query.filter_by(questionid=question.questionid).all())
    questions_marked_official = [question for question in questions if question.official_answer != ""]
    question_notmarked_official = [question.serializer() for question in questions if question.official_answer == ""]
    # print(question_notmarked_official)

    data_summary={}
    data_summary['users']=len(User.query.filter_by(userid = session.get('user_id')).all())
    data_summary['questions']=len(questions)
    data_summary['answers']=len(answers)

    # questions = [
    #     {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
    #     {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
    #     {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    # ]

    return render_template('ModeratorDashboard.html', questions=questions,data_summary=data_summary,official=questions_marked_official,unofficial=question_notmarked_official,nav="Moderator Dashboard")

@moderator_bpt.route('/question_moderation')
@role_required('moderator')
def question_moderation():
    questions=Questions.query.filter_by(orgid=User.query.filter_by(userid = session.get('user_id')).first().organization).order_by(asc(Questions.date)).all()
    new_questions=[]
    for question in questions:
        new_questions.append(question.serializer())
    return render_template('moderate_questions.html',questions=new_questions,nav="Moderate Questions")

@moderator_bpt.route('/mark_as_official/<int:answerid>', methods=['get'])
@role_required('moderator')
def mark_as_official(answerid):
    answer = Answers.query.get(answerid)
    answer.marked_as_official = True
    Questions.query.filter_by(questionid=answer.questionid).first().official_answer = answer.answer

    db.session.commit()
    flash(['Answer marked as official','success'])
    return redirect(url_for('question_and_answer.questions_details', question_id=answer.questionid))


@moderator_bpt.route('/unmark_as_official/<int:answerid>', methods=['get'])
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
    return redirect(url_for('question_and_answer.questions_details', question_id=answer.questionid))