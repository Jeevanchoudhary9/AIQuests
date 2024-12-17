from ..models import db, Questions, Answers
from ..utils.role_check import role_required
from flask import render_template, flash, redirect, url_for
from flask import Blueprint

moderator_bpt = Blueprint('moderator', __name__)

@moderator_bpt.route('/dashboard/moderator')
@role_required('moderator')
def moderator_dashboard():
    questions = [
        {'id': 1, 'title': 'How to implement authentication in React?', 'short_description': 'I need to implement authentication...', 'time_ago': '2 hours', 'answer_count': 5, 'asker_name': 'John Doe'},
        {'id': 2, 'title': 'Best practices for React state management?', 'short_description': 'Looking for suggestions on managing state...', 'time_ago': '1 day', 'answer_count': 3, 'asker_name': 'Jane Smith'},
        {'id': 3, 'title': 'How to optimize React performance?', 'short_description': 'Performance optimization tips...', 'time_ago': '3 days', 'answer_count': 8, 'asker_name': 'Mark Lee'}
    ]

    return render_template('ModeratorDashboard.html', questions=questions,nav="Moderator Dashboard")


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