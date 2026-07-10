# Generated manually

from django.db import migrations, models


def copy_group_specialty_to_student(apps, schema_editor):
    Student = apps.get_model('portfolio', 'Student')
    for student in Student.objects.select_related('group').iterator():
        group = getattr(student, 'group', None)
        if group and group.specialty:
            student.specialty = group.specialty
            student.save(update_fields=['specialty'])


def copy_target_groups_to_specialties(apps, schema_editor):
    Vacancy = apps.get_model('portfolio', 'Vacancy')
    for vacancy in Vacancy.objects.all():
        specialties = []
        for group in vacancy.target_groups.all():
            name = (group.specialty or '').strip()
            if name and name not in specialties:
                specialties.append(name)
        vacancy.target_specialties = ','.join(specialties)
        vacancy.save(update_fields=['target_specialties'])


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0020_group_remove_student_course_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='specialty',
            field=models.CharField(blank=True, max_length=200, verbose_name='Специальность обучения'),
        ),
        migrations.RunPython(copy_group_specialty_to_student, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='group',
        ),
        migrations.AddField(
            model_name='vacancy',
            name='target_specialties',
            field=models.TextField(blank=True, verbose_name='Целевые специальности'),
        ),
        migrations.RunPython(copy_target_groups_to_specialties, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='vacancy',
            name='target_groups',
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='send_notifications',
            field=models.BooleanField(
                default=False,
                verbose_name='Отправить уведомления участникам с выбранными специальностями',
            ),
        ),
        migrations.DeleteModel(
            name='Group',
        ),
    ]
