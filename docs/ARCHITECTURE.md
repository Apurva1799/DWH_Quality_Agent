# Multi-Agent System Architecture with Existing LLM Clients

## Overview
A comprehensive multi-agent chatbot system for MSSQL database interactions using your existing on-prem LLM clients (Sequential LLM Client, DGX 3B Client, DocumentDB Client) built with FastAPI.

## System Architecture

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
             /llm_config                  /health                                      
             /retrieve                    /llm_config                                  
                                    
```

## Integration with Existing LLM Clients

### 1. Sequential LLM Client Integration
**Purpose**: Primary client for Nemotron LLM operations

**Integration Points**:
- Use existing `LLMClient` class for query generation
- Leverage `/llm_config` and `/retrieve` endpoints
- Implement async wrapper around polling mechanism
- Use for complex SQL generation and orchestration

**Configuration**:
```python
# From your existing client
sequential_client = LLMClient(base_url="http://nemotron-server:port")
response = sequential_client.generate_text(
    model="nemotron-4-340b",
    query_text=prompt,
    temperature=0.1
)
```

### 2. DGX 3B Client Integration  
**Purpose**: Secondary client for Qwen/NIM operations

**Integration Points**:
- Use existing `LLM_3B_Client` for query correction and analysis
- Leverage streaming capabilities for real-time responses
- Use health check functionality for client availability
- Implement fallback mechanism from Sequential to DGX

**Configuration**:
```python
# From your existing client
dgx_client = LLM_3B_Client(base_url="https://dgx-server:8193")
response = dgx_client.generate(
    query=prompt,
    model="qwen-72b",
    stream=False,
    rate=50
)
```

### 3. DocumentDB Client Integration
**Purpose**: Store conversation history, user preferences, and analytics

**Integration Points**:
- Store chat sessions and conversation context
- Cache frequent queries and responses
- Log agent performance metrics
- Manage user profiles and preferences

## Agent Responsibilities with Existing Clients

### 1. Orchestrator/Router Agent
**LLM Client**: Sequential LLM Client (Nemotron)

**Responsibilities**:
- Parse user intent using Nemotron's reasoning capabilities
- Route requests to appropriate agents
- Manage conversation context stored in DocumentDB
- Handle error recovery and fallbacks to DGX client

### 2. SQL Agent
**LLM Client**: Sequential LLM Client (Nemotron)

**Responsibilities**:
- Generate SQL queries using Nemotron
- Execute queries against MSSQL server
- Retrieve database schema information
- Handle query safety and validation
- Store query history in DocumentDB

### 3. Query Corrector Agent
**LLM Client**: DGX 3B Client (Qwen/NIM)

**Responsibilities**:
- Validate SQL syntax using Qwen's correction capabilities
- Fix syntax errors in generated queries
- Optimize query performance
- Use DGX streaming for real-time correction feedback
- Validate against database schema

### 4. Response Analyser Agent
**LLM Client**: DGX 3B Client (Qwen/NIM)

**Responsibilities**:
- Analyze query results for accuracy
- Format data for presentation using streaming
- Generate natural language explanations
- Detect anomalies in results
- Store analytics in DocumentDB

## Enhanced Data Flow with Existing Clients

### Normal Query Flow:
1. **User Request** → FastAPI Gateway
2. **FastAPI** → Orchestrator Agent
3. **Orchestrator** → Sequential LLM Client (intent classification)
4. **Orchestrator** → SQL Agent + Sequential LLM Client (query generation)
5. **SQL Agent** → Query Corrector + DGX 3B Client (validation)
6. **Query Corrector** → SQL Agent (execute corrected query)
7. **SQL Agent** → Response Analyser + DGX 3B Client (analysis)
8. **Response Analyser** → DocumentDB (store session)
9. **Response Analyser** → Orchestrator → FastAPI → User

### Error Recovery Flow:
1. If **Sequential LLM Client** fails → fallback to DGX 3B Client
2. If **DGX 3B Client** fails → retry with Sequential LLM Client
3. If query execution fails → DocumentDB logs error for analysis
4. If all clients fail → Orchestrator returns graceful error message

## Technology Stack Integration

### Existing Components
- **Sequential LLM Client**: Nemotron integration
- **DGX 3B Client**: Qwen/NIM integration  
- **DocumentDB Client**: Session storage and analytics

### New Components
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: ORM and database abstraction for MSSQL
- **PyMSSQL**: MSSQL database driver
- **Redis**: Session caching and message broker
- **Loguru**: Structured logging

## Configuration Management

### Environment Variables
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database Configuration
MSSQL_SERVER=your-server
MSSQL_PORT=1433
MSSQL_DATABASE=your-database
MSSQL_USERNAME=your-username
MSSQL_PASSWORD=your-password

# Existing LLM Client Configuration
SEQUENTIAL_LLM_BASE_URL=http://your-nemotron-server:port
DGX_3B_BASE_URL=https://your-dgx-server:8193
DGX_3B_VERIFY_SSL=false

# DocumentDB Configuration
DOCUMENTDB_BASE_URL=http://your-documentdb-server:port
DOCUMENTDB_USERNAME=your-username
DOCUMENTDB_PASSWORD=your-password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Security Considerations with Existing Clients

### Leveraging Existing Security
- **Sequential LLM Client**: SSL verification options
- **DGX 3B Client**: SSL verification and timeout controls
- **DocumentDB Client**: Token-based authentication system

### Additional Security Measures
- SQL injection prevention through parameterized queries
- Query validation before execution
- Execution time limits
- Row count limits for large result sets

## Performance Optimization

### Client-Side Optimizations
- **Sequential LLM Client**: Polling interval optimization
- **DGX 3B Client**: Streaming for real-time responses
- **DocumentDB Client**: Connection pooling and caching

### System-Level Optimizations
- Async/await throughout the stack
- Connection pooling for database and LLM clients
- Response caching in Redis and DocumentDB
- Load balancing across multiple LLM instances

## Deployment Architecture with Existing Services

### Container Deployment
```yaml
services:
  - multi-agent-api (FastAPI application)
  - redis (caching and session store)
  - sequential-llm (your existing Nemotron service)
  - dgx-3b-llm (your existing DGX service)
  - documentdb (your existing DocumentDB service)
  - mssql-database (external or containerized)
```

### Integration Points
- **Health Checks**: Use DGX client's health check functionality
- **Monitoring**: Leverage existing client logging mechanisms
- **Error Handling**: Integrate with existing client error handling
- **Authentication**: Use DocumentDB's token-based system

## Next Steps for Implementation

1. **Create LLM Client Wrappers**: Async wrappers for existing clients
2. **Implement Base Agent Class**: Using your existing patterns
3. **Agent Implementation**: Individual agent logic with client integration
4. **Orchestration**: Request routing and workflow management
5. **API Endpoints**: REST endpoints for user interaction
6. **Testing**: Integration tests with existing LLM services
7. **Documentation**: API docs and integration guides

---

**This architecture leverages your existing LLM client infrastructure while adding the multi-agent capabilities for MSSQL database interactions.**
