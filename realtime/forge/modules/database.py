import psycopg2
import pandas as pd
import sqlite3

class Database:
    def connect(self, url: str):
        raise NotImplementedError("Subclasses must implement this method.")

    def read_tables(self, schema: str = None) -> str:
        raise NotImplementedError("Subclasses must implement this method.")

    def execute_sql(self, sql: str) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement this method.")

    def disconnect(self):
        raise NotImplementedError("Subclasses must implement this method.")

class PostgresDatabase(Database):
    def __init__(self):
        self.connection = None

    def connect(self, url: str):
        self.connection = psycopg2.connect(url)

    def read_tables(self, schema: str = None) -> str:
        cursor = self.connection.cursor()
        if schema:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                """,
                (schema,)
            )
        else:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                """
            )
        tables = cursor.fetchall()

        table_defs = ""
        for table in tables:
            if schema:
                table_schema = schema
                table_name = table[0]
            else:
                table_schema, table_name = table
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                """,
                (table_schema, table_name)
            )
            columns = cursor.fetchall()
            table_defs += f"CREATE TABLE {table_schema}.{table_name} (\n"
            col_defs = []
            for col in columns:
                col_def = f"    {col[0]} {col[1]}"
                if col[3]:
                    col_def += f" DEFAULT {col[3]}"
                if col[2] == 'NO':
                    col_def += " NOT NULL"
                col_defs.append(col_def)
            table_defs += ",\n".join(col_defs)
            table_defs += "\n);\n\n"
        cursor.close()
        return table_defs

    def execute_sql(self, sql: str) -> pd.DataFrame:
        df = pd.read_sql_query(sql, self.connection)
        return df

    def disconnect(self):
        self.connection.close()

class SQLiteDatabase(Database):
    def __init__(self):
        self.connection = None

    def connect(self, url: str):
        self.connection = sqlite3.connect(url)

    def read_tables(self, schema: str = None) -> str:
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        table_defs = ""
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            table_defs += f"CREATE TABLE {table_name} (\n"
            col_defs = []
            for col in columns:
                col_def = f"    {col[1]} {col[2]}"
                if col[3]:
                    col_def += " NOT NULL"
                if col[4]:
                    col_def += f" DEFAULT {col[4]}"
                if col[5]:
                    col_def += " PRIMARY KEY"
                col_defs.append(col_def)
            table_defs += ",\n".join(col_defs)
            table_defs += "\n);\n\n"
        cursor.close()
        return table_defs

    def execute_sql(self, sql: str) -> pd.DataFrame:
        with self.connection:
            cursor = self.connection.cursor()
            try:
                cursor.execute(sql)
                self.connection.commit()  # Ensure changes are saved

                # If it's a SELECT query, return the results
                if sql.strip().lower().startswith("select"):
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    return pd.DataFrame(rows, columns=columns)
                else:
                    return pd.DataFrame()  # Return an empty DataFrame for non-SELECT queries
            except sqlite3.OperationalError as e:
                print(f"SQL Execution Error: {e}")  # Debugging print
                raise e
            finally:
                cursor.close()

    def disconnect(self):
        self.connection.close()

def get_database_instance(sql_dialect: str) -> Database:
    if sql_dialect == 'postgres':
        return PostgresDatabase()
    elif sql_dialect == 'sqlite':
        return SQLiteDatabase()
    else:
        raise ValueError(f"Unsupported SQL dialect: {sql_dialect}")
