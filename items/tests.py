from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Item, Category, CampusLocation


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

    def test_report_item_requires_auth(self):
        response = self.client.get(reverse('items:create'))
        self.assertEqual(response.status_code, 302)

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
