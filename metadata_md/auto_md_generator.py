# ==============================================================================
# SCRIPT SETUP: DYNAMICALLY FIND AND IMPORT THE 'database' MODULE
# ==============================================================================
import sys
from pathlib import Path
from collections import defaultdict

try:
    current_script_path = Path(__file__).resolve()
    backend_path = current_script_path.parents[3]
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
        print(f"Temporarily added '{backend_path}' to Python's search path.")
    from app.database import get_db_connection_gold
    print("Successfully imported 'get_db_connection_gold'.")
except (ImportError, IndexError) as e:
    print(f"\nFATAL: Could not import 'get_db_connection_gold'. Error: {e}")
    print("Ensure __init__.py files exist and the folder structure is correct.")
    sys.exit(1)
# ==============================================================================
# END OF SCRIPT SETUP
# ==============================================================================

import pandas as pd

OUTPUT_FOLDER_PATH = Path(__file__).resolve().parent


def format_sql_name(schema, name):
    return f"[{schema}].[{name}]"


def format_column_name(name):
    return f"[{name}]"


def execute_query(cursor, query, params=None):
    try:
        cursor.execute(query, params) if params else cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame()
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame.from_records(rows, columns=columns)
    except Exception as e:
        print(f"      [Query Failed] Error executing query: {e}")
        return pd.DataFrame()


