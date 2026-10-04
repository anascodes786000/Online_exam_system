"""
Online Exam & Quiz System - Main Flask Application
Features: User Authentication, Student Exam Engine, Admin Management & Results Analytics.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import json
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "online_exam_super_secret_key_change_in_production"

# ==========================================
# Authentication & Role Decorators
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Admin access required for this action.", "danger")
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# Public & Auth Routes
# ==========================================

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? OR username = ?",
            (login_identifier, login_identifier)
        ).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f"Welcome back, {user['full_name']}!", "success")
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid email/username or password.", "danger")

    return render_template('login.html')

@app.route('/demo-login/<role>')
def demo_login(role):
    """Quick one-click login for demonstration and project testing."""
    db = get_db()
    if role == 'admin':
        user = db.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    else:
        user = db.execute("SELECT * FROM users WHERE role = 'student' LIMIT 1").fetchone()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['email'] = user['email']
        session['role'] = user['role']
        flash(f"Logged in as Demo {user['role'].capitalize()} ({user['full_name']}).", "info")
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))

    flash("Demo user not found. Please register an account.", "warning")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')

        if role not in ['student', 'admin']:
            role = 'student'

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        db = get_db()
        # Check uniqueness
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing:
            flash("Username or Email already registered. Please login.", "warning")
            return render_template('register.html')

        hashed_pass = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (username, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (username, full_name, email, hashed_pass, role)
        )
        db.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))

# ==========================================
# Student Routes
# ==========================================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    db = get_db()
    user_id = session['user_id']

    # Fetch active quizzes
    quizzes = db.execute("""
        SELECT q.*, COUNT(ques.id) AS total_questions,
               SUM(ques.marks) AS total_marks
        FROM quizzes q
        LEFT JOIN questions ques ON q.id = ques.quiz_id
        WHERE q.is_active = 1
        GROUP BY q.id
        ORDER BY q.created_at DESC
    """).fetchall()

    # Fetch past attempts
    attempts = db.execute("""
        SELECT a.*, q.title as quiz_title, q.passing_percentage
        FROM attempts a
        JOIN quizzes q ON a.quiz_id = q.id
        WHERE a.user_id = ?
        ORDER BY a.submitted_at DESC
    """, (user_id,)).fetchall()

    # Statistics
    total_taken = len(attempts)
    passed_count = sum(1 for a in attempts if a['passed'] == 1)
    avg_score = round(sum(a['percentage'] for a in attempts) / total_taken, 1) if total_taken > 0 else 0

    return render_template(
        'student/dashboard.html',
        quizzes=quizzes,
        attempts=attempts,
        total_taken=total_taken,
        passed_count=passed_count,
        avg_score=avg_score
    )

@app.route('/exam/<int:quiz_id>/start')
@login_required
def exam_instructions(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ? AND is_active = 1", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found or currently inactive.", "danger")
        return redirect(url_for('student_dashboard'))

    questions_count = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(marks), 0) FROM questions WHERE quiz_id = ?",
        (quiz_id,)
    ).fetchone()

    total_questions = questions_count[0]
    total_marks = questions_count[1]

    if total_questions == 0:
        flash("This quiz currently has no questions assigned. Please check back later.", "warning")
        return redirect(url_for('student_dashboard'))

    return render_template(
        'student/start.html',
        quiz=quiz,
        total_questions=total_questions,
        total_marks=total_marks
    )

@app.route('/exam/<int:quiz_id>/take')
@login_required
def take_exam(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ? AND is_active = 1", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found or not active.", "danger")
        return redirect(url_for('student_dashboard'))

    questions = db.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d, marks FROM questions WHERE quiz_id = ? ORDER BY id ASC",
        (quiz_id,)
    ).fetchall()

    if not questions:
        flash("This exam has no questions available yet.", "warning")
        return redirect(url_for('student_dashboard'))

    # Store exam start time in session if not present
    session[f'exam_started_{quiz_id}'] = True

    return render_template(
        'student/take_exam.html',
        quiz=quiz,
        questions=questions,
        duration_minutes=quiz['duration_minutes']
    )

@app.route('/exam/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_exam(quiz_id):
    db = get_db()
    user_id = session['user_id']

    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('student_dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,)).fetchall()
    
    total_marks = sum(q['marks'] for q in questions)
    user_score = 0
    user_answers = {}

    for q in questions:
        field_name = f"question_{q['id']}"
        selected = request.form.get(field_name) # 'A', 'B', 'C', 'D' or None
        user_answers[str(q['id'])] = selected
        if selected and selected.upper() == q['correct_option'].upper():
            user_score += q['marks']

    percentage = round((user_score / total_marks * 100), 2) if total_marks > 0 else 0.0
    passed = 1 if percentage >= quiz['passing_percentage'] else 0
    time_spent = int(request.form.get('time_spent_seconds', 0))

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO attempts (user_id, quiz_id, score, total_marks, percentage, passed, time_spent_seconds, answers_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        quiz_id,
        user_score,
        total_marks,
        percentage,
        passed,
        time_spent,
        json.dumps(user_answers)
    ))
    attempt_id = cursor.lastrowid
    db.commit()

    flash("Exam submitted successfully! Here is your performance scorecard.", "success")
    return redirect(url_for('exam_result', attempt_id=attempt_id))

@app.route('/exam/result/<int:attempt_id>')
@login_required
def exam_result(attempt_id):
    db = get_db()
    user_id = session['user_id']
    role = session.get('role')

    attempt = db.execute("""
        SELECT a.*, q.title as quiz_title, q.category, q.passing_percentage, u.full_name, u.email
        FROM attempts a
        JOIN quizzes q ON a.quiz_id = q.id
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ?
    """, (attempt_id,)).fetchone()

    if not attempt:
        flash("Result not found.", "danger")
        return redirect(url_for('student_dashboard'))

    # Security check: only candidate or admin can view
    if role != 'admin' and attempt['user_id'] != user_id:
        flash("Access unauthorized for this exam result.", "danger")
        return redirect(url_for('student_dashboard'))

    # Retrieve question details for review
    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (attempt['quiz_id'],)).fetchall()
    user_answers = json.loads(attempt['answers_json']) if attempt['answers_json'] else {}

    # Calculate statistics for review
    correct_count = 0
    incorrect_count = 0
    unattempted_count = 0

    detailed_review = []
    for q in questions:
        user_ans = user_answers.get(str(q['id']))
        is_correct = (user_ans == q['correct_option'])
        is_skipped = (user_ans is None or user_ans == "")

        if is_skipped:
            unattempted_count += 1
            status = "skipped"
        elif is_correct:
            correct_count += 1
            status = "correct"
        else:
            incorrect_count += 1
            status = "wrong"

        detailed_review.append({
            'question': q,
            'user_choice': user_ans,
            'is_correct': is_correct,
            'is_skipped': is_skipped,
            'status': status
        })

    return render_template(
        'student/result.html',
        attempt=attempt,
        detailed_review=detailed_review,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unattempted_count=unattempted_count,
        total_questions=len(questions)
    )

@app.route('/exam/certificate/<int:attempt_id>')
@login_required
def certificate(attempt_id):
    db = get_db()
    attempt = db.execute("""
        SELECT a.*, q.title as quiz_title, u.full_name
        FROM attempts a
        JOIN quizzes q ON a.quiz_id = q.id
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ? AND a.passed = 1
    """, (attempt_id,)).fetchone()

    if not attempt:
        flash("Certificate is only available for passed attempts.", "warning")
        return redirect(url_for('student_dashboard'))

    if session.get('role') != 'admin' and attempt['user_id'] != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('student_dashboard'))

    return render_template('student/certificate.html', attempt=attempt)

# ==========================================
# Admin Routes
# ==========================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()

    total_quizzes = db.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
    total_students = db.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    total_attempts = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    avg_score_raw = db.execute("SELECT AVG(percentage) FROM attempts").fetchone()[0]
    avg_score = round(avg_score_raw, 1) if avg_score_raw is not None else 0.0

    quizzes = db.execute("""
        SELECT q.*, COUNT(DISTINCT ques.id) as question_count,
               COUNT(DISTINCT a.id) as attempt_count,
               COALESCE(SUM(ques.marks), 0) as total_marks
        FROM quizzes q
        LEFT JOIN questions ques ON q.id = ques.quiz_id
        LEFT JOIN attempts a ON q.id = a.quiz_id
        GROUP BY q.id
        ORDER BY q.created_at DESC
    """).fetchall()

    recent_attempts = db.execute("""
        SELECT a.*, u.full_name, u.email, q.title as quiz_title
        FROM attempts a
        JOIN users u ON a.user_id = u.id
        JOIN quizzes q ON a.quiz_id = q.id
        ORDER BY a.submitted_at DESC
        LIMIT 6
    """).fetchall()

    return render_template(
        'admin/dashboard.html',
        total_quizzes=total_quizzes,
        total_students=total_students,
        total_attempts=total_attempts,
        avg_score=avg_score,
        quizzes=quizzes,
        recent_attempts=recent_attempts
    )

@app.route('/admin/quiz/new', methods=['GET', 'POST'])
@admin_required
def admin_create_quiz():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        duration = int(request.form.get('duration_minutes', 15))
        passing_percentage = int(request.form.get('passing_percentage', 50))
        is_active = 1 if request.form.get('is_active') == '1' else 0

        if not title:
            flash("Quiz title is required.", "danger")
            return render_template('admin/quiz_form.html', quiz=None)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO quizzes (title, description, category, duration_minutes, passing_percentage, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, category, duration, passing_percentage, is_active, session['user_id']))
        new_quiz_id = cursor.lastrowid
        db.commit()

        flash("Quiz created successfully! Now add questions to it.", "success")
        return redirect(url_for('admin_quiz_questions', quiz_id=new_quiz_id))

    return render_template('admin/quiz_form.html', quiz=None)

@app.route('/admin/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_quiz(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        duration = int(request.form.get('duration_minutes', 15))
        passing_percentage = int(request.form.get('passing_percentage', 50))
        is_active = 1 if request.form.get('is_active') == '1' else 0

        db.execute("""
            UPDATE quizzes
            SET title = ?, description = ?, category = ?, duration_minutes = ?, passing_percentage = ?, is_active = ?
            WHERE id = ?
        """, (title, description, category, duration, passing_percentage, is_active, quiz_id))
        db.commit()

        flash("Quiz details updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/quiz_form.html', quiz=quiz)

@app.route('/admin/quiz/<int:quiz_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_quiz(quiz_id):
    db = get_db()
    db.execute("UPDATE quizzes SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (quiz_id,))
    db.commit()
    flash("Quiz visibility status toggled.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
@admin_required
def admin_delete_quiz(quiz_id):
    db = get_db()
    db.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    db.commit()
    flash("Quiz and its related questions/attempts have been deleted.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/<int:quiz_id>/questions')
@admin_required
def admin_quiz_questions(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (quiz_id,)).fetchall()
    total_marks = sum(q['marks'] for q in questions)

    return render_template('admin/questions.html', quiz=quiz, questions=questions, total_marks=total_marks)

@app.route('/admin/quiz/<int:quiz_id>/questions/add', methods=['POST'])
@admin_required
def admin_add_question(quiz_id):
    q_text = request.form.get('question_text', '').strip()
    opt_a = request.form.get('option_a', '').strip()
    opt_b = request.form.get('option_b', '').strip()
    opt_c = request.form.get('option_c', '').strip()
    opt_d = request.form.get('option_d', '').strip()
    correct_opt = request.form.get('correct_option', 'A').strip().upper()
    explanation = request.form.get('explanation', '').strip()
    marks = int(request.form.get('marks', 1))

    if not all([q_text, opt_a, opt_b, opt_c, opt_d]):
        flash("All question options and question text must be filled.", "danger")
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))

    db = get_db()
    db.execute("""
        INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (quiz_id, q_text, opt_a, opt_b, opt_c, opt_d, correct_opt, explanation, marks))
    db.commit()

    flash("New question added successfully!", "success")
    return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))

