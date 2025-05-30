from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('medical', '0022_auto_20250530_1426'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='medical_mentalhealthrecord' 
                    AND column_name='is_availing_mental_health'
                ) THEN
                    ALTER TABLE medical_mentalhealthrecord 
                    RENAME COLUMN service_availed_admin TO is_availing_mental_health;
                END IF;
            END $$;
            """,
            # Reverse SQL
            reverse_sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='medical_mentalhealthrecord' 
                    AND column_name='is_availing_mental_health'
                ) THEN
                    ALTER TABLE medical_mentalhealthrecord 
                    RENAME COLUMN is_availing_mental_health TO service_availed_admin;
                END IF;
            END $$;
            """
        ),
    ] 