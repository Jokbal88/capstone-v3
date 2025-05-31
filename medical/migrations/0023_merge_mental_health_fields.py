from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('medical', '0022_auto_20250530_1426'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL
            sql="""
                -- Drop the duplicate column if it exists
            CREATE TABLE IF NOT EXISTS medical_mentalhealthrecord_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NULL REFERENCES medical_patient(id) ON DELETE CASCADE,
                faculty_id INTEGER NULL UNIQUE REFERENCES main_faculty(id) ON DELETE CASCADE,
                is_availing_mental_health BOOLEAN NOT NULL DEFAULT 0,
                prescription VARCHAR(100) NULL,
                certification VARCHAR(100) NULL,
                date_submitted DATETIME NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                prescription_remarks TEXT NULL,
                certification_remarks TEXT NULL
            );
            
            INSERT INTO medical_mentalhealthrecord_new (
                id, patient_id, faculty_id, is_availing_mental_health,
                prescription, certification, date_submitted, status,
                prescription_remarks, certification_remarks
            )
            SELECT 
                id, patient_id, faculty_id,
                CASE 
                    WHEN service_availed_admin IS NOT NULL THEN service_availed_admin
                    ELSE is_availing_mental_health
                END,
                prescription, certification, date_submitted, status,
                prescription_remarks, certification_remarks
            FROM medical_mentalhealthrecord;
            
            DROP TABLE medical_mentalhealthrecord;
            ALTER TABLE medical_mentalhealthrecord_new RENAME TO medical_mentalhealthrecord;
            """,
            # Reverse SQL
            reverse_sql="""
            -- This is a one-way migration, no reverse SQL needed
            """
        ),
        migrations.AlterField(
            model_name='mentalhealthrecord',
            name='is_availing_mental_health',
            field=models.BooleanField(default=False, verbose_name='Is Availing Mental Health'),
        ),
    ] 