@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def admin_delete_question(question_id):
    db = get_db()
    question = db.execute("SELECT quiz_id FROM questions WHERE id = ?", (question_id,)).fetchone()
    if question:
        quiz_id = question['quiz_id']
        db.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        db.commit()
        flash("Question deleted.", "info")
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))

    flash("Question not found.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/results')
@admin_required
def admin_results():
    db = get_db()
    quiz_filter = request.args.get('quiz_id')

    query = """
        SELECT a.*, u.full_name, u.email, u.username, q.title as quiz_title
        FROM attempts a
        JOIN users u ON a.user_id = u.id
        JOIN quizzes q ON a.quiz_id = q.id
    """
    params = []
    if quiz_filter and quiz_filter.isdigit():
        query += " WHERE a.quiz_id = ?"
        params.append(int(quiz_filter))

    query += " ORDER BY a.submitted_at DESC"

    attempts = db.execute(query, params).fetchall()
    quizzes = db.execute("SELECT id, title FROM quizzes ORDER BY title ASC").fetchall()

    return render_template('admin/results.html', attempts=attempts, quizzes=quizzes, selected_quiz=quiz_filter)

@app.route('/admin/attempt/<int:attempt_id>/delete', methods=['POST'])
@admin_required
def admin_delete_attempt(attempt_id):
    db = get_db()
    db.execute("DELETE FROM attempts WHERE id = ?", (attempt_id,))
    db.commit()
    flash("Attempt record deleted successfully.", "info")
    return redirect(request.referrer or url_for('admin_results'))

# ==========================================
# Run Server
# ==========================================

if __name__ == '__main__':
    init_db()
    print("Online Exam & Quiz System is running on http://127.0.0.1:5001")
    print("Mobile access on your Wi-Fi: http://10.131.240.31:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
