"""
GTFS to PostgreSQL Loader

This module provides functionality to load GTFS (General Transit Feed Specification) 
CSV files into a PostgreSQL database with proper error handling and validation.

Author: Generated for ATM GTFS data loading
Date: 2025-09-22
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Optional, Dict, Any
from pathlib import Path


class GTFSLoader:
    """
    A class to handle loading GTFS CSV files into PostgreSQL database.
    """
    
    def __init__(self, 
                 db_connection_string: str = "postgresql://atm:gisdb@192.168.1.251:5432/atm",
                 data_directory: str = "../Data 241212 - GTFS - xarxa",
                 schema_name: str = "atm"):
        """
        Initialize the GTFS Loader.
        
        Args:
            db_connection_string: PostgreSQL connection string
            data_directory: Directory containing GTFS CSV files
            schema_name: PostgreSQL schema name to use
        """
        self.db_connection_string = db_connection_string
        self.data_directory = Path(data_directory)
        self.schema_name = schema_name
        self.engine = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # GTFS file mapping: filename -> (table_name, description)
        self.gtfs_files = {
            'calendar.txt': ('cal', 'Calendar service definitions'),
            'calendar_dates.txt': ('cal_d', 'Calendar date exceptions'),
            'trips.txt': ('tri', 'Trip definitions'),
            'stop_times.txt': ('sto_t', 'Stop times for each trip'),
            'frequencies.txt': ('fre', 'Frequency-based service definitions'),
            'routes.txt': ('rou', 'Route definitions'),
            'stops.txt': ('sto', 'Stop definitions'),
            'shapes.txt': ('sho', 'Shape definitions for routes'),
            'agency.txt': ('age', 'Transit agency information'),
            'transfers.txt': ('tra', 'Transfer definitions between stops')
        }
    
    def connect_to_database(self) -> bool:
        """
        Establish connection to PostgreSQL database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.engine = create_engine(self.db_connection_string)
            # Test the connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info("Successfully connected to PostgreSQL database")
            
            # Check for PostGIS extension
            self._check_postgis_extension()
            
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False
    
    def _check_postgis_extension(self):
        """Check if PostGIS extension is available."""
        if self.engine is None:
            return
            
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM pg_extension WHERE extname='postgis'"))
                postgis_count = result.scalar()
                
                if postgis_count and postgis_count > 0:
                    self.logger.info("PostGIS extension is available")
                else:
                    self.logger.warning("PostGIS extension not found. Geospatial functionality may not work.")
                    self.logger.info("To enable PostGIS, run: CREATE EXTENSION postgis;")
        except Exception as e:
            self.logger.warning(f"Could not check PostGIS extension: {e}")
    
    def check_data_directory(self) -> bool:
        """
        Check if data directory exists and contains GTFS files.
        
        Returns:
            bool: True if directory and files exist, False otherwise
        """
        if not self.data_directory.exists():
            self.logger.error(f"Data directory does not exist: {self.data_directory}")
            return False
        
        missing_files = []
        for filename in self.gtfs_files.keys():
            file_path = self.data_directory / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        if missing_files:
            self.logger.warning(f"Missing GTFS files: {missing_files}")
            # We'll continue with available files
        
        self.logger.info(f"Data directory validated: {self.data_directory}")
        return True
    
    def load_csv_file(self, filename: str, table_name: str, description: str) -> bool:
        """
        Load a single CSV file into PostgreSQL.
        
        Args:
            filename: Name of the CSV file
            table_name: Target table name in PostgreSQL
            description: Description of the file for logging
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = self.data_directory / filename
        
        if not file_path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return False
        
        try:
            self.logger.info(f"Loading {description} from {filename}...")
            
            # Read CSV file with pandas
            df = pd.read_csv(file_path, low_memory=False)
            self.logger.info(f"Read {len(df)} rows from {filename}")
            
            # Upload to PostgreSQL
            if self.engine is None:
                raise ValueError("Database engine not initialized")
                
            df.to_sql(
                name=table_name,
                schema=self.schema_name,
                con=self.engine,
                if_exists='replace',
                index=False,
                method='multi'
            )
            
            self.logger.info(f"Successfully loaded {filename} into table {self.schema_name}.{table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading {filename}: {e}")
            return False
    
    def load_calendar(self) -> bool:
        """Load calendar.txt file."""
        return self.load_csv_file('calendar.txt', 'cal', 'Calendar service definitions')
    
    def load_calendar_dates(self) -> bool:
        """Load calendar_dates.txt file."""
        return self.load_csv_file('calendar_dates.txt', 'cal_d', 'Calendar date exceptions')
    
    def load_trips(self) -> bool:
        """Load trips.txt file."""
        return self.load_csv_file('trips.txt', 'tri', 'Trip definitions')
    
    def load_stop_times(self) -> bool:
        """Load stop_times.txt file."""
        return self.load_csv_file('stop_times.txt', 'sto_t', 'Stop times for each trip')
    
    def load_frequencies(self) -> bool:
        """Load frequencies.txt file."""
        return self.load_csv_file('frequencies.txt', 'fre', 'Frequency-based service definitions')
    
    def load_routes(self) -> bool:
        """Load routes.txt file."""
        return self.load_csv_file('routes.txt', 'rou', 'Route definitions')
    
    def load_stops(self) -> bool:
        """Load stops.txt file and add geospatial functionality."""
        # First load the CSV data
        success = self.load_csv_file('stops.txt', 'sto', 'Stop definitions')
        
        if not success:
            return False
        
        # Add geospatial processing
        try:
            self.logger.info("Adding geospatial functionality to stops table...")
            self._add_geospatial_to_stops()
            self.logger.info("Geospatial functionality added successfully to stops table")
            return True
        except Exception as e:
            self.logger.error(f"Error adding geospatial functionality to stops: {e}")
            return False
    
    def _add_geospatial_to_stops(self):
        """Add geometry column and spatial index to stops table."""
        if self.engine is None:
            raise ValueError("Database engine not initialized")
        
        sql_commands = [
            # Add geometry column
            f"ALTER TABLE {self.schema_name}.sto ADD COLUMN geom geometry(Point, 25831);",
            
            # Update geometry column with transformed coordinates
            f"""UPDATE {self.schema_name}.sto
                SET geom = ST_Transform(
                           ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326),
                           25831
                       );""",
            
            # Create spatial index
            f"""CREATE INDEX sto_geom_gix
                ON {self.schema_name}.sto
                USING GIST (geom);"""
        ]
        
        with self.engine.connect() as conn:
            for i, sql_command in enumerate(sql_commands, 1):
                try:
                    self.logger.info(f"Executing geospatial command {i}/3...")
                    conn.execute(text(sql_command))
                    conn.commit()
                except Exception as e:
                    self.logger.error(f"Error executing SQL command {i}: {e}")
                    self.logger.error(f"SQL: {sql_command}")
                    raise
    
    def load_shapes(self) -> bool:
        """Load shapes.txt file."""
        return self.load_csv_file('shapes.txt', 'sho', 'Shape definitions for routes')
    
    def load_agency(self) -> bool:
        """Load agency.txt file."""
        return self.load_csv_file('agency.txt', 'age', 'Transit agency information')
    
    def load_transfers(self) -> bool:
        """Load transfers.txt file."""
        return self.load_csv_file('transfers.txt', 'tra', 'Transfer definitions between stops')
    
    def load_all_files(self) -> Dict[str, bool]:
        """
        Load all GTFS files to PostgreSQL.
        
        Returns:
            Dict[str, bool]: Dictionary with filename as key and success status as value
        """
        results = {}
        
        # Load each file using individual functions
        load_functions = [
            ('calendar.txt', self.load_calendar),
            ('calendar_dates.txt', self.load_calendar_dates),
            ('trips.txt', self.load_trips),
            ('stop_times.txt', self.load_stop_times),
            ('frequencies.txt', self.load_frequencies),
            ('routes.txt', self.load_routes),
            ('stops.txt', self.load_stops),
            ('shapes.txt', self.load_shapes),
            ('agency.txt', self.load_agency),
            ('transfers.txt', self.load_transfers)
        ]
        
        for filename, load_function in load_functions:
            try:
                results[filename] = load_function()
            except Exception as e:
                self.logger.error(f"Unexpected error loading {filename}: {e}")
                results[filename] = False
        
        # Log summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        self.logger.info(f"Loading completed: {successful}/{total} files loaded successfully")
        
        return results
    
    def close_connection(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed")