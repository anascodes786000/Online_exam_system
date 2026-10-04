"""
Database module for Online Exam and Quiz System
Handles SQLite connection, schema initialization, and sample seed data.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'exam_system.db')

def get_db():
    """Get a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Create tables if they do not exist and seed initial demo data."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', -- 'admin' or 'student'
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Quizzes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'General',
        duration_minutes INTEGER NOT NULL DEFAULT 15,
        passing_percentage INTEGER NOT NULL DEFAULT 50,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 3. Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL, -- 'A', 'B', 'C', or 'D'
        explanation TEXT,
        marks INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """)

    # 4. Exam Attempts / Submissions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        total_marks INTEGER NOT NULL DEFAULT 0,
        percentage REAL NOT NULL DEFAULT 0.0,
        passed INTEGER NOT NULL DEFAULT 0, -- 1 for pass, 0 for fail
        time_spent_seconds INTEGER DEFAULT 0,
        answers_json TEXT, -- JSON record of user answers
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    seed_demo_data(conn)
    conn.close()

def seed_demo_data(conn):
    """Seed default users and sample quizzes if database is empty."""
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@exam.com'")
    admin = cursor.fetchone()

    if not admin:
        # Create Default Admin
        admin_pass = generate_password_hash("admin123")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name)
            VALUES (?, ?, ?, 'admin', ?)
        """, ('admin', 'admin@exam.com', admin_pass, 'System Administrator'))
        admin_id = cursor.lastrowid

        # Create Default Student
        student_pass = generate_password_hash("student123")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name)
            VALUES (?, ?, ?, 'student', ?)
        """, ('student', 'student@exam.com', student_pass, 'Alex Student'))
        student_id = cursor.lastrowid

        # Seed Quiz 1: Python Fundamentals
        cursor.execute("""
            INSERT INTO quizzes (title, description, category, duration_minutes, passing_percentage, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            'Python Programming Core Quiz',
            'Test your understanding of Python syntax, data types, scoping, and built-in methods.',
            'Programming',
            10,
            60,
            admin_id
        ))
        quiz1_id = cursor.lastrowid

        quiz1_questions = [
            (
                quiz1_id,
                "Which of the following is an immutable data type in Python?",
                "List", "Dictionary", "Tuple", "Set",
                "C",
                "Tuples are immutable sequences; once created, their elements cannot be modified, added, or removed.",
                2
            ),
            (
                quiz1_id,
                "What is the output of bool('False') in Python?",
                "False", "True", "None", "Error",
                "B",
                "Any non-empty string in Python evaluates to True when cast to a boolean.",
                2
            ),
            (
                quiz1_id,
                "Which keyword is used to create a generator function in Python?",
                "return", "generate", "yield", "produce",
                "C",
                "The 'yield' statement suspends function execution and returns a generator iterator.",
                2
            ),
            (
                quiz1_id,
                "What will `print(2 ** 3 ** 2)` evaluate to in Python?",
                "64", "512", "128", "256",
                "B",
                "The exponentiation operator `**` has right-to-left associativity in Python. So 3**2 = 9, and 2**9 = 512.",
                2
            ),
            (
                quiz1_id,
                "How do you define a function that accepts any number of positional arguments?",
                "def func(*args):", "def func(**kwargs):", "def func(args...):", "def func(&args):",
                "A",
                "`*args` collects arbitrary positional arguments into a tuple.",
                2
            )
        ]
        cursor.executemany("""
            INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, quiz1_questions)

        # Seed Quiz 2: Web & Full Stack Technologies
        cursor.execute("""
            INSERT INTO quizzes (title, description, category, duration_minutes, passing_percentage, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            'Web Development & HTTP Concepts',
            'Essential questions covering HTTP methods, status codes, REST APIs, and front-end fundamentals.',
            'Web Development',
            10,
            50,
            admin_id
        ))
        quiz2_id = cursor.lastrowid

        quiz2_questions = [
            (
                quiz2_id,
                "Which HTTP status code represents '404'?",
                "Unauthorized", "Bad Request", "Not Found", "Internal Server Error",
                "C",
                "HTTP 404 indicates the origin server did not find a current representation for the target resource.",
                2
            ),
            (
                quiz2_id,
                "Which HTTP method is typically idempotent according to RFC specifications?",
                "POST", "GET", "PATCH", "CONNECT",
                "B",
                "GET, PUT, and DELETE are idempotent; multiple identical requests have the same intended effect as a single request.",
                2
            ),
            (
                quiz2_id,
                "In CSS Flexbox, which property aligns items along the cross axis?",
                "justify-content", "align-items", "flex-direction", "grid-template",
                "B",
                "`align-items` defines the default behavior for how flex items are laid out along the cross axis on the current line.",
                2
            ),
            (
                quiz2_id,
                "What is the primary role of a JSON Web Token (JWT)?",
                "Database encryption", "Securely transmitting information between parties as a JSON object", "Styling user interfaces", "Compiling JavaScript",
                "B",
                "JWTs provide a compact, self-contained way for securely transmitting claims between parties.",
                2
            )
        ]
        cursor.executemany("""
            INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, quiz2_questions)

        # Seed Quiz 3: Database & SQL
        cursor.execute("""
            INSERT INTO quizzes (title, description, category, duration_minutes, passing_percentage, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            'Database & SQL Essentials',
            'Relational database design, keys, joins, normalization, and ACID properties.',
            'Database',
            8,
            50,
            admin_id
        ))
        quiz3_id = cursor.lastrowid

        quiz3_questions = [
            (
                quiz3_id,
                "What does the 'A' in ACID properties of a database transaction stand for?",
                "Accuracy", "Atomicity", "Availability", "Authentication",
                "B",
                "Atomicity guarantees that all operations within a transaction succeed or all fail together (all or nothing).",
                2
            ),
            (
                quiz3_id,
                "Which SQL clause is used to filter records after aggregation (GROUP BY)?",
                "WHERE", "HAVING", "FILTER", "ORDER BY",
                "B",
                "`HAVING` filters aggregated groups, whereas `WHERE` filters individual rows prior to grouping.",
                2
            ),
            (
                quiz3_id,
                "Which normal form eliminates partial dependency on a composite primary key?",
                "1NF", "2NF", "3NF", "BCNF",
                "B",
                "Second Normal Form (2NF) requires 1NF and guarantees that all non-key attributes are fully functionally dependent on the primary key.",
                2
            )
        ]
        cursor.executemany("""
            INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, quiz3_questions)

        # Seed a sample attempt for student
        sample_answers = '{"1": "C", "2": "B", "3": "C", "4": "B", "5": "A"}'
        cursor.execute("""
            INSERT INTO attempts (user_id, quiz_id, score, total_marks, percentage, passed, time_spent_seconds, answers_json)
            VALUES (?, ?, 10, 10, 100.0, 1, 195, ?)
        """, (student_id, quiz1_id, sample_answers))

        conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized and seeded successfully at:", DB_PATH)
