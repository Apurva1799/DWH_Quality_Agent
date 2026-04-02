#!/usr/bin/env python3
"""Test SQL extraction with sample LLM responses"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.sql_agent import SQLAgent

# Test cases with different response formats
test_responses = [
    # Case 1: Simple SQL
    "SELECT * FROM customers;",
    
    # Case 2: SQL with explanation
    "Here is the SQL query:\n\nSELECT name, email FROM users WHERE active = 1;\n\nThis will return all active users.",
    
    # Case 3: SQL in code block
    "```sql\nSELECT COUNT(*) FROM orders;\n```",
    
    # Case 4: SQL with markdown
    "```\nSELECT product_name, price FROM products WHERE price > 100;\n```",
    
    # Case 5: Multi-line SQL
    "SELECT c.name, o.order_date\nFROM customers c\nJOIN orders o ON c.id = o.customer_id\nWHERE o.status = 'completed';",
]

print("Testing SQL Extraction")
print("=" * 60)

agent = SQLAgent("gold")

for i, response in enumerate(test_responses, 1):
    print(f"\nTest {i}:")
    print(f"Input: {response[:50]}...")
    result = agent._extract_sql_from_response(response)
    if result:
        print(f"Extracted: {result[:60]}...")
        print("Status: PASS")
    else:
        print("Status: FAIL - No SQL extracted")

print("\n" + "=" * 60)
