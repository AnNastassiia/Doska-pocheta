from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0018_employer_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employer',
            name='sector',
            field=models.CharField(max_length=255, verbose_name='Сфера деятельности'),
        ),
        migrations.RemoveField(
            model_name='vacancy',
            name='tech_stack',
        ),
    ]
