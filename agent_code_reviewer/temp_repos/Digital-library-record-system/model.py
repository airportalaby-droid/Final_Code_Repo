from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy()

class studentsform(db.Model):
    Id=db.Column(db.Integer,primary_key=True)
    Name=db.Column(db.String(100), unique=True, nullable=False)
    issue_date=db.Column(db.Date)
    return_date=db.Column(db.Date)

    Mail_id=db.Column(db.String(100),nullable=False)
    book_id=db.Column(db.Integer)
    Department=db.Column(db.String(100),nullable=False)
    college=db.Column(db.String(200),nullable=False)



