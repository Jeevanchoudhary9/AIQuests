from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import humanize
import datetime


db=SQLAlchemy(app)


class User(db.Model):
    __TableName__ = 'user'
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20))
    email = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(1024), nullable=False)
    organization = db.Column(db.Integer, db.ForeignKey('organizations.orgid'), nullable=True)
     
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)



class Questions(db.Model):
    __tablename__ = 'Questions'
    questionid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    question_title = db.Column(db.String(50), nullable=False)
    question_detail = db.Column(db.String(200), nullable=False)
    plus_one = db.Column(db.Integer, nullable=False,default=0)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    official_answer = db.Column(db.Integer, db.ForeignKey('answers.answerid'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    ai_answer = db.Column(db.Boolean, nullable=False,default=False)
    tags = db.Column(db.JSON, nullable=False)
    
    def serializer(self):
        return {
            'questionid': self.questionid,
            'question_title': self.question_title,
            'question_detail': self.question_detail,
            'plus_one': self.plus_one,
            'userid': self.userid,
            'email':User.query.filter_by(userid=self.userid).first().username,
            'official_answer': self.official_answer,
            'date': self.date,
            'ai_answer': self.ai_answer,
            'tags': self.tags,
            'no_of_ans': answers.query.filter_by(questionid=self.questionid).count(),
            'relative_time' : humanize.naturaltime(datetime.datetime.now() - self.date)
        }


class plus_ones(db.Model):
    __tablename__ = 'plus_ones'
    plusoneid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    questionid = db.Column(db.Integer, db.ForeignKey('Questions.questionid'), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)


class answers(db.Model):
    __tablename__ = 'answers'
    answerid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    answer = db.Column(db.String(200), nullable=False)
    upvotes = db.Column(db.Integer, nullable=False)
    downvotes = db.Column(db.Integer, nullable=False)
    questionid = db.Column(db.Integer, db.ForeignKey('Questions.questionid'), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    marked_as_official = db.Column(db.Boolean, nullable=False, default=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Answer {self.answerid}>'
    
    def __str__(self):
        return f'{self.answer}'
    
    def serializer(self):
        return {
            'answerid': self.answerid,
            'answer': self.answer,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'questionid': self.questionid,
            'userid': self.userid,
            'marked_as_official': self.marked_as_official,
            'date': self.date,
            'username': User.query.filter_by(userid=self.userid).first(),
            'relative_time' : humanize.naturaltime(datetime.datetime.now() - self.date)
        }
    

class votes(db.Model):
    __tablename__ = 'votes'
    voteid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    vote = db.Column(db.String(10), nullable=False)
    questionid = db.Column(db.Integer, db.ForeignKey('Questions.questionid'), nullable=False)
    answerid = db.Column(db.Integer, db.ForeignKey('answers.answerid'), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Vote {self.voteid}>'
    
    def __str__(self):
        return f'{self.vote}'
    
    def serializer(self):
        return {
            'voteid': self.voteid,
            'vote': self.vote,
            'questionid': self.questionid,
            'answerid': self.answerid,
            'userid': self.userid
        }
    

# class OfficialAnswer(db.Model):
#     __tablename__ = 'officialanswer'
#     officialanswerid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
#     questionid = db.Column(db.Integer, db.ForeignKey('Questions.questionid'))
#     question_text = db.Column(db.Text, nullable=False)
#     answer_text = db.Column(db.Text, nullable=False)
#     embedding = db.Column(db.Text, nullable=False)

#     def __repr__(self):
#         return f'<Official Answer {self.officialanswerid}>'

#     def __str__(self):
#         return f'{self.answer_text}'
    
#     def serializer(self):
#         return {
#             'officialanswerid': self.officialanswerid,
#             'questionid': self.questionid,
#             'question_text': self.question_text,
#             'answer_text': self.answer_text,
#             'embedding': self.embedding
#         }


class Organizations(db.Model):
    __tablename__ = 'organizations'
    orgid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    orgname = db.Column(db.String(50), nullable=False)
    orgdesc = db.Column(db.String(200), nullable=True)
    orglogo = db.Column(db.String(200), nullable=True)
    orgemail = db.Column(db.String(50), nullable=False)
    orgPassword = db.Column(db.String(1024), nullable=False)
    orgphone = db.Column(db.String(20), nullable=True)
    orgaddress = db.Column(db.String(200), nullable=True)
    orgwebsite = db.Column(db.String(200), nullable=False)
    orgtype = db.Column(db.String(20), nullable=True)
    orgTotalMembers = db.Column(db.Integer, nullable=True)
    orgadmin = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return f'<Organization {self.orgid}>'

    def __str__(self):
        return f'{self.orgname}'
    
    def serializer(self):
        return {
            'orgid': self.orgid,
            'orgname': self.orgname,
            'orgdesc': self.orgdesc,
            'orglogo': self.orglogo,
            'orgemail': self.orgemail,
            'orgphone': self.orgphone,
            'orgaddress': self.orgaddress,
            'orgwebsite': self.orgwebsite,
            'orgtype': self.orgtype,
            'orgTotalMembers': self.orgTotalMembers,
            'orgadmin': self.orgadmin,
            'orgdate': self.orgdate
        }


class Moderator(db.Model):
    __tablename__ = 'moderator'
    modid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    subject = db.Column(db.Integer, db.ForeignKey('labels.labelid'), nullable=False)
    orgid = db.Column(db.Integer, db.ForeignKey('organizations.orgid'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    officelocation = db.Column(db.String(200), nullable=False)


    def __repr__(self):
        return f'<Moderator {self.modid}>'

    def __str__(self):
        return f'{self.userid}'
    
    def serializer(self):
        return {
            'modid': self.modid,
            'userid': self.userid,
            'orgid': self.orgid,
            'date': self.date
        }


class Labels(db.Model):
    __tablename__ = 'labels'
    labelid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    labelname = db.Column(db.String(50), nullable=False)
    orgid = db.Column(db.Integer, db.ForeignKey('organizations.orgid'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Label {self.labelid}>'

    def __str__(self):
        return f'{self.labelname}'
    
    def serializer(self):
        return {
            'labelid': self.labelid,
            'labelname': self.labelname,
            'labeldesc': self.labeldesc,
            'labeltags': self.labeltags,
            'orgid': self.orgid,
            'date': self.date
        }

        
with app.app_context():
    db.create_all()

    admin=User.query.filter_by(username='admin').first()
    if not admin:
        organization=Organizations(
            orgname = "Dummy Organization", orgemail = "org email", orgwebsite = "www.dummy.com",
            orgadmin = "", orgtype = "type", orgTotalMembers = 1)
            
        admin=User(username='admin', password='admin',
                    firstname='admin', lastname='admin',email='admin@admin.com')
        # admin_profile=Profile(profileid='1', firstname='admin', lastname='admin',email='admin@admin.com')
        db.session.add(organization)
        db.session.add(admin)
        db.session.commit()