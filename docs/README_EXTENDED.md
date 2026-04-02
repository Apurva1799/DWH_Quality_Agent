# Enhanced Multi-Agent Database Chatbot

An advanced multi-agent chatbot system supporting multiple MSSQL databases and LLM models, built with FastAPI and designed for customer satisfaction analytics.

##  Enhanced Features

### **Multi-Database Support**
- **Silver DB**: Customer satisfaction data, feedback, projects
- **Gold DB**: Production customer data, analytics, reports  
- **IoT DB**: Sensor data, device information, real-time metrics
- **Dev DB**: Development and testing data

### **Multiple LLM Models**
- **Nemotron 49B**: Primary model for SQL generation and orchestration
- **Nemotron 253B**: Large model for complex queries and intent classification
- **DeepSeek R1 70B**: Alternative model for general queries
- **Llama 70B**: Fast model for simple queries

### **Intelligent Routing**
- Automatic database selection based on query context
- Smart LLM model selection based on query complexity
- Fallback mechanisms between models and databases
- Enhanced intent classification

##  Architecture

```
        
   User Request   Enhanced FastAPIEnhanced Orchestr
   (REST API)           Gateway           ator Agent       
        
                                                        
                       
                                                                                   
                                                                                   
                                    
            Enhanced SQL                  Query Corrector              Response        
            Agent (4 DBs)                   Agent                      Analyser        
             - Auto DB Sel                - Syntax Fix                 - Quality Check 
             - Smart LLM                  - Optimization               - Format        
             - Multi-Model                - Validation                 - Context       
                                    
                                                                                   
                       
                                                      
                       
                                                                                   
                                                                                   
                                    
              Nemotron 253B               Nemotron 49B                 DeepSeek R1   
             (Complex Queries)             (Primary Model)              (General Q&A)   
                                    
                                                                
                                                                
                                                       
                                                          Llama 70B    
                                                        (Fast Queries)  
                                                       
```

##  Database Configuration

### **Silver Database**
- **Server**: `afdbsrv.kalyanicorp.com`
- **Database**: `Silver_DB`
- **Purpose**: Customer satisfaction, feedback, projects
- **Access**: Read-only access for analytics

### **Gold Database**
- **Server**: `afdbsrv.kalyanicorp.com`
- **Database**: `GOLD_DB`
- **Purpose**: Production customer data, reports
- **Access**: Read-only access for analytics

### **IoT Database**
- **Server**: `sqldbsrv.kalyanicorp.com`
- **Database**: `IOTEDGEDB`
- **Purpose**: Sensor data, device metrics
- **Access**: Real-time data access

### **Development Database**
- **Server**: `sqldbDEV.kalyanicorp.com`
- **Database**: `Development`
- **Purpose**: Testing and development
- **Access**: Full development access

##  LLM Model Selection Logic

### **Query Complexity Analysis**
```python
def choose_llm_model(query):
    complexity_indicators = [
        "join", "union", "subquery", "case when", "window function",
        "partition by", "group by", "having", "aggregate"
    ]
    
    if any(indicator in query.lower() for indicator in complexity_indicators):
        return "nemotron_253b"  # Large model for complex queries
    else:
        return "nemotron_49b"   # Efficient model for simple queries
```

### **Fallback Hierarchy**
1. **Primary**: Nemotron 253B (complex) / Nemotron 49B (simple)
2. **Fallback 1**: DeepSeek R1 70B
3. **Fallback 2**: Llama 70B
4. **Final**: Error with all models unavailable

##  Quick Start

### **1. Environment Setup**

```bash
# Copy the extended configuration
cp .env.example.extended .env

# Edit with your actual credentials
nano .env
```

### **2. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **3. Place Your Client Files**

Ensure these files are in the root directory:
- `llm_clients.py` (Sequential LLM Client)
- `dgx_3b_client.py` (DGX 3B Client)
- `documentdb_client.py` (DocumentDB Client)

