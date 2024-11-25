from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db=SQLAlchemy(app)

class User(db.Model):
    __TableName__ = 'user'
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    uname = db.Column(db.String(50), nullable=False, unique=True)
    passhash = db.Column(db.String(1024), nullable=False)
    profileid = db.Column(db.String(1024), nullable=False)
    role = db.Column(db.String(10), nullable=False)
     
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Profile(db.Model):
    __TableName__ = 'profile'
    profileid = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20))
    email = db.Column(db.String(50), nullable=False, unique=True)
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)

class Questions(db.Model):
    __tablename__ = 'Questions'
    questionid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    question_title = db.Column(db.String(50), nullable=False)
    question_detail = db.Column(db.String(200), nullable=False)
    plus_one = db.Column(db.Integer, nullable=False,default=0)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    official_answer = db.Column(db.String(200), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    ai_answer = db.Column(db.Boolean, nullable=False,default=False)
    
    def serializer(self):
        return {
            'questionid': self.questionid,
            'question_title': self.question_title,
            'question_detail': self.question_detail,
            'plus_one': self.plus_one,
            'userid': self.userid,
            'official_answer': self.official_answer
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
    marked_as_official = db.Column(db.Boolean, nullable=False)
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
            'marked_as_official': self.marked_as_official
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

with app.app_context():
    db.create_all()

    admin=User.query.filter_by(uname='admin').first()
    if not admin:
        admin=User(uname='admin', password='admin', role='manager', profileid='1')
        admin_profile=Profile(profileid='1', firstname='admin', lastname='admin',email='admin@admin.com')
        db.session.add(admin)
        db.session.add(admin_profile)
        db.session.commit()