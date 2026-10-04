"""
Automated Integration Tests for Online Exam and Quiz System
Verifies all core routes, student exam workflow, and admin management.
"""

import unittest
from app import app
from database import init_db

class OnlineExamSystemTestCase(unittest.TestCase):
    def setUp(self):
        init_db()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_homepage_and_login_render(self):
        """Test home page and login page load properly."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Online Exam & Quiz System', res.data)

        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sign In', res.data)

    def test_02_student_demo_login_and_dashboard(self):
        """Test student demo login and dashboard."""
        res = self.client.get('/demo-login/student', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Student Portal', res.data)
        self.assertIn(b'Python Programming Core Quiz', res.data)

    def test_03_exam_lifecycle(self):
        """Test starting, taking, and submitting an exam."""
        # 1. Login as student
        self.client.get('/demo-login/student', follow_redirects=True)

        # 2. View Instructions
        res = self.client.get('/exam/1/start')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Assessment Rules & Guidelines', res.data)

        # 3. Take Exam
        res = self.client.get('/exam/1/take')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Question Palette', res.data)
        self.assertIn(b'timerDisplay', res.data)

        # 4. Submit Exam with Answers
        # In Quiz 1: Q1=C, Q2=B, Q3=C, Q4=B, Q5=A
        payload = {
            'question_1': 'C',
            'question_2': 'B',
            'question_3': 'C',
            'question_4': 'B',
            'question_5': 'A',
            'time_spent_seconds': '120'
        }
        res = self.client.post('/exam/1/submit', data=payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Congratulations, You Passed!', res.data)
        self.assertIn(b'100.0%', res.data)
        self.assertIn(b'Detailed Question & Answer Review', res.data)

    def test_04_certificate_access(self):
        """Test certificate rendering for passed attempt."""
        self.client.get('/demo-login/student', follow_redirects=True)
        # Attempt 1 was seeded as passed (100%)
        res = self.client.get('/exam/certificate/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Certificate of Achievement', res.data)
        self.assertIn(b'VERIFIED CREDENTIAL', res.data)

    def test_05_admin_dashboard_and_controls(self):
        """Test admin login, dashboard, and quiz questions manager."""
        res = self.client.get('/demo-login/admin', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Instructor & Admin Control Center', res.data)
        self.assertIn(b'Assessment Repository', res.data)

        # Manage Questions view
        res = self.client.get('/admin/quiz/1/questions')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Questions in this Assessment', res.data)

        # Results table view
        res = self.client.get('/admin/results')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Candidate Exam Submissions', res.data)

if __name__ == '__main__':
    unittest.main()
