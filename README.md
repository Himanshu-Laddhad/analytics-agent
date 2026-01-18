# Analytics Agent 🤖📊

An intelligent analytics agent that converts natural language questions into safe SQL queries, executes them on a live database, and returns interactive visualizations.

## 🎯 Features

- **Natural Language to SQL**: Ask questions in plain English
- **Multi-Agent Architecture**: LangGraph-orchestrated workflow
- **SQL Safety**: Multi-layered protection against destructive queries
- **Interactive Visualizations**: Plotly-powered charts
- **Production-Ready**: Docker, Redis caching, OpenTelemetry observability

## 🏗️ Architecture
```
User → Streamlit UI → FastAPI → LangGraph Agents → PostgreSQL
                                      ↓
                                  Redis Cache
                                      ↓
                              OpenTelemetry → Jaeger
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- Python 3.11+ (for local development)

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd analytics-agent
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the services**
- API Documentation: http://localhost:8000/docs
- Jaeger Tracing UI: http://localhost:16686
- Streamlit Frontend: http://localhost:8501 (coming soon)

### API Endpoints

- `GET /health` - System health check
- `GET /schema` - Database schema information
- `POST /query` - Process natural language query

## 📁 Project Structure
```
analytics-agent/
├── backend/              # FastAPI + Agents
│   ├── app/
│   │   ├── main.py      # API entry point
│   │   ├── config.py    # Configuration
│   │   ├── database.py  # DB connections
│   │   ├── agents/      # LangGraph agents
│   │   ├── safety/      # SQL validation
│   │   └── observability/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Streamlit UI (coming soon)
├── docker-compose.yml
└── init.sql             # Sample database
```

## 🛡️ Safety Features

1. **Read-Only Database User**: Agent cannot modify data
2. **Query Timeout**: 30-second execution limit
3. **AST Validation**: SQLGlot parsing ensures only SELECT queries
4. **Row Limits**: Maximum 10,000 rows per query
5. **Join Limits**: Maximum 3 table joins

## 🔧 Development

### Running Tests (Coming Soon)
```bash
pytest backend/tests/
```

### Viewing Logs
```bash
docker-compose logs -f backend
```

### Rebuilding After Changes
```bash
docker-compose down
docker-compose up --build
```

## 📊 Sample Queries

Once running, try these example queries:

- "What were the top 5 products by revenue last month?"
- "Show me daily order trends for the past week"
- "Which product category has the highest average order value?"

## 🚢 Deployment

### Railway (Recommended)

1. Create Railway project
2. Provision PostgreSQL and Redis
3. Add environment variables from `.env.example`
4. Deploy backend service
5. Deploy frontend service

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions (coming soon).

## 🧪 Current Status

- [x] Phase 1: System Foundations
- [ ] Phase 2: Agent Orchestration
- [ ] Phase 3: SQL Safety
- [ ] Phase 4: Data Interpretation
- [ ] Phase 5: Visualization Intelligence
- [ ] Phase 6: Performance & Caching
- [ ] Phase 7: Observability
- [ ] Phase 8: UI Integration
- [ ] Phase 9: Deployment

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Contact

Your Name - your.email@example.com