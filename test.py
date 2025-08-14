#!/usr/bin/env python3
"""
Database migration script to add youtube_video_id, start_time, and end_time columns to webinar_settings and majlis_webinar_settings tables
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
        
        # Step 1: Add columns to webinar_settings table
        print("📝 Adding columns to webinar_settings table...")
        cursor.execute("""
            ALTER TABLE webinar_settings 
            ADD COLUMN IF NOT EXISTS youtube_video_id VARCHAR(32),
            ADD COLUMN IF NOT EXISTS start_time TIMESTAMP,
            ADD COLUMN IF NOT EXISTS end_time TIMESTAMP;
        """)
        
        # Step 2: Add columns to majlis_webinar_settings table
        print("📝 Adding columns to majlis_webinar_settings table...")
        cursor.execute("""
            ALTER TABLE majlis_webinar_settings 
            ADD COLUMN IF NOT EXISTS start_time TIMESTAMP,
            ADD COLUMN IF NOT EXISTS end_time TIMESTAMP;
        """)
        
        # Step 3: Update existing rows with default values
        print("🔄 Setting default values for existing rows...")
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
                   COUNT(youtube_video_id) as rows_with_video_id,
                   COUNT(start_time) as rows_with_start_time,
                   COUNT(end_time) as rows_with_end_time
            FROM webinar_settings;
        """)
        
        result = cursor.fetchone()
        total_rows, rows_with_video_id, rows_with_start_time, rows_with_end_time = result
        
        cursor.execute("""
            SELECT COUNT(*) as total_rows,
                   COUNT(start_time) as rows_with_start_time,
                   COUNT(end_time) as rows_with_end_time
            FROM majlis_webinar_settings;
        """)
        
        majlis_result = cursor.fetchone()
        majlis_total_rows, majlis_rows_with_start_time, majlis_rows_with_end_time = majlis_result
        
        print("✅ Migration completed successfully!")
        print(f"📊 WebinarSettings - Total rows: {total_rows}")
        print(f"📺 WebinarSettings - Rows with youtube_video_id: {rows_with_video_id}")
        print(f"⏰ WebinarSettings - Rows with start_time: {rows_with_start_time}")
        print(f"⏰ WebinarSettings - Rows with end_time: {rows_with_end_time}")
        print(f"📊 MajlisWebinarSettings - Total rows: {majlis_total_rows}")
        print(f"⏰ MajlisWebinarSettings - Rows with start_time: {majlis_rows_with_start_time}")
        print(f"⏰ MajlisWebinarSettings - Rows with end_time: {majlis_rows_with_end_time}")
        
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
    print("Adding youtube_video_id, start_time, and end_time columns")
    print("=" * 50)
    
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
        print("Your webinar_settings and majlis_webinar_settings tables now have the new columns:")
        print("• youtube_video_id (webinar_settings only)")
        print("• start_time (both tables)")
        print("• end_time (both tables)")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()