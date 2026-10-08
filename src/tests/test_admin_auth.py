import unittest

from fastapi.testclient import TestClient

import app as app_module
from teacher_auth import hash_password


class AdminAuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app_module.app)

    def setUp(self):
        app_module.teacher_sessions.clear()
        app_module.teacher_credentials = {
            "teacher": hash_password("correct-password")
        }
        self.activity_name = "Chess Club"
        self.email = "new-student@mergington.edu"
        participants = app_module.activities[self.activity_name]["participants"]
        if self.email in participants:
            participants.remove(self.email)
        self.client.cookies.clear()

    def tearDown(self):
        participants = app_module.activities[self.activity_name]["participants"]
        if self.email in participants:
            participants.remove(self.email)

    def login(self):
        return self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "correct-password"},
        )

    def test_activities_remain_public(self):
        response = self.client.get("/activities")

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.activity_name, response.json())

    def test_registration_mutations_require_teacher_login(self):
        signup_response = self.client.post(
            f"/activities/{self.activity_name}/signup",
            params={"email": self.email},
        )
        unregister_response = self.client.delete(
            f"/activities/{self.activity_name}/unregister",
            params={"email": "michael@mergington.edu"},
        )

        self.assertEqual(signup_response.status_code, 401)
        self.assertEqual(unregister_response.status_code, 401)
        self.assertNotIn(
            self.email,
            app_module.activities[self.activity_name]["participants"],
        )
        self.assertIn(
            "michael@mergington.edu",
            app_module.activities[self.activity_name]["participants"],
        )

    def test_invalid_password_does_not_create_session(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(app_module.SESSION_COOKIE, response.cookies)

    def test_teacher_can_register_and_unregister_student(self):
        login_response = self.login()
        signup_response = self.client.post(
            f"/activities/{self.activity_name}/signup",
            params={"email": self.email},
        )
        unregister_response = self.client.delete(
            f"/activities/{self.activity_name}/unregister",
            params={"email": self.email},
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(signup_response.status_code, 200)
        self.assertEqual(unregister_response.status_code, 200)

    def test_logout_invalidates_teacher_session(self):
        self.login()
        logout_response = self.client.post("/auth/logout")
        signup_response = self.client.post(
            f"/activities/{self.activity_name}/signup",
            params={"email": self.email},
        )

        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(signup_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
