# Multi-Agent Database Chatbot

A comprehensive multi-agent system for MSSQL database interactions using on-prem LLM clients.

##  Quick Start

```bash
# Setup environment
cp config/.env.example.extended .env
# Edit .env with your credentials

# Install dependencies
make dev-install

# Run enhanced version
make run-enhanced
```

##  Project Structure

```
Multi_Agent_System/
 app/                    # Main application
    agents/            # Agent implementations
    config.py         # Configuration
    main.py           # Basic API
    main_extended.py  # Enhanced API
 clients/               # External LLM clients
 config/               # Configuration templates
 docs/                 # Documentation
 deployments/          # Deployment files
 tests/               # Test suite
```

##  Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design overview
- **[Setup Guide](docs/README.md)** - Basic installation and usage
- **[Enhanced Features](docs/README_EXTENDED.md)** - Multi-database and multi-LLM support
- **[Project Structure](PROJECT_STRUCTURE.md)** - Detailed organization guide

##  Development

```bash
# Development workflow
make dev          # Format, lint, test
make run-dev      # Run with auto-reload
make test         # Run tests
make health       # Check system health
```

##  API Access

- **Basic API**: http://localhost:8000/docs
- **Enhanced API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

##  Features

- **Multi-Database Support**: Silver, Gold, IoT, Dev databases
- **Multiple LLM Models**: Nemotron 49B/253B, DeepSeek, Llama
- **Intelligent Routing**: Automatic database and model selection
- **Conversation Management**: Session tracking and history
- **Comprehensive Monitoring**: Health checks and status endpoints

##  License

MIT License - see LICENSE file for details.
