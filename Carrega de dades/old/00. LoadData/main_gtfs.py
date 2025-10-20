"""
Main script to load GTFS data into PostgreSQL

This script loads GTFS CSV files into a PostgreSQL database 
using predefined configuration settings.

Usage:
    python main_gtfs.py

Author: Generated for ATM GTFS data loading
Date: 2025-09-22
"""

import sys
from pathlib import Path
from gtfs_to_postgresql import GTFSLoader

# Configuration constants
DB_CONNECTION_STRING = "postgresql://atm:atm@192.168.1.251:5432/gisdb"
DATA_DIRECTORY = "../Data 241212 - GTFS - xarxa"
SCHEMA_NAME = "atm"


def list_gtfs_files(data_directory: str):
    """List available GTFS files in the data directory."""
    data_path = Path(data_directory)
    
    if not data_path.exists():
        print(f"❌ Data directory does not exist: {data_directory}")
        return
    
    gtfs_files = [
        'calendar.txt', 'calendar_dates.txt', 'trips.txt', 'stop_times.txt',
        'frequencies.txt', 'routes.txt', 'stops.txt', 'shapes.txt',
        'agency.txt', 'transfers.txt'
    ]
    
    print(f"📁 Data directory: {data_path.absolute()}")
    print("📋 GTFS files status:")
    
    for filename in gtfs_files:
        file_path = data_path / filename
        if file_path.exists():
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"  ✅ {filename} ({size_mb:.2f} MB)")
        else:
            print(f"  ❌ {filename} (not found)")


def main():
    """Main execution function."""
    print("🚀 GTFS to PostgreSQL Loader")
    print("=" * 40)
    print(f"📁 Data directory: {DATA_DIRECTORY}")
    print(f"🗄️  Database schema: {SCHEMA_NAME}")
    print()
    
    # List available files first
    list_gtfs_files(DATA_DIRECTORY)
    print()
    
    # Initialize the loader
    try:
        loader = GTFSLoader(
            db_connection_string=DB_CONNECTION_STRING,
            data_directory=DATA_DIRECTORY,
            schema_name=SCHEMA_NAME
        )
    except Exception as e:
        print(f"❌ Error initializing loader: {e}")
        return 1
    
    try:
        # Check data directory
        if not loader.check_data_directory():
            print("❌ Data directory validation failed")
            return 1
        
        # Connect to database
        print("🔌 Connecting to database...")
        if not loader.connect_to_database():
            print("❌ Database connection failed")
            return 1
        
        # Load all files
        print("📚 Loading all GTFS files...")
        print("📍 Note: stops.txt will include geospatial processing (EPSG:25831)")
        results = loader.load_all_files()
        
        # Print summary
        print("\n📊 Loading Results:")
        print("-" * 30)
        
        for filename, success in results.items():
            status = "✅" if success else "❌"
            if filename == 'stops.txt' and success:
                print(f"  {status} {filename} (with geospatial processing)")
            else:
                print(f"  {status} {filename}")
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\n📈 Summary: {successful}/{total} files loaded successfully")
        
        if successful == total:
            print("🎉 All files loaded successfully!")
            return 0
        else:
            print("⚠️ Some files failed to load. Check the logs above.")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        # Always close the connection
        loader.close_connection()


if __name__ == "__main__":
    sys.exit(main())
