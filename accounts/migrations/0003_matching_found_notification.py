from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('claim_submitted', 'Claim Submitted'),
                    ('matching_found_report', 'Matching Found Report'),
                    ('claim_approved', 'Claim Approved'),
                    ('claim_rejected', 'Claim Rejected'),
                    ('item_returned', 'Item Returned'),
                    ('info', 'Information'),
                ],
                default='info',
                max_length=30,
            ),
        ),
    ]
