from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from items.models import Category, CampusLocation, Item
from claims.models import Claim, HandoffOTP, HandoffAuditLog


class Command(BaseCommand):
    help = 'Populates the Belong database with campus categories, locations, users, and realistic lost/found listings.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding campus lost & found demo data...")

        # 1. Create Categories
        categories_data = [
            ('Electronics', 'electronics', 'laptop', 'Laptops, chargers, headphones, calculators, phones'),
            ('Keys & Access Cards', 'keys', 'key', 'Room keys, car keys, fobs, keychains'),
            ('Wallets & Bags', 'wallets-bags', 'wallet', 'Backpacks, totes, wallets, purses, pouches'),
            ('Student IDs & Cards', 'ids-cards', 'id-card', 'Campus cards, driving licenses, credit cards'),
            ('Clothing & Gear', 'clothing', 'shirt', 'Jackets, hoodies, caps, umbrellas, scarves'),
            ('Books & Stationery', 'books', 'book', 'Notebooks, textbooks, pencil cases, binders'),
            ('Eyewear & Accessories', 'eyewear', 'glasses', 'Spectacles, sunglasses, watches, rings'),
            ('Other Items', 'other', 'box', 'Water bottles, sporting equipment, miscellaneous items'),
        ]

        cat_objs = {}
        for name, slug, icon, desc in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon, 'description': desc}
            )
            cat_objs[slug] = cat

        # 2. Create Campus Locations
        locations_data = [
            ('Main University Library', 'LIB', 'Floors 1-4, silent study, computer lab, café'),
            ('Student Union Center', 'SUC', 'Food court, student lounge, club rooms, game hall'),
            ('Science & Technology Hall', 'STH', 'Physics labs, computer science department, lecture halls'),
            ('Engineering Block A', 'ENG-A', 'Robotics lab, maker space, auditorium'),
            ('Campus Sports Complex & Gym', 'GYM', 'Indoor basketball court, gym, swimming pool lockers'),
            ('Central Campus Quad', 'QUAD', 'Benches, outdoor lawn, clock tower vicinity'),
            ('Central Security & Lost Desk', 'SEC-102', 'Main gate campus security building, Room 102'),
        ]

        loc_objs = {}
        for name, code, desc in locations_data:
            loc, _ = CampusLocation.objects.get_or_create(
                name=name,
                defaults={'building_code': code, 'description': desc}
            )
            loc_objs[code] = loc

        # 3. Create Demo Users
        # Admin / Desk officer
        admin_user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@campus.edu',
            'first_name': 'Desk',
            'last_name': 'Officer',
            'is_staff': True,
            'is_superuser': True,
        })
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            admin_user.profile.role = 'desk_admin'
            admin_user.profile.campus_id = 'STAFF-001'
            admin_user.profile.department = 'Campus Safety & Desk Services'
            admin_user.profile.save()

        # Student Alex
        alex, created = User.objects.get_or_create(username='alex_rivera', defaults={
            'email': 'alex.rivera@campus.edu',
            'first_name': 'Alex',
            'last_name': 'Rivera',
        })
        if created:
            alex.set_password('password123')
            alex.save()
            alex.profile.role = 'student'
            alex.profile.campus_id = 'STU-2024-9102'
            alex.profile.department = 'Computer Science'
            alex.profile.phone_number = '+1 (555) 349-2011'
            alex.profile.save()

        # Student Sarah
        sarah, created = User.objects.get_or_create(username='sarah_chen', defaults={
            'email': 'sarah.chen@campus.edu',
            'first_name': 'Sarah',
            'last_name': 'Chen',
        })
        if created:
            sarah.set_password('password123')
            sarah.save()
            sarah.profile.role = 'student'
            sarah.profile.campus_id = 'STU-2023-8419'
            sarah.profile.department = 'Mechanical Engineering'
            sarah.profile.phone_number = '+1 (555) 882-9401'
            sarah.profile.save()

        # Student Jordan
        jordan, created = User.objects.get_or_create(username='jordan_lee', defaults={
            'email': 'jordan.lee@campus.edu',
            'first_name': 'Jordan',
            'last_name': 'Lee',
        })
        if created:
            jordan.set_password('password123')
            jordan.save()
            jordan.profile.role = 'student'
            jordan.profile.campus_id = 'STU-2025-1104'
            jordan.profile.department = 'Economics'
            jordan.profile.save()

        now = timezone.now()

        # 4. Create Sample Items
        # Item 1: Found MacBook Charger (Fresh)
        i1, _ = Item.objects.get_or_create(
            title="67W USB-C Apple MacBook Power Adapter & Braided Cable",
            defaults={
                'item_type': 'found',
                'category': cat_objs['electronics'],
                'location': loc_objs['LIB'],
                'specific_spot': 'Floor 2, silent cubicle row C near power socket #14',
                'incident_date': (now - timedelta(days=1)).date(),
                'description': 'Found a white Apple 67W power brick with an authentic braided USB-C cable left plugged into the desk socket.',
                'identifying_details': 'There is a small purple dot sticker on the side of the power brick.',
                'status': 'active',
                'reporter': sarah,
                'holding_location': 'Left with Library 1st Floor Reception',
            }
        )

        # Item 2: Found Hydro Flask (With Active Approved Claim & OTP demonstration)
        i2, _ = Item.objects.get_or_create(
            title="Matte Navy Blue Hydro Flask Water Bottle (32 oz)",
            defaults={
                'item_type': 'found',
                'category': cat_objs['other'],
                'location': loc_objs['GYM'],
                'specific_spot': 'Bench next to Court 2',
                'incident_date': (now - timedelta(days=2)).date(),
                'description': 'Navy blue 32 oz Hydro Flask with straw lid. Clean condition with multiple waterproof stickers.',
                'identifying_details': 'Stickers include: NASA Meatball logo, GitHub Octocat, and Yosemite National Park.',
                'status': 'handoff_ready',
                'reporter': sarah,
                'holding_location': 'Finder in possession (Sarah Chen)',
            }
        )

        # Create Claim and OTP for Item 2
        claim2, created = Claim.objects.get_or_create(
            item=i2,
            claimant=alex,
            defaults={
                'description': 'This is my water bottle! It has a Yosemite park sticker and a GitHub Octocat on the back. Inside the cap there is a minor dent from dropping it last semester.',
                'status': 'approved',
                'review_notes': 'Sticker descriptions match 100%. Approved for pickup.',
                'reviewed_by': sarah,
                'reviewed_at': now - timedelta(hours=3),
            }
        )
        if created:
            HandoffOTP.objects.create(
                claim=claim2,
                otp_code='482915',
                expires_at=now + timedelta(minutes=15),
                is_used=False
            )

        # Item 3: Lost Sony Headphones
        i3, _ = Item.objects.get_or_create(
            title="Sony WH-1000XM4 Wireless Over-Ear Headphones (Black)",
            defaults={
                'item_type': 'lost',
                'category': cat_objs['electronics'],
                'location': loc_objs['SUC'],
                'specific_spot': 'Food Court booth near Asian Express',
                'incident_date': (now - timedelta(days=3)).date(),
                'description': 'Black over-ear Sony noise-canceling headphones in their grey zippered carrying case. Left on table during lunch.',
                'identifying_details': 'Device Bluetooth name was set to "Alex\'s XM4". Case contains a short aux cable and airline dual-pin adapter.',
                'status': 'active',
                'reporter': alex,
                'holding_location': 'Seeking information',
            }
        )

        # Item 4: Found Student ID Card
        i4, _ = Item.objects.get_or_create(
            title="Official Campus Student Smart ID Card",
            defaults={
                'item_type': 'found',
                'category': cat_objs['ids-cards'],
                'location': loc_objs['QUAD'],
                'specific_spot': 'Fell near bike rack on East pathway',
                'incident_date': (now - timedelta(days=2)).date(),
                'description': 'Student RFID smartcard found on the pathway grass after classes.',
                'identifying_details': 'Belongs to a student with initial J. Department of Economics.',
                'status': 'active',
                'reporter': alex,
                'holding_location': 'Delivered to Central Security Room 102',
            }
        )

        # Item 5: Aged Item (>35 days old) for Campus Desk Aging Audit Demo
        aged_date = now - timedelta(days=36)
        i5, _ = Item.objects.get_or_create(
            title="Vintage Brown Leather Fossil Trifold Wallet",
            defaults={
                'item_type': 'found',
                'category': cat_objs['wallets-bags'],
                'location': loc_objs['ENG-A'],
                'specific_spot': 'Auditorium 101, back row under seat 44',
                'incident_date': aged_date.date(),
                'description': 'Brown leather wallet found during end-of-month auditorium cleanout.',
                'identifying_details': 'Contains a Starbucks gift card with $5 balance and loyalty stamp card.',
                'status': 'active',
                'reporter': admin_user,
                'holding_location': 'Central Lost & Found Storage Locker #12',
            }
        )
        # Force created_at to 36 days ago so aging logic triggers
        Item.objects.filter(pk=i5.pk).update(created_at=aged_date)

        # Item 6: Reunited / Returned Item Demo
        i6, _ = Item.objects.get_or_create(
            title="Silver iPad Air 5th Gen (64GB, Blue Folio Smart Case)",
            defaults={
                'item_type': 'found',
                'category': cat_objs['electronics'],
                'location': loc_objs['STH'],
                'specific_spot': 'Computer lab 302, workstation 8',
                'incident_date': (now - timedelta(days=5)).date(),
                'description': 'Silver iPad left next to workstation monitor.',
                'identifying_details': 'Lock screen has photo of golden retriever named Bailey.',
                'status': 'returned',
                'reporter': admin_user,
                'holding_location': 'Successfully returned to owner',
            }
        )

        claim6, _ = Claim.objects.get_or_create(
            item=i6,
            claimant=jordan,
            defaults={
                'description': 'Lock screen wallpaper is my golden retriever dog Bailey. iPad serial ends in 992.',
                'status': 'completed',
                'review_notes': 'Verified lockscreen image and unlocked with passcode.',
                'reviewed_by': admin_user,
                'reviewed_at': now - timedelta(days=4),
            }
        )

        HandoffAuditLog.objects.get_or_create(
            item=i6,
            claim=claim6,
            defaults={
                'returned_to': jordan,
                'confirmed_by': admin_user,
                'notes': 'Verified ownership in person via 6-digit OTP and passcode unlocking.'
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Successfully seeded demo categories, locations, users, and listings!"))
        self.stdout.write(self.style.NOTICE("Demo credentials:"))
        self.stdout.write("  Admin / Desk: username='admin', password='admin123'")
        self.stdout.write("  Claimant:     username='alex_rivera', password='password123'")
        self.stdout.write("  Finder:       username='sarah_chen', password='password123'")
