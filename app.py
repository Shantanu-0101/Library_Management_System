from flask import Flask, render_template, request, redirect, session, url_for
from models import db,Student, Admin, Category, Books, Issued_books, Fines, StatusType, IssueRequest, RequestStatus, Notification, BookSuggestion
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import openpyxl
from flask import send_file
import io
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from models import StatusType

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "fa4b1e6579c52d0bbf9a361de6c8635d4333306a3bfead17a8e8e62da826e018"

db.init_app(app)

with app.app_context():
    db.create_all()


#adding admin in DB manually
# with app.app_context():
#     admin = Admin(name="Admin", email="admin@csmss.com", password=generate_password_hash("admin123"))
#     db.session.add(admin)
#     db.session.commit()


#home-page
@app.route('/')
def index():
    return render_template('index.html')

# Student Signup
@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        new_student = Student(
            name = request.form['name'],
            email = request.form['email'],
            password = generate_password_hash(request.form['password']),
            roll_number = request.form['roll_number']
        )

        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('student_login'))
    return render_template('auth/student_signup.html', pending=True)


# Student Login
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student = Student.query.filter_by(email=request.form['email']).first()
        if student and check_password_hash(student.password, request.form['password']):
            if student and check_password_hash(student.password, request.form['password']):
                if not student.is_approved:
                    return render_template('auth/student_login.html', 
                        error='Your account is pending admin approval.')
            session['student_name'] = student.name
            session['student_id'] = student.id
            session['role'] = 'student'
            return redirect(url_for('student_dashboard'))
        return render_template('auth/student_login.html', error='Invalid credentials')
    return render_template('auth/student_login.html')


# Admin Login (no signup — admin added manually in DB)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(email=request.form['email']).first()
        if admin and check_password_hash(admin.password, request.form['password']):
            session['admin_id'] = admin.id
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        return render_template('auth/admin_login.html', error='Invalid credentials')
    return render_template('auth/admin_login.html')


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# add books
@app.route('/add_books', methods=['GET', 'POST'])
def add_books():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category_id = request.form['category_id']
        category_name = request.form['category_id']
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()  # gets the id without full commit
        category_id = category.id
        total_copies = request.form['total_copies']

        file = request.files.get('cover_image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)  # sanitizes the name
            file.save(os.path.join('static/images', filename))
            cover_image = filename  # store just the name in DB
        else:
            cover_image = None

        new_book = Books(title=title, author=author, isbn=isbn, category_id=category_id, total_copies=total_copies, available_copies=total_copies, cover_image=cover_image)
        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for('manage_book'))
    return render_template('admin/add_book.html')

# manage books section
@app.route('/admin/books', methods=['GET'])
def manage_book():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    books = Books.query.all()
    success = request.args.get('success')
    return render_template('admin/manage_books.html', books=books, success=success)


