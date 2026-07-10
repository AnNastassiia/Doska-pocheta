# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0021_student_specialty_remove_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='parent_phone',
            field=models.CharField(blank=True, max_length=50, verbose_name='Телефон родителя (законного представителя)'),
        ),
        migrations.AddField(
            model_name='student',
            name='parent_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Электронная почта родителя (законного представителя)'),
        ),
        migrations.AddField(
            model_name='student',
            name='data_processing_consent_file',
            field=models.FileField(blank=True, null=True, upload_to='students/consents/', verbose_name='Подписанное согласие на обработку данных'),
        ),
        migrations.AddField(
            model_name='student',
            name='parent_consent_file',
            field=models.FileField(blank=True, null=True, upload_to='students/consents/parent/', verbose_name='Согласие законного представителя'),
        ),
        migrations.AlterField(
            model_name='student',
            name='data_processing_consent',
            field=models.BooleanField(default=False, verbose_name='Согласие на обработку данных (подтверждено файлом)'),
        ),
    ]
