from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import enum

db = SQLAlchemy()

# Student Table
class Student(db.Model):
    __tablename__ = 'Students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    roll_number = db.Column(db.String(20), nullable=False, unique=True)
    is_approved = db.Column(db.Boolean, default=False)

    issued_books = db.relationship('Issued_books', backref='student', lazy=True)
    fines = db.relationship('Fines', backref='student', lazy=True)

# Admin 
class Admin(db.Model):
    __tablename__ = 'Admins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)


# Books Table (id, title, author, isbn, category_id, total_copies, available_copies, cover_image)
class Books(db.Model):
    __tablename__ = 'Books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(500), nullable=False)
    isbn = db.Column(db.String(140), nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    total_copies = db.Column(db.Integer, nullable=False)
    available_copies = db.Column(db.Integer, nullable=False)
    cover_image = db.Column(db.String(200))


# categories table
class Category(db.Model):
    __tablename__ = 'Categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)



class StatusType(enum.Enum):
    ACTIVE = "issued"
    INACTIVE = "returned"

# issued book (id, user_id, book_id, issue_date, due_date, return_date, status (issued / returned))
class Issued_books(db.Model):
    __tablename__ = 'Issued_Books'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Students.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('Books.id'), nullable=False)
    issue_date  = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=True)   # set manually in route
    return_date = db.Column(db.DateTime, nullable=True)   # empty until returned
    status = db.Column(db.Enum(StatusType), nullable=False, default=StatusType.ACTIVE)

    book = db.relationship('Books', backref='issued_records', lazy=True)


# Fines Table (id, user_id, issued_book_id, amount, paid (true/false))
class Fines(db.Model):
    __tablename__ = 'Fines'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Students.id'), nullable=False)
    issued_books_id = db.Column(db.Integer, db.ForeignKey('Issued_Books.id'))
    amount = db.Column(db.Float, nullable=False, default=0.0)
    paid = db.Column(db.Boolean, default=False)
    issued_book = db.relationship('Issued_books', backref='fine', lazy=True)


class RequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class IssueRequest(db.Model):
    __tablename__ = 'IssueRequests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('Students.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('Books.id'),    nullable=False)
    status = db.Column(db.Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    rejection_reason = db.Column(db.String(200), nullable=True)

    student = db.relationship('Student', backref='requests', lazy=True)
    book = db.relationship('Books',   backref='requests', lazy=True)


class Notification(db.Model):
    __tablename__ = 'Notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class BookSuggestion(db.Model):
    __tablename__ = 'BookSuggestions'

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('Students.id'), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    author     = db.Column(db.String(100), nullable=True)
    reason     = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    student = db.relationship('Student', backref='suggestions', lazy=True)