"""Database connection management using pymssql."""
import pymssql
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseConnection:
    """MS SQL Server connection handler using pymssql."""
    
    def __init__(self):
        self._connection: Optional[pymssql.Connection] = None
    
    def connect(self) -> pymssql.Connection:
        """Establish database connection."""
        try:
            self._connection = pymssql.connect(
                server=settings.DB_SERVER,
                user=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
                database=settings.DB_DATABASE,
                as_dict=True,
                tds_version='7.4'
            )
            logger.info("Database connection established successfully")
            return self._connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            logger.info("Database connection closed")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        cursor = None
        try:
            if not self._connection:
                self.connect()
            cursor = self._connection.cursor()
            yield cursor
            self._connection.commit()
        except Exception as e:
            if self._connection:
                self._connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results."""
        with self.get_cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get schema information for a specific table."""
        query = f"""
        SELECT 
            COLUMN_NAME as column_name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            CHARACTER_MAXIMUM_LENGTH as max_length
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query)
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        results = self.execute_query(query)
        return [row['TABLE_NAME'] for row in results]
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

# Global database connection instance
db_connection = DatabaseConnection()