# Multi-Agent Database Chatbot

A comprehensive multi-agent chatbot system for MSSQL database interactions using on-prem LLM clients (Nemotron and Qwen) built with FastAPI.

## Features

- **Multi-Agent Architecture**: Orchestrator, SQL Agent, Query Corrector, Response Analyser
- **Existing LLM Integration**: Uses your existing Sequential LLM Client, DGX 3B Client, and DocumentDB Client
- **MSSQL Database Support**: Full integration with Microsoft SQL Server
- **Conversation Management**: Session tracking and history storage
- **Error Handling**: Comprehensive fallback mechanisms and error recovery
- **Real-time Analysis**: Data pattern detection, anomaly detection, and insights

## Architecture

```
        
   User Request     FastAPI         Orchestrator   
   (REST API)           Gateway              Agent         
        
                                                        
                       
                                                                                   
                                                                                   
                                    
               SQL Agent                  Query Corrector              Response        
                                            Agent                      Analyser        
             - Query Gen                  - Syntax Fix                 - Quality Check 
             - Execution                  - Optimization               - Format        
             - Results                    - Validation                 - Context       
                                    
                                                                                   
                       
                                                      
                       
                                                                                   
                                                                                   
                                    
             Sequential LLM                 DGX 3B                       MSSQL Server  
               Client                       Client                       Database      
             (Nemotron)                   (Qwen/NIM)                                   
                                    
```

## Agent Responsibilities

### 1. Orchestrator Agent
- **LLM Client**: Sequential LLM Client (Nemotron)
- **Purpose**: Central coordinator that routes requests and manages agent workflow
- **Functions**: Intent classification, request routing, conversation context management

### 2. SQL Agent
- **LLM Client**: Sequential LLM Client (Nemotron)
- **Purpose**: Handle all SQL-related operations and database interactions
- **Functions**: Query generation, execution, schema retrieval, safety checks

### 3. Query Corrector Agent
- **LLM Client**: DGX 3B Client (Qwen/NIM)
- **Purpose**: Validate, optimize, and correct SQL queries
- **Functions**: Syntax validation, error correction, optimization suggestions

### 4. Response Analyser Agent
- **LLM Client**: DGX 3B Client (Qwen/NIM)
- **Purpose**: Analyze and format responses for better user experience
- **Functions**: Result analysis, pattern detection, natural language explanations

## Quick Start

### Prerequisites

- Python 3.8+
- MSSQL Server
- Existing LLM services:
  - Sequential LLM Client (Nemotron)
  - DGX 3B Client (Qwen/NIM)
  - DocumentDB Client

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd Multi_Agent_System
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

4. **Place your existing client files**:
   - `llm_clients.py` (Sequential LLM Client)
   - `dgx_3b_client.py` (DGX 3B Client)
   - `documentdb_client.py` (DocumentDB Client)

### Configuration

Edit the `.env` file with your actual endpoints:

```env
# Database Configuration
MSSQL_SERVER=your-mssql-server
MSSQL_DATABASE=your-database
MSSQL_USERNAME=your-username
MSSQL_PASSWORD=your-password

# LLM Client Configuration
SEQUENTIAL_LLM_BASE_URL=http://your-nemotron-server:port
DGX_3B_BASE_URL=https://your-dgx-server:8193
DOCUMENTDB_BASE_URL=http://your-documentdb-server:port
DOCUMENTDB_USERNAME=your-username
DOCUMENTDB_PASSWORD=your-password
```

### Running the Application

1. **Start the API server**:
```bash
python -m app.main
```

2. **Or use uvicorn directly**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### Main Endpoints

- `POST /chat` - Main chat endpoint for processing user queries
- `GET /health` - Comprehensive health check of all components
- `GET /schema` - Get database schema information
- `POST /validate-sql` - Validate SQL query syntax

### Conversation Management

- `GET /conversations/{user_id}/{session_id}` - Get conversation history
- `DELETE /conversations/{user_id}/{session_id}` - Clear conversation history