def get_table_columns(cursor, schema, table_name):
    query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION;
    """
    df = execute_query(cursor, query, (schema, table_name))
    if df.empty:
        return []
    df["DATA_TYPE_GROUP"] = df["DATA_TYPE"].apply(
        lambda x: (
            "numeric"
            if x in [
                "int", "bigint", "smallint", "tinyint", "decimal", "numeric",
                "float", "real", "money", "smallmoney",
            ]
            else "string"
        )
    )
    return df.to_dict('records')


def generate_detailed_column_profile(cursor, schema, name):
    """Generates a detailed, column-by-column profile for a single table."""
    profile_lines = []
    full_table_name = format_sql_name(schema, name)
    
    columns = get_table_columns(cursor, schema, name)
    if not columns:
        profile_lines.append("*Could not retrieve column information.*")
        return "\n".join(profile_lines)
    
    profile_lines.append("**Column Profiles:**\n")

    for column in columns:
        col_name = column["COLUMN_NAME"]
        col_type = column["DATA_TYPE"]
        col_group = column["DATA_TYPE_GROUP"]
        col_len = (
            f"({int(column['CHARACTER_MAXIMUM_LENGTH'])})"
            if column["CHARACTER_MAXIMUM_LENGTH"]
            and column["CHARACTER_MAXIMUM_LENGTH"] is not None
            and column["CHARACTER_MAXIMUM_LENGTH"] > 0
            else ""
        )
        safe_col_name = format_column_name(col_name)

        profile_lines.append(f"*   `{col_name}` ({col_type}{col_len})")

        # Skip profiling key/id numeric columns as measures
        if col_name.lower().endswith(("id", "key")) and col_group == "numeric":
            continue

        # Numeric stats
        if col_group == "numeric":
            stats_query = f"""
                SELECT 
                    MIN({safe_col_name}) as MinValue, 
                    MAX({safe_col_name}) as MaxValue,
                    (
                        SELECT DISTINCT 
                            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {safe_col_name}) OVER() 
                        FROM {full_table_name} 
                        WHERE {safe_col_name} IS NOT NULL
                    ) as MedianValue
                FROM {full_table_name}
            """
            stats_df = execute_query(cursor, stats_query)
            if not stats_df.empty and stats_df.iloc[0]['MinValue'] is not None:
                stats = stats_df.iloc[0]
                profile_lines.append(
                    f"    *   **Range:** {stats['MinValue']} – {stats['MaxValue']}"
                )
                profile_lines.append(
                    f"    *   **Median:** {stats['MedianValue']}"
                )

        # String / categorical stats
        else:
            unique_count_query = f"""
                SELECT COUNT(DISTINCT {safe_col_name}) as Cnt 
                FROM {full_table_name};
            """
            unique_count_df = execute_query(cursor, unique_count_query)
            unique_count = unique_count_df.iloc[0]["Cnt"] if not unique_count_df.empty else 0

            if unique_count == 0:
                profile_lines.append("    *   **Values:** *No data found.*")
                continue

            if 0 < unique_count < 30:
                header = "All Values"
                values_query = f"""
                    SELECT DISTINCT TOP 30 {safe_col_name} 
                    FROM {full_table_name} 
                    WHERE {safe_col_name} IS NOT NULL 
                    ORDER BY {safe_col_name};
                """
            else:
                header = "Mode 5 values (most frequent)"
                values_query = f"""
                    SELECT TOP 5 {safe_col_name} 
                    FROM {full_table_name} 
                    WHERE {safe_col_name} IS NOT NULL 
                    GROUP BY {safe_col_name} 
                    ORDER BY COUNT(*) DESC;
                """
            
            values_df = execute_query(cursor, values_query)
            if not values_df.empty:
                values_list = [str(v) for v in values_df[col_name].dropna().unique()]
                truncated_values = [
                    (v[:75] + "...") if len(v) > 75 else v for v in values_list
                ]
                display_values = ", ".join([f"`{v}`" for v in truncated_values])
                profile_lines.append(f"    *   **{header}:** {display_values}")
    
    return "\n".join(profile_lines)


# ==============================================================================
# RELATIONSHIP DISCOVERY (FK + DATA-VALIDATED)
# ==============================================================================

def get_all_foreign_keys(cursor):
    """
    Returns all FK relationships in the database using sys.* views.

    Columns:
    - FK_Name
    - FK_Schema, FK_Table, FK_Column
    - PK_Schema, PK_Table, PK_Column
    """
    query = """
        SELECT
            fk.name AS FK_Name,
            OBJECT_SCHEMA_NAME(fk.parent_object_id) AS FK_Schema,
            OBJECT_NAME(fk.parent_object_id) AS FK_Table,
            pc.name AS FK_Column,
            OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS PK_Schema,
            OBJECT_NAME(fk.referenced_object_id) AS PK_Table,
            rc.name AS PK_Column
        FROM sys.foreign_keys fk
        INNER JOIN sys.foreign_key_columns fkc 
            ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.columns pc 
            ON fkc.parent_object_id = pc.object_id 
           AND fkc.parent_column_id = pc.column_id
        INNER JOIN sys.columns rc 
            ON fkc.referenced_object_id = rc.object_id 
           AND fkc.referenced_column_id = rc.column_id
        WHERE fk.is_disabled = 0
          AND fk.is_ms_shipped = 0;
    """
    df = execute_query(cursor, query)
    if df.empty:
        return []
    return df.to_dict("records")


def build_fk_relationship_maps(fact_tables, dim_tables, fk_rows):
    """
    Build:
      - fact_dim_map:  (FactSchema, FactTable) -> list of {schema, table, fact_col, dim_col}
      - dim_relationships_map: (DimSchema, DimTable) -> list of {schema, table, parent_col, ref_col}
    using only REAL foreign keys.
    """
    fact_keys = {(t["TABLE_SCHEMA"], t["TABLE_NAME"]) for t in fact_tables}
    dim_keys = {(t["TABLE_SCHEMA"], t["TABLE_NAME"]) for t in dim_tables}

    fact_dim_map = defaultdict(list)
    dim_relationships_map = defaultdict(list)

    for row in fk_rows:
        fk_schema = row["FK_Schema"]
        fk_table = row["FK_Table"]
        fk_col = row["FK_Column"]
        pk_schema = row["PK_Schema"]
        pk_table = row["PK_Table"]
        pk_col = row["PK_Column"]

        parent_key = (fk_schema, fk_table)
        ref_key = (pk_schema, pk_table)

        # FACT -> DIM relationships via FK
        if parent_key in fact_keys and ref_key in dim_keys:
            fact_dim_map[parent_key].append(
                {
                    "schema": pk_schema,
                    "table": pk_table,
                    "fact_col": fk_col,
                    "dim_col": pk_col,
                }
            )

        # DIM -> DIM chaining via FK
        if parent_key in dim_keys and ref_key in dim_keys:
            dim_relationships_map[parent_key].append(
                {
                    "schema": pk_schema,
                    "table": pk_table,
                    "parent_col": fk_col,
                    "ref_col": pk_col,
                }
            )

    return fact_dim_map, dim_relationships_map


def augment_dim_relationships_with_data(cursor, dim_tables, dim_columns_map, dim_relationships_map):
    """
    For each dimension, look for other dimensions that share a key/ID column
    AND actually join on that column (data-level validation).
    """
    dim_set = {(t["TABLE_SCHEMA"], t["TABLE_NAME"]) for t in dim_tables}

    for (schema, name), cols in dim_columns_map.items():
        if (schema, name) not in dim_set:
            continue

        key_cols = [c for c in cols if c.lower().endswith(("id", "key"))]
        if not key_cols:
            continue

        for col in key_cols:
            for (other_schema, other_name), other_cols in dim_columns_map.items():
                if (schema, name) == (other_schema, other_name):
                    continue
                if (other_schema, other_name) not in dim_set:
                    continue
                if col not in other_cols:
                    continue

                # Avoid duplicates
                existing = dim_relationships_map.get((schema, name), [])
                if any(
                    r["schema"] == other_schema
                    and r["table"] == other_name
                    and r["parent_col"] == col
                    for r in existing
                ):
                    continue

                table_a = format_sql_name(schema, name)
                table_b = format_sql_name(other_schema, other_name)
                col_safe = format_column_name(col)

                join_query = f"""
                    SELECT TOP 1 1
                    FROM {table_a} a
                    JOIN {table_b} b
                        ON a.{col_safe} = b.{col_safe}
                       AND a.{col_safe} IS NOT NULL
                       AND b.{col_safe} IS NOT NULL;
                """
                df = execute_query(cursor, join_query)
                if not df.empty:
                    dim_relationships_map[(schema, name)].append(
                        {
                            "schema": other_schema,
                            "table": other_name,
                            "parent_col": col,
                            "ref_col": col,
                        }
                    )


def augment_fact_dim_relationships_with_data(
    cursor, fact_tables, dim_tables, dim_columns_map, fact_dim_map
):
    """
    For each fact, find dimensions with shared key/ID columns that actually join.
    """
    dim_set = {(t["TABLE_SCHEMA"], t["TABLE_NAME"]) for t in dim_tables}
    # For fast lookups
    dim_cols_map = dim_columns_map

    # Build a map of fact -> column set
    fact_cols_map = {
        (f["TABLE_SCHEMA"], f["TABLE_NAME"]): {c["COLUMN_NAME"] for c in f["columns"]}
        for f in fact_tables
    }

    for fact in fact_tables:
        fs, fn = fact["TABLE_SCHEMA"], fact["TABLE_NAME"]
        fact_key = (fs, fn)
        fact_cols = fact_cols_map.get(fact_key, set())
        fact_key_cols = [c for c in fact_cols if c.lower().endswith(("id", "key"))]
        if not fact_key_cols:
            continue

        for (ds, dn) in dim_set:
            dim_cols = dim_cols_map.get((ds, dn), set())
            common_keys = [c for c in fact_key_cols if c in dim_cols]
            if not common_keys:
                continue

            for col in common_keys:
                # Avoid duplicates
                existing = fact_dim_map.get(fact_key, [])
                if any(
                    r["schema"] == ds
                    and r["table"] == dn
                    and r["fact_col"] == col
                    for r in existing
                ):
                    continue

                t_fact = format_sql_name(fs, fn)
                t_dim = format_sql_name(ds, dn)
                col_safe = format_column_name(col)

                join_query = f"""
                    SELECT TOP 1 1
                    FROM {t_fact} f
                    JOIN {t_dim} d
                        ON f.{col_safe} = d.{col_safe}
                       AND f.{col_safe} IS NOT NULL
                       AND d.{col_safe} IS NOT NULL;
                """
                df = execute_query(cursor, join_query)
                if not df.empty:
                    fact_dim_map[fact_key].append(
                        {
                            "schema": ds,
                            "table": dn,
                            "fact_col": col,
                            "dim_col": col,
                        }
                    )


# ==============================================================================
# MARKDOWN GENERATORS (UNCHANGED FORMAT)
# ==============================================================================

def generate_fact_markdown(fact_info, direct_dims, dim_relationships_map):
    schema, name = fact_info["TABLE_SCHEMA"], fact_info["TABLE_NAME"]
    markdown_lines = [f"## Fact Table: `{schema}.{name}`", "---"]

    columns = fact_info["columns"]
    markdown_lines.append("**Columns:**")
    for col in columns:
        markdown_lines.append(f"- `{col['COLUMN_NAME']}` ({col['DATA_TYPE']})")
    markdown_lines.append("\n---\n")

    markdown_lines.append("**Related Dimensions:**")
    if not direct_dims:
        markdown_lines.append("- None found.")
    else:
        for rel in sorted(direct_dims, key=lambda x: x['table']):
            dim_name = rel['table']
            join_key = (
                rel['fact_col']
                if rel['fact_col'] == rel['dim_col']
                else f"{rel['fact_col']} -> {rel['dim_col']}"
            )
            
            line = f"- {dim_name} (join over `{join_key}`)"

            chained_dims = dim_relationships_map.get((rel['schema'], dim_name), [])
            if chained_dims:
                chained_parts = []
                for chained_rel in chained_dims:
                    chained_name = chained_rel['table']
                    chained_key = chained_rel['parent_col']
                    chained_parts.append(f"{chained_name} (join over `{chained_key}`)")
                line += " joins with " + ", ".join(chained_parts)
            
            markdown_lines.append(line)
    return "\n".join(markdown_lines)


def generate_dim_markdown(cursor, dim_info, dim_relationships_map):
    """Generates the content for a Dimension table's markdown file."""
    schema, name = dim_info["TABLE_SCHEMA"], dim_info["TABLE_NAME"]
    markdown_lines = [f"## Dimension Table: `{schema}.{name}`", "---"]

    # Add detailed column profiles
    profile_md = generate_detailed_column_profile(cursor, schema, name)
    markdown_lines.append(profile_md)

    # FK + data-validated referenced dimensions
    referenced_dims = dim_relationships_map.get((schema, name), [])

    if referenced_dims:
        markdown_lines.append("\n---\n")
        markdown_lines.append("**Referenced Dimensions:**")
        for rel in referenced_dims:
            ref_name = rel['table']
            join_key = f"`{rel['parent_col']}` -> `{rel['ref_col']}`"
            markdown_lines.append(f"- {ref_name} (via {join_key})")
    
    return "\n".join(markdown_lines)


