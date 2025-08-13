#!/usr/bin/env python3
"""
Database migration script to add youtube_video_id column to webinar_settings table
"""

import psycopg2
import sys
from urllib.parse import urlparse

def connect_to_db(connection_string):
    """Parse connection string and establish database connection"""
    try:
        # Parse the connection string
        parsed = urlparse(connection_string)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading '/'
            user=parsed.username,
            password=parsed.password
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def execute_migration(conn):
    """Execute the migration SQL commands"""
    try:
        cursor = conn.cursor()
        
        print("🚀 Starting database migration...")
        
        # Step 1: Add the new column
        print("📝 Adding youtube_video_id column...")
        cursor.execute("""
            ALTER TABLE webinar_settings 
            ADD COLUMN IF NOT EXISTS youtube_video_id VARCHAR(32);
        """)
        
        # Step 2: Update existing rows with default value
        print("🔄 Setting default value for existing rows...")
        cursor.execute("""
            UPDATE webinar_settings 
            SET youtube_video_id = 'GXRL7PcPbOA' 
            WHERE youtube_video_id IS NULL;
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("""
            SELECT COUNT(*) as total_rows, 
                   COUNT(youtube_video_id) as rows_with_video_id
            FROM webinar_settings;
        """)
        
        result = cursor.fetchone()
        total_rows, rows_with_video_id = result
        
        print("✅ Migration completed successfully!")
        print(f"📊 Total rows: {total_rows}")
        print(f"📺 Rows with youtube_video_id: {rows_with_video_id}")
        
        cursor.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error during migration: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        conn.rollback()
        return False
    
    return True

def main():
    # Database connection string
    CONNECTION_STRING = "postgresql://postgres:bHaJHoNZuiNzjhOMRkiCwlsgvxsHyUxM@yamabiko.proxy.rlwy.net:37305/railway"
    
    print("🔧 Webinar Settings Migration Tool")
    print("=" * 40)
    
    # Connect to database
    conn = connect_to_db(CONNECTION_STRING)
    if not conn:
        sys.exit(1)
    
    # Execute migration
    success = execute_migration(conn)
    
    # Close connection
    conn.close()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Your webinar_settings table now has the youtube_video_id column.")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()