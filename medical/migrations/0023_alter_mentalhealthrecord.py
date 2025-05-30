from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('medical', '0022_auto_20250530_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mentalhealthrecord',
            name='service_availed_admin',
            field=models.BooleanField(default=False, verbose_name='Is Availing Mental Health'),
        ),
    ] 