### System Status

- `GET /agents/status` - Get status of all agents
- `GET /` - Root endpoint with API information

## Usage Examples

### Chat Request

```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "message": "Show me all customers from California",
    "user_id": "user123",
    "session_id": "session456"
})

print(response.json())
```

### Health Check

```python
response = requests.get("http://localhost:8000/health")
print(response.json())
```

## Workflow Example

1. **User Query**: "Show me all customers from California"

2. **Orchestrator** (Nemotron):
   - Classifies intent as "sql_query"
   - Routes to SQL workflow

3. **SQL Agent** (Nemotron):
   - Generates SQL: `SELECT * FROM customers WHERE state = 'CA';`

4. **Query Corrector** (Qwen/NIM):
   - Validates SQL syntax
   - Returns: "SQL query is valid"

5. **SQL Execution**:
   - Executes query against MSSQL
   - Returns results

6. **Response Analyser** (Qwen/NIM):
   - Analyzes results for patterns
   - Generates natural language explanation
   - Stores conversation in DocumentDB

7. **Final Response**: "Found 245 customers from California. Here are the results..."

## Error Handling

The system includes comprehensive error handling:

- **LLM Client Failures**: Automatic fallback between Sequential and DGX clients
- **SQL Execution Errors**: Detailed error messages and correction suggestions
- **Database Connectivity**: Connection pooling and retry mechanisms
- **Agent Failures**: Graceful degradation and error reporting

## Monitoring and Logging

- **Structured Logging**: Using Loguru for detailed application logs
- **Health Checks**: Comprehensive monitoring of all components
- **Performance Metrics**: Execution time tracking for all operations
- **Conversation Analytics**: Stored in DocumentDB for analysis

## Security Considerations

- **SQL Injection Prevention**: Parameterized queries and validation
- **API Security**: Configurable CORS and authentication
- **Data Privacy**: No sensitive data logging
- **Session Isolation**: User-based session management

## Development

### Project Structure

```
Multi_Agent_System/
 app/
    agents/
       base.py              # Base agent class
       orchestrator.py       # Orchestrator agent
       sql_agent.py          # SQL generation agent
       query_corrector.py    # Query correction agent
       response_analyser.py  # Response analysis agent
    config.py                # Configuration management
    database.py              # MSSQL database layer
    llm_manager.py           # LLM client manager
    main.py                  # FastAPI application
 llm_clients.py               # Your Sequential LLM Client
 dgx_3b_client.py             # Your DGX 3B Client
 documentdb_client.py         # Your DocumentDB Client
 requirements.txt
 .env.example
 README.md
```

### Testing

Run the health check to verify all components are working:

```bash
curl http://localhost:8000/health
```

Test a simple chat request:

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, how can you help me?"}'
```

## Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  multi-agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MSSQL_SERVER=mssql
      - SEQUENTIAL_LLM_BASE_URL=http://sequential-llm:8000
      - DGX_3B_BASE_URL=https://dgx-3b:8193
      - DOCUMENTDB_BASE_URL=http://documentdb:8000
    depends_on:
      - mssql
      - redis

  mssql:
    image: mcr.microsoft.com/mssql/server:2019-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourPassword123
    ports:
      - "1433:1433"

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## Troubleshooting

### Common Issues

1. **LLM Client Connection Errors**:
   - Verify base URLs in `.env`
   - Check SSL verification settings
   - Ensure LLM services are running

2. **Database Connection Issues**:
   - Verify MSSQL server credentials
   - Check network connectivity
   - Ensure database exists

3. **DocumentDB Authentication**:
   - Verify username and password
   - Check if DocumentDB service is running
   - Ensure proper SSL settings

### Logs

Check application logs:

```bash
tail -f logs/app.log
```

## License

This project is licensed under the MIT License.

## Support

For support and questions, please refer to the documentation or create an issue in the repository.