### **4. Start Enhanced Application**

```bash
# Start the enhanced API server
python -m app.main_extended

# Or use uvicorn directly
uvicorn app.main_extended:app --host 0.0.0.0 --port 8000 --reload
```

##  Enhanced API Endpoints

### **Core Endpoints**

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/chat` | POST | Enhanced chat with multi-database support |
| `/health` | GET | Comprehensive health check |
| `/databases` | GET | List all available databases |
| `/llm-status` | GET | Detailed LLM model status |
| `/schema/{database}` | GET | Database schema information |

### **Database Operations**

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/validate-sql` | POST | Validate SQL for specific database |
| `/conversations/{user_id}/{session_id}` | GET | Conversation history |
| `/conversations/{user_id}/{session_id}` | DELETE | Clear conversation history |

##  Usage Examples

### **1. Basic Chat with Database Selection**

```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "message": "Show me customer satisfaction from silver database",
    "user_id": "user123",
    "session_id": "session456"
})

print(response.json())
```

### **2. Database-Specific Queries**

```python
# Query Gold Database
response = requests.post("http://localhost:8000/chat", json={
    "message": "What are the top performing products in gold database?",
    "user_id": "user123",
    "session_id": "session456"
})

# Query IoT Database
response = requests.post("http://localhost:8000/chat", json={
    "message": "Show sensor data from IoT database",
    "user_id": "user123", 
    "session_id": "session456"
})
```

### **3. Get Database Information**

```python
# List all databases
response = requests.get("http://localhost:8000/databases")
print(response.json())

# Get specific database schema
response = requests.get("http://localhost:8000/schema/silver")
print(response.json())
```

### **4. LLM Model Status**

```python
# Check all LLM models
response = requests.get("http://localhost:8000/llm-status")
print(response.json())
```

##  Enhanced Workflow Examples

### **Complex Query Workflow**

1. **User**: "Show me customer satisfaction trends over the last 6 months with demographic breakdown from gold database"

2. **Orchestrator (Nemotron 253B)**:
   - Detects complex query with trends and demographics
   - Routes to Gold database
   - Selects Nemotron 253B for complex query generation

3. **SQL Agent (Gold)**:
   - Generates complex SQL with joins and aggregations
   - Uses Nemotron 253B for query generation

4. **Query Corrector (DeepSeek)**:
   - Validates complex SQL syntax
   - Optimizes for performance

5. **Response Analyser (DeepSeek)**:
   - Analyzes trends and patterns
   - Generates natural language insights

### **Simple Query Workflow**

1. **User**: "How many customers are there in silver database?"

2. **Orchestrator (Nemotron 49B)**:
   - Detects simple query
   - Routes to Silver database
   - Selects Nemotron 49B for efficiency

3. **SQL Agent (Silver)**:
   - Generates simple COUNT query
   - Uses Nemotron 49B for fast generation

##  Configuration Details

### **LLM Model Configuration**

```env
# Nemotron Models
LLM_NEMOTRON_49B=nvidia/llama-3.3-nemotron-super-49b-v1.5
BASE_URL_LLM_NEMOTRON_49B=https://10.7.30.1:8191

LLM_NEMOTRON_253B=nvidia/llama-3.1-nemotron-ultra-253b-v1
BASE_URL_LLM_NEMOTRON_253B=https://10.7.30.1:8190

# Alternative Models
LLM_DEEPSEEK_R1_70B=deepseek-r1:70b
BASE_URL_LLM_DEEPSEEK_R1_70B=https://10.7.110.82:9999
```

### **Database Configuration**

```env
# Silver Database
SQL_SILVERDB_SERVER=afdbsrv.kalyanicorp.com
SQL_SILVERDB_NAME=Silver_DB
SQL_SILVERDB_USERNAME=Silver_Reader
SQL_SILVERDB_PASSWORD=Silver_Reader@123

# Gold Database  
SQL_GOLDDB_SERVER=afdbsrv.kalyanicorp.com
SQL_GOLDDB_NAME=GOLD_DB
SQL_GOLDDB_USERNAME=Gold_Reader
SQL_GOLDDB_PASSWORD=goldreader@bfl123
```

