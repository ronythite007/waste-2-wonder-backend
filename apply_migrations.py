import os
import psycopg2
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def apply_migrations():
    """Apply all migrations in order"""
    try:
        # Get database connection details from environment variables
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Connect to the database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Create migrations table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applied_migrations (
                migration_name text PRIMARY KEY,
                applied_at timestamptz DEFAULT now()
            );
        """)
        conn.commit()

        # Get list of migration files
        migrations_dir = os.path.join('supabase', 'migrations')
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])

        # Get already applied migrations
        cur.execute("SELECT migration_name FROM applied_migrations;")
        applied = {row[0] for row in cur.fetchall()}

        # Apply new migrations
        for migration_file in migration_files:
            if migration_file not in applied:
                logger.info(f"Applying migration: {migration_file}")
                
                # Read migration file
                with open(os.path.join(migrations_dir, migration_file), 'r') as f:
                    migration_sql = f.read()

                # Execute the entire migration file
                try:
                    cur.execute(migration_sql)
                    conn.commit()  # Commit the migration
                except psycopg2.errors.DuplicateObject as e:
                    logger.warning(f"Skipping duplicate object in {migration_file}: {str(e)}")
                    conn.rollback()  # Rollback on duplicate object
                except Exception as e:
                    logger.error(f"Error executing migration {migration_file}: {str(e)}")
                    conn.rollback()  # Rollback on other errors
                    raise

                # Record migration as applied
                try:
                    cur.execute(
                        "INSERT INTO applied_migrations (migration_name) VALUES (%s);",
                        (migration_file,)
                    )
                    conn.commit()
                    logger.info(f"Successfully applied migration: {migration_file}")
                except psycopg2.errors.UniqueViolation:
                    logger.warning(f"Migration {migration_file} was already marked as applied")
                    conn.rollback()

        logger.info("All migrations completed successfully")

    except Exception as e:
        logger.error(f"Error applying migrations: {str(e)}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    apply_migrations()