# Excel template download
@app.route('/admin/books/template')
def download_template():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Books"
    ws.append(['title', 'author', 'isbn', 'category', 'total_copies', 'cover_image'])
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return send_file(stream, as_attachment=True,
                     download_name='books_template.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# Excel upload
# @app.route('/admin/books/upload', methods=['POST'])
# def upload_books():
#     if session.get('role') != 'admin':
#         return redirect(url_for('admin_login'))

#     file = request.files.get('excel_file')
#     if not file or file.filename == '':
#         return redirect(url_for('manage_book'))

#     wb = openpyxl.load_workbook(file)
#     ws = wb.active

#     added = 0


#     for row in ws.iter_rows(min_row=2, values_only=True):
#         title  = row[0]
#         author = row[1] if row[1] else 'Unknown'
#         total_copies = row[2]

#         print(f"Processing: {title}")   # ← add this

#         if not title:
#             print("SKIPPED - no title")  # ← add this
#             continue

#         print(f"Adding: {title}")

#         isbn = f"LIB{str(added + 1).zfill(5)}"
#         category_name = 'General'
#         cover_image   = None

#         if not title:        # skip empty rows
#             continue

#         if Books.query.filter_by(title=str(title).strip()).first():
#             continue

#         category = Category.query.filter_by(name=category_name).first()
#         if not category:
#             category = Category(name=category_name)
#             db.session.add(category)
#             db.session.flush()

#         new_book = Books(
#             title=str(title),
#             author=str(author),
#             isbn=str(isbn),
#             category_id=category.id,
#             total_copies=int(total_copies or 1),
#             available_copies=int(total_copies or 1),
#             cover_image=str(cover_image) if cover_image else None
#         )
#         db.session.add(new_book)
#         added += 1

#     try:
#         db.session.commit()
#         print(f"SUCCESS: {added} books added")
#     except Exception as e:
#         db.session.rollback()
#         print(f"ERROR: {e}")
#         return f"Upload failed: {e}"
#     return redirect(url_for('manage_book',success=f"{added} books added"))

# excel Upload
@app.route('/admin/books/upload', methods=['POST'])
def upload_books():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    file = request.files.get('excel_file')
    if not file or file.filename == '':
        return redirect(url_for('add_books'))

    wb = openpyxl.load_workbook(file)
    ws = wb.active

    added   = 0
    skipped = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        title        = row[0]
        author       = row[1] if row[1] else 'Unknown'
        total_copies = row[2]

        if not title:
            skipped += 1
            continue

        if Books.query.filter_by(title=str(title).strip()).first():
            skipped += 1
            continue

        isbn = f"LIB{str(added + 1).zfill(5)}"

        category = Category.query.filter_by(name='General').first()
        if not category:
            category = Category(name='General')
            db.session.add(category)
            db.session.flush()

        new_book = Books(
            title            = str(title).strip(),
            author           = str(author).strip(),
            isbn             = isbn,
            category_id      = category.id,
            total_copies     = int(total_copies or 1),
            available_copies = int(total_copies or 1),
            cover_image      = None
        )
        db.session.add(new_book)
        added += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Upload failed: {str(e)}"

    return redirect(url_for('manage_book',
        success=f"{added} books added, {skipped} skipped"))



# Delete Book
@app.route('/delete/<int:book_id>', methods=['POST'])
def delete(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    book_to_del = Books.query.get_or_404(book_id)
    try:
        db.session.delete(book_to_del)
        db.session.commit()
        return redirect(url_for('manage_book'))
    except:
        return "There is a problem deleting that book"

#Edit Book
@app.route("/admin/books/edit/<int:book_id>/", methods=['GET', 'POST'])
def edit_book(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    
    book_to_edit = Books.query.get_or_404(book_id)

    if request.method == 'POST':
        book_to_edit.title = request.form.get('title')
        book_to_edit.author = request.form.get('author')
        book_to_edit.isbn = request.form.get('isbn')

        total = request.form.get('total_copies', '').strip()
        avail = request.form.get('available_copies', '').strip()

        book_to_edit.total_copies = int(total) if total else book_to_edit.total_copies
        book_to_edit.available_copies = int(avail) if avail else book_to_edit.available_copies
        

        category_name = request.form.get('category')
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()
        book_to_edit.category_id = category.id

        file = request.files.get('cover_image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/images', filename))
            book_to_edit.cover_image = filename

        db.session.commit()
        return redirect(url_for('manage_book'))

    return render_template('admin/edit_book.html', book=book_to_edit)


# Student Browse Books
@app.route('/student/browse_books', methods=['GET'])
def browse_books():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    books = Books.query.all()
    active_count = Issued_books.query.filter_by(
        user_id = session.get('student_id'),
        status  = StatusType.ACTIVE
    ).count()

    return render_template('student/browse_books.html', books=books, active_count=active_count)



# Student requests to issue a book
@app.route('/student/request-issue/<int:book_id>', methods=['POST'])
def request_issue(book_id):
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))

    student_id = session.get('student_id')

    # Check 1 — already has an active issue for this book
    already_issued = Issued_books.query.filter_by(
        user_id = student_id,
        book_id = book_id,
        status  = StatusType.ACTIVE
    ).first()
    if already_issued:
        return redirect(url_for('browse_books', error='already_issued'))

    # Check 2 — already sent a pending request for this book
    pending = IssueRequest.query.filter_by(
        student_id = student_id,
        book_id    = book_id,
        status     = RequestStatus.PENDING
    ).first()
    if pending:
        return redirect(url_for('browse_books', error='already_requested'))

    # Check 3 — book limit of 3
    active_count = Issued_books.query.filter_by(
        user_id = student_id,
        status  = StatusType.ACTIVE
    ).count()
    if active_count >= 3:
        return redirect(url_for('browse_books', error='limit_reached'))

    # All checks passed — create request
    new_request = IssueRequest(
        student_id = student_id,
        book_id    = book_id
    )
    db.session.add(new_request)
    db.session.commit()

    return redirect(url_for('browse_books', success='requested'))

