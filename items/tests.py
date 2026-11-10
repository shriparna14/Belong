from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Item, Category, CampusLocation
from accounts.models import Notification
from claims.models import Claim


class ItemFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='student1', password='pass123', email='student1@campus.edu')
        self.category = Category.objects.create(name='Electronics', slug='electronics', icon='laptop')
        self.location = CampusLocation.objects.create(name='Library', building_code='LIB')

    def test_homepage_loads_and_displays_stats(self):
        response = self.client.get(reverse('items:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "belong.")
        self.assertContains(response, "Somewhere on campus, something is missing.")

    def test_returned_lost_report_is_labeled_returned(self):
        item = Item.objects.create(
            title='Returned lost textbook',
            item_type='lost',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Returned textbook',
            status='returned',
            reporter=self.user,
        )

        response = self.client.get(reverse('items:detail', args=[item.pk]))
        self.assertContains(response, 'Returned')
        self.assertNotContains(response, 'Lost item')

    def test_report_item_requires_auth(self):
        response = self.client.get(reverse('items:create'))
        self.assertEqual(response.status_code, 302)

    def test_campus_desk_requires_staff_or_desk_role(self):
        response = self.client.get(reverse('items:desk'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username='student1', password='pass123')
        response = self.client.get(reverse('items:desk'))
        self.assertRedirects(response, reverse('items:index'))

        self.user.profile.role = 'desk_admin'
        self.user.profile.save()
        response = self.client.get(reverse('items:desk'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lost &amp; Found Desk Console')

    def test_authenticated_user_can_report_item(self):
        self.client.login(username='student1', password='pass123')
        response = self.client.post(reverse('items:create'), {
            'item_type': 'found',
            'title': 'Keys on blue keychain',
            'category': self.category.id,
            'location': self.location.id,
            'specific_spot': 'Floor 1 lobby',
            'incident_date': timezone.now().date(),
            'description': 'Found silver keys with blue lanyard',
            'identifying_details': 'Has a tiny gym fob attached',
            'holding_location': 'Left with reception',
        })
        self.assertEqual(response.status_code, 302)
        item = Item.objects.filter(title='Keys on blue keychain').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.reporter, self.user)

    def test_found_report_notifies_matching_lost_reporter(self):
        lost_owner = User.objects.create_user(
            username='lost_owner',
            password='pass123',
            email='owner@campus.edu',
        )
        Item.objects.create(
            title='Lost phone',
            item_type='lost',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Black phone',
            reporter=lost_owner,
        )

        self.client.login(username='student1', password='pass123')
        response = self.client.post(reverse('items:create'), {
            'item_type': 'found',
            'title': 'Found iPhone',
            'category': self.category.id,
            'location': self.location.id,
            'incident_date': timezone.now().date(),
            'description': 'Black iPhone found near the library',
            'holding_location': 'Library desk',
        })

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(recipient=lost_owner)
        self.assertEqual(notification.notification_type, 'matching_found_report')
        self.assertIn('Found iPhone', notification.message)
        self.assertEqual(
            notification.link,
            reverse('items:detail', args=[Item.objects.get(title='Found iPhone').pk]),
        )

    def test_lost_to_found_to_claim_flow_between_two_users(self):
        lost_owner = User.objects.create_user(
            username='lost_owner_flow',
            password='pass123',
            email='owner-flow@campus.edu',
        )
        finder = User.objects.create_user(
            username='finder_flow',
            password='pass123',
            email='finder-flow@campus.edu',
        )
        lost_item = Item.objects.create(
            title='Lost iPhone 15',
            item_type='lost',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Black iPhone 15 with a blue case',
            identifying_details='Unique scratch beside the camera',
            reporter=lost_owner,
        )

        self.client.login(username='finder_flow', password='pass123')
        found_response = self.client.post(reverse('items:create'), {
            'item_type': 'found',
            'title': 'Found iPhone 15',
            'category': self.category.id,
            'location': self.location.id,
            'incident_date': timezone.now().date(),
            'description': 'Black iPhone found near the library',
            'identifying_details': 'Scratch beside the camera',
            'holding_location': 'Library desk',
        })
        self.assertEqual(found_response.status_code, 302)
        found_item = Item.objects.get(title='Found iPhone 15')
        self.assertTrue(
            Notification.objects.filter(
                recipient=lost_owner,
                notification_type='matching_found_report',
                link=reverse('items:detail', args=[found_item.pk]),
            ).exists()
        )

        self.client.login(username='lost_owner_flow', password='pass123')
        claim_response = self.client.post(
            reverse('claims:create', args=[found_item.pk]),
            {'description': 'The camera scratch matches my phone.'},
        )
        self.assertEqual(claim_response.status_code, 302)
        claim = Claim.objects.get(item=found_item, claimant=lost_owner)
        self.assertEqual(claim.status, 'pending')
        self.assertEqual(Item.objects.get(pk=lost_item.pk).status, 'active')

        self.client.login(username='finder_flow', password='pass123')
        review_response = self.client.post(
            reverse('claims:review', args=[claim.pk]),
            {'action': 'approve', 'review_notes': 'Evidence matches.'},
        )
        self.assertEqual(review_response.status_code, 302)
        claim.refresh_from_db()
        found_item.refresh_from_db()
        self.assertEqual(claim.status, 'approved')
        self.assertEqual(found_item.status, 'handoff_ready')

    def test_other_user_cannot_edit_or_delete_report(self):
        owner = User.objects.create_user(username='owner', password='pass123')
        item = Item.objects.create(
            title='Owner item',
            item_type='lost',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Private report',
            reporter=owner,
        )
        self.client.login(username='student1', password='pass123')

        edit_response = self.client.get(reverse('items:edit', args=[item.pk]))
        delete_response = self.client.get(reverse('items:delete', args=[item.pk]))

        self.assertRedirects(edit_response, reverse('items:detail', args=[item.pk]))
        self.assertRedirects(delete_response, reverse('items:detail', args=[item.pk]))
        self.assertTrue(Item.objects.filter(pk=item.pk).exists())

    def test_item_aging_calculation(self):
        old_item = Item.objects.create(
            title='Old Notebook',
            item_type='found',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Unclaimed notebook',
            reporter=self.user,
        )
        # Force created_at to 35 days ago
        Item.objects.filter(pk=old_item.pk).update(created_at=timezone.now() - timedelta(days=35))
        old_item.refresh_from_db()
        self.assertTrue(old_item.is_aged)
    def test_search_by_keyword_category_and_location(self):
        item1 = Item.objects.create(
            title='Black Lenovo ThinkPad Laptop',
            item_type='lost',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Lost in computer lab area',
            reporter=self.user,
        )
        other_loc = CampusLocation.objects.create(name='Student Center', building_code='SC')
        item2 = Item.objects.create(
            title='Red Hydro Flask Bottle',
            item_type='found',
            category=Category.objects.create(name='Bottles', slug='bottles'),
            location=other_loc,
            incident_date=timezone.now().date(),
            description='Left on cafeteria table',
            reporter=self.user,
        )

        resp = self.client.get(reverse('items:index'), {'q': 'Lenovo'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ThinkPad')
        self.assertNotContains(resp, 'Hydro Flask')

        resp_cat = self.client.get(reverse('items:index'), {'category': 'electronics'})
        self.assertContains(resp_cat, 'ThinkPad')
        self.assertNotContains(resp_cat, 'Hydro Flask')

        resp_loc = self.client.get(reverse('items:index'), {'location': other_loc.id})
        self.assertContains(resp_loc, 'Hydro Flask')
        self.assertNotContains(resp_loc, 'ThinkPad')

    def test_search_date_range_and_pagination_preserve_filters(self):
        for index in range(10):
            item = Item.objects.create(
                title=f'Library report {index}',
                item_type='lost',
                category=self.category,
                location=self.location,
                incident_date=timezone.now().date() - timedelta(days=index),
                description='Reported near the library',
                reporter=self.user,
            )
            Item.objects.filter(pk=item.pk).update(
                created_at=timezone.now() - timedelta(days=index)
            )

        response = self.client.get(reverse('items:index'), {
            'type': 'lost',
            'location': self.location.id,
            'date_from': (timezone.now().date() - timedelta(days=9)).isoformat(),
            'date_to': timezone.now().date().isoformat(),
            'sort': 'oldest',
            'page': 2,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Library report')
        self.assertContains(response, 'page=1')
        self.assertContains(response, f'location={self.location.id}')
        self.assertContains(response, 'date_from=')
        self.assertContains(response, 'date_to=')
        self.assertContains(response, 'sort=oldest')

    def test_matching_suggestions_and_privacy_of_sensitive_info(self):
        lost_item = Item.objects.create(
            title='Blue Leather Wallet',
            item_type='lost',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Lost near reception desk',
            identifying_details='Driver license inside with ID number 987654321',
            reporter=self.user,
        )
        other_user = User.objects.create_user(username='finder2', password='pass123')
        found_item = Item.objects.create(
            title='Dark Navy Wallet',
            item_type='found',
            category=self.category,
            location=self.location,
            incident_date=timezone.now().date(),
            description='Found on 1st floor desk',
            identifying_details='Has photo of a golden retriever in inner slot',
            reporter=other_user,
        )

        # Unauthenticated user: private details hidden, suggestions present
        resp = self.client.get(reverse('items:detail', args=[found_item.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dark Navy Wallet')
        self.assertNotContains(resp, 'Has photo of a golden retriever in inner slot')
        self.assertContains(resp, 'Blue Leather Wallet')

        # Owner logged in: private details visible
        self.client.login(username='finder2', password='pass123')
        resp_owner = self.client.get(reverse('items:detail', args=[found_item.pk]))
        self.assertContains(resp_owner, 'Has photo of a golden retriever in inner slot')
