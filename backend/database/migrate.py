"""
Database migration script
Creates all necessary tables in PostgreSQL
Run this once to set up the database schema
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import services
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import db


async def run_migration():
    """Run database migration to create all tables"""
    try:
        # Connect to database
        print("[*] Connecting to database...")
        await db.connect()
        
        # Read schema.sql file
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            print(f"[ERROR] Schema file not found: {schema_file}")
            return
        
        print(f"[*] Reading schema from: {schema_file}")
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema (split by semicolons for multiple statements)
        # asyncpg.execute can handle multiple statements
        print("[*] Creating tables...")
        await db.execute(schema_sql)
        
        print("[SUCCESS] Migration completed successfully!")
        
        # Verify tables were created
        print("\n[*] Verifying tables...")
        tables = await db.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"[SUCCESS] Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("MeetMap Database Migration")
    print("=" * 50)
    asyncio.run(run_migration())

