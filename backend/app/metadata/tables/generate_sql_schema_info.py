import logging
import os
from collections import Counter
from datetime import date

import pyodbc

from app.database import get_db_connection_silver

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Connection details for ODBC Driver 17 for SQL Server
# CONNECTION_STRING removed. Using centralized silver DB connection.

# Output folder path for schema Markdown files
OUTPUT_FOLDER = "Agent\\schema information"


def serialize_json(obj):
    """
    Helper function to serialize objects like `date` that aren't natively JSON serializable.
    """
    if isinstance(obj, date):
        return obj.isoformat()
    return str(obj)


def get_mode(values, max_modes=25):
    """
    Helper function to calculate the mode (most frequent values) of a list.
    Limits the number of mode values to `max_modes`.
    """
    if not values:
        return []
    counter = Counter(values)
    most_common = counter.most_common(max_modes)
    return [item[0] for item in most_common]


def get_table_schema(cursor, schema_name, table_name):
    """
    Get the schema details for a specific table within a schema.
    The logic inspects column values in Python:
      - If all non-null values are ints, return 5 mode examples.
      - If the column is a string and the first non-null value has more than 4 words,
        treat it as a sentence column (return 4 mode examples and mark as irrelevant).
      - Otherwise, for categorical columns, if the unique count is ≤ 25, list them all;
        if more than 25 unique values, return the 25 mode examples.
    """
    logging.info(f"  Fetching schema for table: {schema_name}.{table_name}")
    cursor.execute(
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'"
    )
    columns = [row[0] for row in cursor.fetchall()]
    schema_info = {"TableName": table_name, "Schema": schema_name, "Columns": {}}

    for column_name in columns:
        logging.info(f" Analyzing column: {column_name}")
        cursor.execute(f"SELECT [{column_name}] FROM [{schema_name}].[{table_name}]")
        column_values = [row[0] for row in cursor.fetchall()]

        # Filter out None values for type checking.
        non_null_values = [v for v in column_values if v is not None]

        # Determine column type based on Python value inspection.
        if non_null_values:
            if all(isinstance(v, int) for v in non_null_values):
                col_type = "int"
            elif (
                isinstance(non_null_values[0], str)
                and len(non_null_values[0].split()) > 4
            ):
                col_type = "sentence"
            else:
                col_type = "categorical"
        else:
            col_type = "categorical"

        # Process column based on its determined type.
        if col_type == "int":
            # For int columns, always return 5 mode examples.
            mode_values = get_mode(column_values, max_modes=5)
            schema_info["Columns"][column_name] = {"ExampleModeValues": mode_values}
        elif col_type == "sentence":
            # For sentence columns, always return 4 mode examples and mark as
            # irrelevant.
            mode_values = get_mode(column_values, max_modes=4)
            schema_info["Columns"][column_name] = {
                "ExampleModeValues": mode_values,
                "Note": "Irrelevant column (long sentence values)",
            }
        else:  # categorical
            unique_count = len(set(column_values))
            if unique_count <= 25:
                schema_info["Columns"][column_name] = {
                    "UniqueValues": sorted(set(column_values), key=str)
                }
            else:
                mode_values = get_mode(column_values, max_modes=25)
                schema_info["Columns"][column_name] = {"ExampleModeValues": mode_values}

    return schema_info


def generate_schema_markdown(schema_names):
    """
    Generate schema information in Markdown format for all tables within the specified schemas.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection_silver()
        if conn is None:
            logging.error("  Error generating schema information: Database connection failed.")
            return
        cursor = conn.cursor()

        # Ensure the output folder exists
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        for schema_name in schema_names:
            logging.info(f"  Processing schema: {schema_name}")
            # Get all table names for the specified schema
            cursor.execute(
                f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_TYPE = 'BASE TABLE'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                logging.warning(
                    f"   No tables found in schema '{schema_name}'. Skipping."
                )
                continue

            markdown_output = f"# Schema: {schema_name}\n\n"

            for table_name in tables:
                table_schema = get_table_schema(cursor, schema_name, table_name)
                markdown_output += f"## Table: {table_name}\n\n"

                for column_name, column_info in table_schema["Columns"].items():
                    markdown_output += f"- **Column**: {column_name}\n"
                    if "UniqueValues" in column_info:
                        unique_values = ", ".join(map(str, column_info["UniqueValues"]))
                        markdown_output += f"  - **Unique Values**: {unique_values}\n"
                    if "ExampleModeValues" in column_info:
                        mode_values = ", ".join(
                            map(str, column_info["ExampleModeValues"])
                        )
                        markdown_output += (
                            f"  - **Example Mode Values**: {mode_values}\n"
                        )
                    if "Note" in column_info:
                        markdown_output += f"  - **Note**: {column_info['Note']}\n"
                markdown_output += "\n"

            # Save schema information to a Markdown file
            output_file = os.path.join(OUTPUT_FOLDER, f"{schema_name}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_output)
            logging.info(
                f"  Schema information for '{schema_name}' saved to '{output_file}'."
            )

    except Exception as e:
        logging.error(f"  Error generating schema information: {e}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Specify the schema names you want to analyze
    schema_names = input(
        "Enter schema names (comma-separated, e.g., 'dbo, Sales, Manufacturing'): "
    ).split(",")
    schema_names = [schema.strip() for schema in schema_names]
    generate_schema_markdown(schema_names)