@app.route('/admin/requests/approve/<int:request_id>', methods=['POST'])
def approve_request(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    req  = IssueRequest.query.get_or_404(request_id)
    book = Books.query.get_or_404(req.book_id)

    # check copies still available
    if book.available_copies <= 0:
        req.status = RequestStatus.REJECTED
        db.session.commit()
        return redirect(url_for('admin_requests'))

    # create the issued book record
    new_issue = Issued_books(
        user_id    = req.student_id,
        book_id    = req.book_id,
        issue_date = datetime.now(timezone.utc),
        due_date   = datetime.now(timezone.utc) + timedelta(days=14),
        status     = StatusType.ACTIVE
    )

    # update book copies and request status
    book.available_copies -= 1
    req.status = RequestStatus.APPROVED

    db.session.add(new_issue)
    db.session.commit()

    return redirect(url_for('admin_requests'))


# Admin rejects a request
@app.route('/admin/requests/reject/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    req        = IssueRequest.query.get_or_404(request_id)
    req.status = RequestStatus.REJECTED
    req.rejection_reason = request.form.get('reason', 'No reason provided')
    db.session.commit()

    return redirect(url_for('admin_requests'))


# Admin sees all pending requests
@app.route('/admin/requests')
def admin_requests():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    pending  = IssueRequest.query.filter_by(status=RequestStatus.PENDING).all()
    approved = IssueRequest.query.filter_by(status=RequestStatus.APPROVED).all()
    rejected = IssueRequest.query.filter_by(status=RequestStatus.REJECTED).all()

    return render_template('admin/requests.html',
        pending  = pending,
        approved = approved,
        rejected = rejected
    )


# Student Issued Books section
@app.route('/student/my_issued_books')
def my_books():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))

    student_id = session.get('student_id')

    # fetch only ACTIVE issued books for this student
    # also join with Books so we can show title, author in template
    issued = Issued_books.query.filter_by(
        user_id=student_id,
        status=StatusType.ACTIVE
    ).all()

    return render_template('student/my_issued_books.html', issued=issued, now = datetime.now())


# Return Book 
@app.route('/admin/issued/return/<int:issued_id>', methods=['POST'])
def admin_return_book(issued_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    record      = Issued_books.query.get_or_404(issued_id)
    return_date = datetime.now(timezone.utc)

    record.return_date = return_date
    record.status      = StatusType.INACTIVE
    record.book.available_copies += 1

    # fine calculation
    fine_per_day = 2
    due_date = record.due_date.replace(tzinfo=timezone.utc)

    if return_date > due_date:
        overdue_days = (return_date - due_date).days
        amount       = overdue_days * fine_per_day

        new_fine = Fines(
            user_id         = record.user_id,
            issued_books_id = record.id,
            amount          = amount,
            paid            = False
        )
        db.session.add(new_fine)

    db.session.commit()
    return redirect(url_for('admin_issued'))


# Calculate Fine
@app.route('/student/my_fines')
def my_fines():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))

    student_id = session.get('student_id')

    fines = Fines.query.filter_by(user_id=student_id).all()

    return render_template('student/my_fines.html', fines=fines)

# Student Dashboards
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))

    student_id = session.get('student_id')
    today = datetime.now()

    # active issued books
    active_books = Issued_books.query.filter_by(
        user_id=student_id,
        status=StatusType.ACTIVE
    ).all()

    # count returned books
    returned_count = Issued_books.query.filter_by(
        user_id=student_id,
        status=StatusType.INACTIVE
    ).count()

    # books due within 3 days
    due_soon = [
        b for b in active_books
        if b.due_date and (b.due_date - today).days <= 3
    ]

    # fines
    all_fines = Fines.query.filter_by(user_id=student_id).all()
    total_fine = sum(f.amount for f in all_fines)
    unpaid_fine = sum(f.amount for f in all_fines if not f.paid)

    notifications = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    return render_template('student/dashboard.html',
        active_books = active_books,
        returned_count = returned_count,
        due_soon_count = len(due_soon),
        total_fine = total_fine,
        unpaid_fine = unpaid_fine,
        student_name = session.get('student_name'),
        notifications = notifications,
        now = datetime.now()
    )


# Admin manage student section
@app.route('/admin/students')
def manage_students():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    
    students = Student.query.all()
    return render_template('admin/manage_students.html', students=students, StatusType=StatusType)

