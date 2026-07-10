from django.db import migrations


STATUS_MAP = {
    'pending_student': 'pending_manager',
    'approved_by_student': 'approved_by_manager',
    'rejected_by_student': 'rejected_by_manager',
}


def migrate_contact_request_statuses(apps, schema_editor):
    ContactRequest = apps.get_model('portfolio', 'ContactRequest')
    for old_status, new_status in STATUS_MAP.items():
        ContactRequest.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0023_remove_contactrequest_responded_at_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_contact_request_statuses, migrations.RunPython.noop),
    ]
