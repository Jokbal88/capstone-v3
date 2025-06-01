from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('medical', '0022_auto_20250530_1426'),
    ]

    operations = [
        # Mental Health Record table update
        migrations.RunSQL(
            sql="""
            -- Create new table with updated structure
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
            
            -- Copy data from old table to new table
            INSERT INTO medical_mentalhealthrecord_new (
                id, patient_id, faculty_id, is_availing_mental_health,
                prescription, certification, date_submitted, status,
                prescription_remarks, certification_remarks
            )
            SELECT 
                id, patient_id, faculty_id, is_availing_mental_health,
                prescription, certification, date_submitted, status,
                prescription_remarks, certification_remarks
            FROM medical_mentalhealthrecord;
            
            -- Drop old table and rename new table
            DROP TABLE medical_mentalhealthrecord;
            ALTER TABLE medical_mentalhealthrecord_new RENAME TO medical_mentalhealthrecord;
            """,
            reverse_sql="""
            -- This is a one-way migration, no reverse SQL needed
            """
        ),
        
        # Update MentalHealthRecord field
        migrations.AlterField(
            model_name='mentalhealthrecord',
            name='is_availing_mental_health',
            field=models.BooleanField(default=False, verbose_name='Is Availing Mental Health'),
        ),
        
        # Add PWD card remarks to MedicalRequirement if it doesn't exist
        migrations.RunSQL(
            sql="""
            -- Check if pwd_card_remarks column exists before adding it
            SELECT CASE 
                WHEN NOT EXISTS (
                    SELECT 1 
                    FROM pragma_table_info('medical_medicalrequirement') 
                    WHERE name='pwd_card_remarks'
                ) 
                THEN 'ALTER TABLE medical_medicalrequirement ADD COLUMN pwd_card_remarks TEXT NULL;'
                ELSE 'SELECT 1;'
            END;
            """,
            reverse_sql="""
            -- No reverse SQL needed
            """
        ),
        
        # Update DentalRecords date_appointed field
        migrations.AlterField(
            model_name='dentalrecords',
            name='date_appointed',
            field=models.DateTimeField(null=True),
        ),
    ] 