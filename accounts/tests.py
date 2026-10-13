from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class AuthenticationViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='sam_student',
            email='sam@campus.edu',
            password='testpassword123',
            first_name='Sam',
            last_name='Taylor'
        )

    def test_login_page_renders_clean_template(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good to have you back.")
        self.assertContains(response, "Every belonging has a way back.")
        self.assertContains(response, "belong.")
        self.assertContains(response, 'data-target="login-password-field"')

    def test_registration_page_renders_clean_template(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Find your place here.")
        self.assertContains(response, "Create account")
        self.assertContains(response, 'data-target="reg-password-field"')
        self.assertContains(response, 'data-target="reg-confirm-password-field"')

    def test_valid_login_via_username(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'sam_student',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('items:index'))

    def test_valid_login_via_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'sam@campus.edu',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('items:index'))

    def test_invalid_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'sam_student',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email/username or password")

    def test_valid_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Emma',
            'last_name': 'Watson',
            'username': 'emma_w',
            'email': 'emma@campus.edu',
            'password': 'StrongPassword!123',
            'confirm_password': 'StrongPassword!123',
            'campus_id': 'STU-1029',
            'department': 'Literature',
            'phone_number': '555-1234',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.filter(username='emma_w').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, 'emma@campus.edu')
        self.assertEqual(new_user.profile.campus_id, 'STU-1029')

    def test_registration_password_mismatch_failure(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Emma',
            'last_name': 'Watson',
            'username': 'emma_w2',
            'email': 'emma2@campus.edu',
            'password': 'PasswordA',
            'confirm_password': 'PasswordB',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")

    def test_my_activity_page(self):
        self.client.login(username='sam_student', password='testpassword123')
        response = self.client.get('/my-activity/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Activity dashboard")

    def test_admin_dashboard_access_control(self):
        # Non-staff user should be redirected
        self.client.login(username='sam_student', password='testpassword123')
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('items:index'))

        # Staff user can view
        self.user.is_staff = True
        self.user.save()
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrative Overview")
        self.assertContains(response, "Total Reports")

    def test_notifications_flow(self):
        from accounts.models import Notification
        notif = Notification.objects.create(
            recipient=self.user,
            title="Test Notice",
            message="Your claim was approved",
            notification_type="claim_approved"
        )
        self.client.login(username='sam_student', password='testpassword123')
        response = self.client.get(reverse('accounts:notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Notice")

        # Mark as read
        read_resp = self.client.get(reverse('accounts:mark_notification_read', args=[notif.pk]))
        self.assertEqual(read_resp.status_code, 302)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

