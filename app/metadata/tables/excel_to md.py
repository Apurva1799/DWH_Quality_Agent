from pathlib import Path

import pandas as pd


def csv_to_markdown(csv_path, markdown_path=None):
    df = pd.read_csv(csv_path, encoding="cp1252")

    # Fill NaNs with empty string for cleaner output
    df = df.fillna("")

    # Build Markdown
    header = "| " + " | ".join(df.columns) + " |"
    separator = "|" + "|".join([" --- " for _ in df.columns]) + "|"
    rows = ["| " + " | ".join(str(val) for val in row) + " |" for row in df.values]

    markdown = "\n".join([header, separator] + rows)

    # Save to file
    if markdown_path:
        Path(markdown_path).write_text(markdown, encoding="utf-8")
        print(f"  Markdown saved to {markdown_path}")
    else:
        print(markdown)


# Example usage
csv_file = r"C:\Users\rkts7080002\Downloads\Bus Matrix Kalyani Final Filling.csv"
output_md = r"C:\Users\rkts7080002\Desktop\Family_of_agents\AI-Agent\backend\app\Agent\schema information\Bus_Matrix_Table.md"
csv_to_markdown(csv_file, output_md)