##  Monitoring and Health

### **Comprehensive Health Check**

```bash
curl http://localhost:8000/health
```

Response includes:
- **Agent Status**: All agent health
- **LLM Clients**: Status of each model
- **Databases**: Connectivity for each database
- **DocumentDB**: Storage system status

### **LLM Model Monitoring**

```bash
curl http://localhost:8000/llm-status
```

Provides:
- **Model Information**: Name and endpoint
- **Health Status**: Available/unavailable
- **Performance**: Response times and success rates

##  Security Features

### **Database Security**
- Read-only access for production databases
- Separate credentials for each database
- SQL injection prevention
- Query validation and sanitization

### **API Security**
- Configurable CORS policies
- Session-based authentication
- Request rate limiting
- Error handling without data leakage

### **Data Privacy**
- No sensitive data in logs
- Secure credential management
- Session isolation
- Conversation encryption in DocumentDB

##  Troubleshooting

### **Common Issues**

1. **Database Connection Errors**
   ```bash
   # Check database connectivity
   curl http://localhost:8000/databases
   ```

2. **LLM Model Unavailable**
   ```bash
   # Check LLM status
   curl http://localhost:8000/llm-status
   ```

3. **Configuration Errors**
   ```bash
   # Verify environment variables
   python -c "from app.config_extended import extended_settings; print(extended_settings.dict())"
   ```

### **Debug Mode**

Enable debug mode for detailed logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

##  Advanced Features

### **Learning and Adaptation**

The system supports:
- **Few-shot learning** from DocumentDB
- **Namespace-based** knowledge organization
- **Conversation context** persistence
- **User preference** learning

### **Performance Optimization**

- **Connection pooling** for databases
- **Async processing** for all operations
- **Intelligent caching** of frequent queries
- **Load balancing** between LLM models

### **Scalability**

- **Horizontal scaling** support
- **Microservice architecture**
- **Container-ready** deployment
- **Load balancer** compatible

##  Deployment

### **Docker Deployment**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main_extended:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Docker Compose**

```yaml
version: '3.8'
services:
  enhanced-chatbot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SQL_SILVERDB_SERVER=afdbsrv.kalyanicorp.com
      - BASE_URL_LLM_NEMOTRON_49B=https://10.7.30.1:8191
      - DOCUMENTDB_BASE_URL=https://10.7.1.200:8002
    volumes:
      - ./logs:/app/logs
```

##  API Documentation

### **Interactive Documentation**

Visit `http://localhost:8000/docs` for interactive API documentation.

### **OpenAPI Specification**

Access the OpenAPI spec at `http://localhost:8000/openapi.json`.

##  Integration Examples

### **Python Client**

```python
from typing import Dict, Any
import requests

class EnhancedChatbotClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.user_id = "default_user"
        self.session_id = "default_session"
    
    def chat(self, message: str, database: str = None) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/chat",
            json={
                "message": message,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "database": database
            }
        )
        return response.json()
    
    def get_databases(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/databases")
        return response.json()
    
    def get_health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = EnhancedChatbot()

# Query different databases
silver_result = client.chat("Show customer satisfaction trends", "silver")
gold_result = client.chat("What are top products?", "gold")
iot_result = client.chat("Show sensor data", "iot")
```

##  License

This project is licensed under MIT License.

##  Support

For support and questions:
1. Check the health endpoints for system status
2. Review logs in `logs/app_extended.log`
3. Verify configuration in `.env`
4. Check API documentation at `/docs`

---

**Enhanced Multi-Agent Database Chatbot** - Your intelligent database assistant with multi-database and multi-LLM support! 