# Admin view student details 
@app.route('/admin/students/<int:student_id>')
def student_detail(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    
    student = Student.query.get_or_404(student_id)
    return render_template('admin/student_detail.html', student=student)


# Admin issued books section
@app.route('/admin/issued')
def admin_issued():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    filter_by = request.args.get('filter')

    if filter_by == 'active':
        issued = Issued_books.query.filter_by(status=StatusType.ACTIVE).all()
    elif filter_by == 'returned':
        issued = Issued_books.query.filter_by(status=StatusType.INACTIVE).all()
    else:
        issued = Issued_books.query.all()

    return render_template('admin/issued_books.html',
        issued = issued,
        now = datetime.now()
    )

# Admin Fines section
@app.route('/admin/fines')
def admin_fines():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    filter_by = request.args.get('filter')

    if filter_by == 'unpaid':
        fines = Fines.query.filter_by(paid=False).all()
    elif filter_by == 'paid':
        fines = Fines.query.filter_by(paid=True).all()
    else:
        fines = Fines.query.all()

    total_unpaid    = sum(f.amount for f in Fines.query.all() if not f.paid)
    total_collected = sum(f.amount for f in Fines.query.all() if f.paid)

    return render_template('admin/fines.html',
        fines = fines,
        total_unpaid = total_unpaid,
        total_collected = total_collected
    )


# Mark fine as paid
@app.route('/admin/fines/paid/<int:fine_id>', methods=['POST'])
def mark_paid(fine_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    fine = Fines.query.get_or_404(fine_id)
    fine.paid = True
    db.session.commit()
    return redirect(url_for('admin_fines'))

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    total_books      = Books.query.count()
    total_students   = Student.query.count()
    total_issued     = Issued_books.query.filter_by(status=StatusType.ACTIVE).count()
    total_returned   = Issued_books.query.filter_by(status=StatusType.INACTIVE).count()
    total_fines      = db.session.query(db.func.sum(Fines.amount)).scalar() or 0
    unpaid_fines     = db.session.query(db.func.sum(Fines.amount)).filter_by(paid=False).scalar() or 0

    # overdue books — active issues where due_date has passed
    now = datetime.now(timezone.utc)
    all_active = Issued_books.query.filter_by(status=StatusType.ACTIVE).all()
    overdue_count = sum(
        1 for r in all_active
        if r.due_date and r.due_date.replace(tzinfo=timezone.utc) < now
    )

    # recent 5 issued records for activity table
    recent_issued = Issued_books.query.order_by(
        Issued_books.issue_date.desc()
    ).limit(5).all()

    # books per category
    categories     = Category.query.all()
    category_names = [c.name for c in categories]
    category_counts = [
        Books.query.filter_by(category_id=c.id).count()
        for c in categories
    ]

    return render_template('admin/dashboard.html',
        total_books = total_books,
        total_students = total_students,
        total_issued = total_issued,
        total_returned = total_returned,
        total_fines = total_fines,
        unpaid_fines = unpaid_fines,
        overdue_count = overdue_count,
        recent_issued = recent_issued,
        now = now,
        category_names  = category_names,
        category_counts = category_counts
    )

# Admin approve student route
@app.route('/admin/students/approve/<int:student_id>', methods=['POST'])
def approve_student(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(student_id)
    student.is_approved = True
    db.session.commit()
    return redirect(url_for('manage_students'))

# student request section
@app.route('/student/my_requests')
def my_requests():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))

    requests = IssueRequest.query.filter_by(
        student_id=session.get('student_id')
    ).order_by(IssueRequest.created_at.desc()).all()

    return render_template('student/my_requests.html', requests=requests)


# Admin post notification
@app.route('/admin/notifications', methods=['GET', 'POST'])
def admin_notifications():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        new_notif = Notification(
            title   = request.form['title'],
            message = request.form['message']
        )
        db.session.add(new_notif)
        db.session.commit()

    notifications = Notification.query.order_by(
        Notification.created_at.desc()
    ).all()

    return render_template('admin/notifications.html',
        notifications=notifications
    )


# Delete notification
@app.route('/admin/notifications/delete/<int:notif_id>', methods=['POST'])
def delete_notification(notif_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    notif = Notification.query.get_or_404(notif_id)
    db.session.delete(notif)
    db.session.commit()
    return redirect(url_for('admin_notifications'))

# Student's book suggestion section
# Student submits book suggestion
@app.route('/student/suggest_book', methods=['GET', 'POST'])
def suggest_book():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))

    if request.method == 'POST':
        new_suggestion = BookSuggestion(
            student_id = session.get('student_id'),
            title      = request.form['title'],
            author     = request.form.get('author'),
            reason     = request.form.get('reason')
        )
        db.session.add(new_suggestion)
        db.session.commit()
        return render_template('student/suggest_book.html', success=True)

    return render_template('student/suggest_book.html')


# Admin views all suggestions
@app.route('/admin/suggestions')
def admin_suggestions():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    suggestions = BookSuggestion.query.order_by(
        BookSuggestion.created_at.desc()
    ).all()
    return render_template('admin/suggestions.html', suggestions=suggestions)

if __name__ == "__main__":
    app.run(debug=True)