"""Database connection management."""
import pyodbc
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseConnection:
    """MS SQL Server connection handler."""
    
    def __init__(self):
        self.connection_string = settings.database_url
        self._connection: Optional[pyodbc.Connection] = None
    
    def connect(self) -> pyodbc.Connection:
        """Establish database connection."""
        try:
            self._connection = pyodbc.connect(self.connection_string)
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
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
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