# ==============================================================================
# MAIN GENERATION FUNCTION
# ==============================================================================

def generate_and_save_markdown_files(conn, output_folder: Path):
    output_folder.mkdir(parents=True, exist_ok=True)
    print(f"\nMarkdown files will be saved to: {output_folder.resolve()}")

    try:
        cursor = conn.cursor()
        print("Fetching table list with schemas...")
        query = """
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE';
        """
        all_tables_df = execute_query(cursor, query)

        if all_tables_df.empty:
            print("No tables found in the database.")
            return

        all_tables = all_tables_df.to_dict("records")
        fact_tables = [t for t in all_tables if t["TABLE_NAME"].lower().startswith("fact_")]
        dim_tables = [t for t in all_tables if t["TABLE_NAME"].lower().startswith("dim_")]
        ft_tables = [t for t in all_tables if t["TABLE_NAME"].lower().startswith("ft_")]
        
        print(f"Found {len(fact_tables)} fact, {len(dim_tables)} dimension, and {len(ft_tables)} flat tables.")

        # Pre-computing table schemas and relationships...
        print("\nPre-computing table schemas and relationships...")

        # Load columns for dimensions (for chaining & join detection)
        dim_columns_map = {
            (tbl["TABLE_SCHEMA"], tbl["TABLE_NAME"]): {
                c['COLUMN_NAME'] for c in get_table_columns(cursor, tbl["TABLE_SCHEMA"], tbl["TABLE_NAME"])
            }
            for tbl in dim_tables
        }
        
        # Load columns for facts (for metadata & join detection)
        for fact in fact_tables:
            fact["columns"] = get_table_columns(cursor, fact["TABLE_SCHEMA"], fact["TABLE_NAME"])

        # 1) Base relationships via foreign keys
        print("Loading foreign key relationships...")
        fk_rows = get_all_foreign_keys(cursor)
        print(f"Found {len(fk_rows)} foreign key relationships in the database.")

        fact_dim_map, dim_relationships_map = build_fk_relationship_maps(
            fact_tables=fact_tables,
            dim_tables=dim_tables,
            fk_rows=fk_rows,
        )

        # 2) Augment Dim->Dim chaining using data validation
        print("Augmenting dimension chaining via data-level checks...")
        augment_dim_relationships_with_data(
            cursor,
            dim_tables,
            dim_columns_map,
            dim_relationships_map,
        )

        # 3) Augment Fact->Dim relationships using data validation (for cases without FKs)
        print("Augmenting fact-dimension relationships via data-level checks...")
        augment_fact_dim_relationships_with_data(
            cursor,
            fact_tables,
            dim_tables,
            dim_columns_map,
            fact_dim_map,
        )

        # 1. Process Fact Tables
        print("\nGenerating markdown for Fact tables...")
        for fact_info in fact_tables:
            name = fact_info["TABLE_NAME"]
            schema = fact_info["TABLE_SCHEMA"]
            output_file_path = output_folder / f"{name}.md"
            
            print(f"  -> Processing {name}...")
            fact_key = (schema, name)
            direct_dims = fact_dim_map.get(fact_key, [])
            markdown_content = generate_fact_markdown(fact_info, direct_dims, dim_relationships_map)
            
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"     ... Generated: {output_file_path.name}")

        # 2. Process Dimension Tables
        print("\nGenerating markdown for Dimension tables...")
        for dim_info in dim_tables:
            name = dim_info["TABLE_NAME"]
            output_file_path = output_folder / f"{name}.md"
            
            print(f"  -> Processing {name}...")
            markdown_content = generate_dim_markdown(cursor, dim_info, dim_relationships_map)

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"     ... Generated: {output_file_path.name}")

        # 3. Process Flat Tables
        print("\nGenerating markdown for Flat tables...")
        for ft_info in ft_tables:
            schema, name = ft_info["TABLE_SCHEMA"], ft_info["TABLE_NAME"]
            output_file_path = output_folder / f"{name}.md"

            print(f"  -> Processing {name}...")
            header = [
                f"## Flat Table: `{schema}.{name}`",
                "---",
                "This is a self-contained table.\n"
            ]
            profile_md = generate_detailed_column_profile(cursor, schema, name)

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(header) + profile_md)
            print(f"     ... Generated: {output_file_path.name}")

    except Exception as e:
        print(f"\nFATAL: An error occurred during database processing: {e}")

    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    print("--- Starting Database Schema Documentation Generator ---")
    connection = None
    try:
        connection = get_db_connection_gold()
        if connection:
            generate_and_save_markdown_files(connection, OUTPUT_FOLDER_PATH)
        else:
            print("FATAL: Failed to establish a database connection. Exiting.")
            sys.exit(1)
    except Exception as e:
        print(f"FATAL: An unexpected error occurred in the main execution block: {e}")
    finally:
        if connection:
            connection.close()
            print("\nDatabase connection closed.")
    print("\n--- Generation Complete ---")


