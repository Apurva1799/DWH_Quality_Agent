#  Gold Database Chatbot

An intelligent chatbot interface for querying the Gold database using natural language.

##  Quick Start

### Option 1: Command Line Interface (CLI)

```bash
# Start the CLI chatbot
make chatbot

# Or directly
python3 scripts/gold_chatbot.py
```

### Option 2: Web Interface

```bash
# Start the web chatbot
make chatbot-web

# Or directly
python3 scripts/gold_chatbot_web.py

# Then open browser: http://localhost:5000
```

##  How to Use

### CLI Chatbot

1. **Start the chatbot**: `make chatbot`
2. **Type your question**: Ask anything about your data
3. **Special commands**:
   - `tables` - List all available tables
   - `help` - Show help information
   - `quit` or `exit` - End the session

### Example Queries

```
 You: Show me all tables
 Bot: Here are the available tables in GOLD_DB...

 You: What are the top 10 customers?
 Bot: The top 10 customers by revenue are...

 You: Count total records in main table
 Bot: There are 15,234 records in the table.

 You: Show sales data for last month
 Bot: Here are the sales figures for last month...
```

### Web Chatbot

1. **Start the web server**: `make chatbot-web`
2. **Open browser**: Go to `http://localhost:5000`
3. **Start chatting**: Type your questions in the chat box
4. **Use example chips**: Click on example queries to try them

##  Features

### Natural Language Processing
- Convert plain English questions to SQL queries
- Understand context and intent
- Handle complex queries with joins and aggregations

### Multi-Database Support
-  Gold Database (GOLD_DB)
-  Silver Database (Silver_DB)
-  IoT Database (IOTEDGEDB)
-  Development Database (Development)

### Smart Query Generation
- Automatic SQL query generation
- Query validation and correction
- Error handling with helpful suggestions

### Security
- URL-encoded credentials (handles special characters like @)
- Read-only database access
- Session management
- No SQL injection risks

##  Architecture

```
User Input (Natural Language)
        ↓
 Orchestrator Agent
        ↓
 SQL Agent (Gold DB)
        ↓
 Query Generation
        ↓
 Database Execution
        ↓
 Results & Formatting
        ↓
 Natural Language Response
```

##  Configuration

The chatbot automatically uses your existing `.env` configuration:

```env
# Gold Database
SQL_GOLDDB_SERVER=afdbsrv.kalyanicorp.com
SQL_GOLDDB_NAME=GOLD_DB
SQL_GOLDDB_USERNAME=Gold_Reader
SQL_GOLDDB_PASSWORD=goldreader@bfl123
```

##  Files

- `scripts/gold_chatbot.py` - CLI chatbot interface
- `scripts/gold_chatbot_web.py` - Web chatbot interface
- `scripts/test_gold_db_connection.py` - Connection test
- `scripts/setup_gold_db.py` - Configuration setup

##  Example Use Cases

### 1. Data Exploration
```
"Show me all tables in the database"
"What columns are in the customer table?"
"Show me the first 5 rows of orders"
```

### 2. Analytics Queries
```
"What are the top 10 products by sales?"
"Show monthly revenue trend"
"Count orders by status"
"Find customers with no orders"
```

### 3. Data Quality Checks
```
"Find duplicate records"
"Show null values in customer table"
"Check for invalid email addresses"
"List orphaned records"
```

### 4. Reporting
```
"Generate sales report for Q4 2023"
"Show customer growth by month"
"List overdue payments"
"Top performing regions"
```

##  Troubleshooting

### Connection Issues
```bash
# Test the connection first
make test-gold-db

# If it fails, check:
# 1. Network connectivity to afdbsrv.kalyanicorp.com
# 2. Port 1433 is open
# 3. Credentials are correct in .env file
```

### Query Issues
- **Query too slow**: Add more specific filters
- **No results**: Check table names and column names
- **Error**: Try rephrasing the question

### LLM Issues
If the LLM clients are not available, the chatbot will still work for direct database queries using pre-built templates.

##  API Usage

You can also query the chatbot via REST API:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show top customers from gold database",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

##  Next Steps

1. **Test the connection**: `make test-gold-db`
2. **Start CLI chatbot**: `make chatbot`
3. **Or start web chatbot**: `make chatbot-web`
4. **Ask questions** about your data!

##  Support

If you encounter issues:
1. Check database connectivity: `make test-gold-db`
2. Verify configuration: `make setup-gold-db`
3. Check logs in `logs/app.log`
4. Review the [troubleshooting tips](#troubleshooting)

---

**Happy Chatting with Your Data!** 
