# Moral Duel Backend API

Blockchain-powered debate platform where users engage in moral dilemmas, vote on cases, and earn NEO-based token rewards.

## Features

- 🔐 JWT Authentication with Neo Wallet Integration
- 🤖 AI-Generated Moral Dilemmas (GPT-4)
- ⛓️ Blockchain Verdict Commitment (Neo N3)
- 💰 Smart Contract Reward Distribution (NEP-17)
- 🗳️ Voting & Arguments System
- 🏆 Leaderboard & Badges

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: SQLite + Prisma ORM
- **Cache**: Redis
- **AI**: OpenAI GPT-4
- **Blockchain**: Neo N3
- **Auth**: JWT + Neo Wallet Signature

## Setup

### Quick Start with Makefile

The easiest way to get started:

```bash
# Install dependencies and generate Prisma client
make install

# Run development server with auto-reload
make dev

# Or run in background
make start

# Stop background server
make stop

# View all available commands
make help
```

### Manual Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Add your OpenAI API key, Neo credentials, etc.
```

### 3. Initialize Database

```bash
# Generate Prisma client (or use: make db-generate)
prisma generate

# Create database (or use: make db-push)
prisma db push
```

### 4. Run Server

```bash
# Development mode with auto-reload (or use: make dev)
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Background mode with logs (or use: make start)
nohup python main.py > logs/server.log 2>&1 &
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Available Make Commands

### Setup & Installation
- `make install` - Install dependencies and generate Prisma client
- `make db-generate` - Generate Prisma client
- `make db-push` - Push database schema
- `make db-reset` - Reset database (⚠️ deletes all data)

### Development
- `make dev` - Run development server with auto-reload
- `make server` - Run production server
- `make start` - Start server in background
- `make stop` - Stop background server
- `make restart` - Restart server
- `make logs` - View server logs (when running in background)

### Background Workers
- `make workers-start` - Start background workers (Celery)
- `make workers-stop` - Stop background workers
- `make workers-restart` - Restart background workers

### Testing & Quality
- `make test` - Run all tests
- `make test-cov` - Run tests with coverage report
- `make lint` - Run linting checks
- `make format` - Format code with black

### Utilities
- `make clean` - Clean cache and temporary files
- `make help` - Show all available commands

## Project Structure

```
moral-duel-api/
├── app/
│   ├── routes/          # API endpoints
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   ├── utils/           # Utilities (auth, database)
│   ├── middleware/      # Rate limiting, etc.
│   └── config.py        # Configuration
├── prisma/
│   └── schema.prisma    # Database schema
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables
```

## API Endpoints

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - User login
- `POST /auth/wallet/connect` - Connect Neo wallet
- `GET /auth/wallet/verify` - Verify wallet

### Cases
- `GET /cases` - List all cases
- `GET /cases/:id` - Get case details
- `POST /cases` - Create case
- `POST /cases/:id/vote` - Vote on case
- `POST /cases/:id/arguments` - Submit argument

### Profile & Rewards
- `GET /profile` - User profile
- `GET /profile/rewards` - List rewards
- `POST /profile/rewards/claim` - Claim rewards

### Blockchain
- `GET /blockchain/network-info` - Network status
- `GET /blockchain/transaction/:hash` - Transaction details

## Development

### Running Tests

```bash
pytest
pytest --cov=app tests/
```

### Database Migrations

```bash
# Create migration
prisma migrate dev --name migration_name

# Apply migrations
prisma migrate deploy
```

## License

MIT
