from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from items.models import Item, Category, CampusLocation
from claims.models import Claim, HandoffOTP, HandoffAuditLog


class ClaimsAndOTPEndToEndTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.finder = User.objects.create_user(username='finder_jane', password='pass123', email='jane@campus.edu')
        self.claimant = User.objects.create_user(username='owner_bob', password='pass123', email='bob@campus.edu')
        
        self.cat = Category.objects.create(name='Electronics', slug='electronics', icon='laptop')
        self.loc = CampusLocation.objects.create(name='Main Hall', building_code='MH')

        self.item = Item.objects.create(
            title='AirPods Pro Case',
            item_type='found',
            category=self.cat,
            location=self.loc,
            incident_date=timezone.now().date(),
            description='White AirPods charging case',
            identifying_details='Serial ends in 771',
            status='active',
            reporter=self.finder,
            holding_location='With Finder',
        )

    def test_claim_submission_and_otp_verification_workflow(self):
        # 1. Claimant logs in and submits a claim
        self.client.login(username='owner_bob', password='pass123')
        response = self.client.post(reverse('claims:create', args=[self.item.id]), {
            'description': 'These are my AirPods! Serial ends in 771, engraved with "Bob".'
        })
        self.assertEqual(response.status_code, 302)
        
        claim = Claim.objects.filter(item=self.item, claimant=self.claimant).first()
        self.assertIsNotNone(claim)
        self.assertEqual(claim.status, 'pending')

        # Item status becomes claim_pending
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'claim_pending')

        # 2. Finder logs in and reviews/approves the claim
        self.client.login(username='finder_jane', password='pass123')
        response = self.client.post(reverse('claims:review', args=[claim.id]), {
            'action': 'approve',
            'review_notes': 'Engraving and serial matches. Come pick up at library.'
        })
        self.assertEqual(response.status_code, 302)

        claim.refresh_from_db()
        self.assertEqual(claim.status, 'approved')
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'handoff_ready')

        # Verify OTP was generated
        otp = getattr(claim, 'handoff_otp', None)
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.otp_code), 6)
        self.assertTrue(otp.is_valid)

        # 3. Finder verifies OTP upon physical handoff
        response = self.client.post(reverse('claims:verify_otp', args=[claim.id]), {
            'otp_code': otp.otp_code,
            'notes': 'Verified student card in person.'
        })
        self.assertEqual(response.status_code, 302)

        # Confirm completed state
        otp.refresh_from_db()
        claim.refresh_from_db()
        self.item.refresh_from_db()

        self.assertTrue(otp.is_used)
        self.assertEqual(claim.status, 'completed')
        self.assertEqual(self.item.status, 'returned')

        # Confirm audit log created
        log = HandoffAuditLog.objects.filter(claim=claim).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.returned_to, self.claimant)
        self.assertEqual(log.confirmed_by, self.finder)
