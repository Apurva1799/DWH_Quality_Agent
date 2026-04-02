# Project Structure

This document outlines the organized folder structure of the Multi-Agent Database Chatbot system.

##  Directory Structure

```
Multi_Agent_System/
  app/                          # Main application package
     agents/                   # Agent implementations
       __init__.py             # Agent package exports
       base.py                 # Abstract base agent class
       sql_agent.py            # SQL generation agent
       query_corrector.py      # SQL validation agent
       response_analyser.py    # Result analysis agent
       orchestrator.py         # Basic orchestrator
       enhanced_sql_agent.py   # Multi-database SQL agent
       enhanced_orchestrator.py # Enhanced orchestrator
    __init__.py                 # Application package exports
    config.py                   # Basic configuration
    config_extended.py          # Extended configuration
    database.py                 # Database layer
    llm_manager.py              # Basic LLM manager
    llm_manager_extended.py     # Enhanced LLM manager
    main.py                     # Basic FastAPI application
    main_extended.py            # Enhanced FastAPI application
  clients/                     # External client integrations
    __init__.py                 # Client package exports
    llm_clients.py              # Sequential LLM Client (Nemotron)
    dgx_3b_client.py            # DGX 3B Client (Qwen)
    documentdb_client.py        # DocumentDB Client
  config/                      # Configuration files
    __init__.py                 # Config package
    .env.example                # Basic environment template
    .env.example.extended        # Extended environment template
  docs/                        # Documentation
    __init__.py                 # Docs package
    ARCHITECTURE.md             # System architecture
    README.md                   # Basic setup guide
    README_EXTENDED.md           # Enhanced features guide
  deployments/                 # Deployment configurations
    __init__.py                 # Deployments package
    requirements.txt            # Python dependencies
  logs/                        # Runtime logs
    .gitkeep                    # Ensures directory is tracked
  scripts/                     # Utility scripts
    __init__.py                 # Scripts package
  tests/                       # Test suite
    __init__.py                 # Tests package
  .env                         # Local environment configuration
  .gitignore                   # Git ignore rules
  Makefile                     # Development commands
  PROJECT_STRUCTURE.md         # This file
  pyproject.toml               # Modern Python packaging
  setup.py                     # Legacy packaging support
  README.md                   # Project overview (symlink to docs/README.md)
```

##  Package Organization

### **Core Application (`app/`)**
- **Purpose**: Main application logic and API endpoints
- **Key Components**: Agents, configuration, database layer, LLM managers
- **Entry Points**: `main.py` (basic), `main_extended.py` (enhanced)

### **External Clients (`clients/`)**
- **Purpose**: Integration with external services
- **Components**: LLM clients, DocumentDB client
- **Note**: These are user-provided client files

### **Configuration (`config/`)**
- **Purpose**: Environment and configuration templates
- **Files**: Basic and extended configuration examples
- **Usage**: Copy to `.env` and customize

### **Documentation (`docs/`)**
- **Purpose**: All documentation files
- **Content**: Architecture, setup guides, feature documentation
- **Formats**: Markdown files

### **Deployment (`deployments/`)**
- **Purpose**: Deployment-related configurations
- **Content**: Dependencies, Docker files (to be added)
- **Usage**: Production deployment setup

### **Development Support**
- **`scripts/`**: Utility and automation scripts
- **`tests/`**: Unit and integration tests
- **`logs/`**: Runtime log files

##  Quick Start

### **1. Setup Environment**
```bash
# Copy configuration template
cp config/.env.example.extended .env

# Install dependencies
make dev-install
```

### **2. Run Application**
```bash
# Basic version
make run

# Enhanced version
make run-enhanced

# Development mode with auto-reload
make run-dev
```

### **3. Development Workflow**
```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Full development workflow
make dev
```

##  Import Structure

### **Basic Usage**
```python
from app import app, settings, llm_manager
from app.agents import SQLAgent, OrchestratorAgent
from clients import SequentialLLMClient, DocumentDBClient
```

### **Enhanced Usage**
```python
from app import enhanced_app, extended_settings, extended_llm_manager
from app.agents import EnhancedSQLAgent, EnhancedOrchestratorAgent
```

##  Configuration Hierarchy

1. **Base Configuration** (`app/config.py`)
2. **Extended Configuration** (`app/config_extended.py`)
3. **Environment Variables** (`.env` file)
4. **Runtime Overrides** (function parameters)

##  Key Features by Package

### **`app/agents/`**
- **BaseAgent**: Abstract base class with common functionality
- **SQL Agents**: Query generation and execution
- **Orchestrator**: Request routing and workflow management
- **Enhanced Versions**: Multi-database and multi-LLM support

### **`app/`**
- **LLM Managers**: Client wrapper with fallback mechanisms
- **Database Layer**: SQLAlchemy integration with connection pooling
- **API Endpoints**: FastAPI application with comprehensive endpoints

### **`clients/`**
- **External Integration**: User-provided client implementations
- **Async Wrappers**: Synchronous clients wrapped for async use
- **Error Handling**: Comprehensive error management

##  Development Guidelines

### **File Organization**
- Keep related files in the same package
- Use `__init__.py` for clean imports
- Follow naming conventions (snake_case for files, PascalCase for classes)

### **Import Best Practices**
- Import from packages, not individual files
- Use relative imports within packages
- Keep import statements organized

### **Configuration Management**
- Use environment variables for sensitive data
- Provide configuration templates
- Support multiple deployment scenarios

##  Migration from Old Structure

The old flat structure has been reorganized:

| Old Location | New Location |
|--------------|--------------|
| `llm_clients.py` | `clients/llm_clients.py` |
| `dgx_3b_client.py` | `clients/dgx_3b_client.py` |
| `documentdb_client.py` | `clients/documentdb_client.py` |
| `.env.example*` | `config/.env.example*` |
| `*.md` | `docs/*.md` |
| `requirements.txt` | `deployments/requirements.txt` |

### **Import Updates Required**

If you have existing code importing from the old structure, update imports:

```python
# Old imports
from llm_clients import LLMClient
from dgx_3b_client import LLM_3B_Client

# New imports
from clients import SequentialLLMClient, LLM_3B_Client
```

##  Next Steps

1. **Update Imports**: Modify any existing code to use new import paths
2. **Configure Environment**: Set up `.env` with your credentials
3. **Run Tests**: Verify everything works with `make test`
4. **Start Development**: Use `make run-dev` for development

This organized structure provides better maintainability, clearer separation of concerns, and easier scaling for future development.
