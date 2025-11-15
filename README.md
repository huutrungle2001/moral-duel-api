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
# Generate Prisma client
prisma generate

# Create database
prisma db push
```

### 4. Run Server

```bash
# Development mode with auto-reload
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

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
