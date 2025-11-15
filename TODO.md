# Moral Duel Backend - Implementation TODO

## Phase 1: Project Setup & Foundation

### Environment Setup
- [x] Initialize Python FastAPI project structure
- [x] Set up virtual environment and dependencies (FastAPI, uvicorn, pydantic)
- [x] Configure environment variables (.env file)
- [x] Install SQLite and Redis
- [x] Install Prisma ORM for Python
- [x] Set up project folder structure (routes, models, services, utils)
- [x] Configure CORS and middleware
- [x] Set up logging configuration

### Database Setup
- [x] Create Prisma schema file
- [x] Define `users` table schema
- [x] Define `cases` table schema
- [x] Define `arguments` table schema
- [x] Define `user_votes` table schema
- [x] Define `rewards` table schema
- [x] Define `badges` table schema
- [x] Define `community_posts` table schema
- [x] Define `leaderboard_cache` table schema
- [x] Run Prisma migrations
- [ ] Set up Redis connection and configuration (optional, server runs without it)
- [ ] Create database seed data for testing

### Authentication System
- [x] Implement JWT token generation and validation
- [x] Create password hashing utilities (bcrypt)
- [x] Build `POST /auth/register` endpoint
- [x] Build `POST /auth/login` endpoint
- [x] Implement JWT authentication middleware
- [x] Create user session management
- [x] Add password validation rules
- [x] Implement rate limiting for auth endpoints (5 req/min)

## Phase 2: Neo Wallet Integration

### Wallet Connection
- [x] Research Neo N3 wallet signature verification
- [x] Install Neo N3 Python SDK (neo-mamba)
- [x] Build `POST /auth/wallet/connect` endpoint
- [x] Implement Neo wallet signature verification
- [x] Build `GET /auth/wallet/verify` endpoint
- [x] Store Neo wallet address in user profile
- [ ] Test with NeoLine wallet
- [ ] Test with O3 wallet
- [ ] Test with OneGate wallet

### Blockchain Connection
- [x] Set up Neo N3 TestNet connection
- [x] Configure Neo RPC URL
- [x] Test blockchain connectivity
- [x] Create utility functions for Neo interactions
- [x] Build `GET /blockchain/network-info` endpoint
- [x] Build `GET /blockchain/transaction/:txHash` endpoint
- [x] Implement transaction status checking
- [ ] Set up platform wallet management (requires private key configuration)

## Phase 3: Core Case Management

### Case CRUD Operations
- [x] Build `GET /cases` endpoint (list all cases with filters)
- [x] Build `GET /cases/:id` endpoint (case details)
- [x] Build `POST /cases` endpoint (user-submitted cases)
- [x] Implement case status management (pending, active, closed)
- [x] Add pagination for case listings
- [x] Add filtering by status, date, popularity
- [x] Add sorting options
- [x] Build `GET /cases/:id/blockchain` endpoint
- [x] Build `GET /cases/:id/ai-verdict` endpoint (closed cases only)

### Case Validation
- [x] Implement case content moderation rules
- [x] Validate case title (min/max length)
- [x] Validate case context
- [ ] Implement rate limiting for case creation (3/hour)
- [ ] Add duplicate case detection

## Phase 4: AI Integration

### AI Service Setup
- [x] Set up OpenAI API connection
- [x] Create AI service abstraction layer
- [x] Implement AI case generation prompt
- [x] Implement AI verdict generation prompt
- [x] Implement AI moderation for user-submitted cases
- [x] Add confidence scoring for AI verdicts
- [ ] Test AI response quality
- [ ] Add fallback for AI service failures
- [ ] Implement AI response caching

### AI Case Generator (Background Job)
- [x] Set up background job scheduler (APScheduler or Celery)
- [x] Create AI case generation job (runs every 12 hours)
- [x] Generate moral dilemma using AI
- [x] Generate AI verdict BEFORE case goes live
- [x] Create verdict hash (SHA-256)
- [x] Commit verdict hash to blockchain
- [x] Store case with hidden verdict and blockchain TX hash
- [x] Set case timer (24 hours)
- [x] Add job error handling and retry logic
- [x] Add job monitoring and logging

## Phase 5: Voting System

### Vote Management
- [x] Build `POST /cases/:caseId/vote` endpoint (YES/NO vote)
- [x] Validate user can only vote once per case
- [x] Track vote timestamp
- [x] Update vote counts in real-time
- [ ] Implement rate limiting for voting (10 req/min)
- [x] Add vote validation rules
- [x] Prevent voting on closed cases

### Argument System
- [x] Build `POST /arguments/:argumentId/vote` endpoint (like argument)
- [x] Build `DELETE /arguments/:argumentId/vote` endpoint (unlike)
- [x] Enforce max 3 argument likes per user per case
- [x] Build `POST /cases/:caseId/arguments` endpoint
- [x] Validate argument length (20-300 chars)
- [x] Require user voted before submitting argument
- [x] Require user liked 3 arguments before submitting
- [x] Track argument vote counts
- [x] Identify top 3 arguments by votes (in case closure job)

## Phase 6: Blockchain Smart Contracts

### Smart Contract Development
- [x] Write C# Verdict Storage Contract
- [x] Implement `commitVerdict()` method
- [x] Implement `getVerdict()` method
- [x] Implement `verifyVerdict()` method
- [x] Write NEP-17 Reward Token Contract
- [x] Implement `transfer()` method
- [x] Implement `balanceOf()` method
- [x] Implement `totalSupply()` method
- [x] Integrate Neo SDK for contract invocation
- [x] Build wallet service for signature verification
- [ ] Test smart contracts on Neo N3 TestNet (requires deployment)
- [ ] Deploy Verdict Storage Contract (requires setup)
- [ ] Deploy NEP-17 Token Contract (requires setup)
- [ ] Store contract hashes in environment variables

### Verdict Commitment
- [x] Implement verdict hash generation
- [x] Create blockchain transaction builder
- [x] Build verdict commitment function
- [x] Invoke smart contract for verdict storage (SDK integrated)
- [x] Store blockchain transaction hash in database
- [ ] Add transaction confirmation monitoring (background job)
- [x] Build `POST /blockchain/verify-verdict` endpoint
- [x] Implement verdict integrity verification

## Phase 7: Reward System

### Reward Calculation
- [x] Implement reward pool calculation logic
- [x] Calculate 40% to winning side voters
- [x] Calculate 30% to top 3 arguments (weighted)
- [x] Calculate 20% to all participants
- [x] Calculate 10% to case creator (if ≥100 participants)
- [x] Validate user voted on winning side
- [x] Create reward records in database
- [x] Set reward status (pending, processing, completed, failed)

### Reward Distribution
- [x] Build `GET /profile/rewards` endpoint
- [x] Build `POST /profile/rewards/claim` endpoint
- [x] Validate user has Neo wallet connected
- [x] Implement batch reward claiming
- [ ] Build smart contract invocation for token transfer (requires Neo SDK)
- [ ] Handle blockchain transaction signing (requires Neo SDK)
- [ ] Update reward status after transaction (monitoring job needed)
- [x] Build `GET /profile/rewards/:id/status` endpoint
- [ ] Add GAS fee estimation (requires Neo SDK)
- [ ] Monitor platform wallet GAS balance

## Phase 8: Background Jobs

### Case Closure Job
- [x] Create case closure job (runs every 5 minutes)
- [x] Find cases where `closes_at <= NOW()`
- [x] Reveal pre-committed verdict from blockchain
- [x] Calculate rewards for winners
- [x] Update case status to closed
- [x] Mark top 3 arguments
- [x] Add job error handling
- [x] Add job logging


### Case Creation Job
- [ ] Create case job (runs every 12 hours)
- [ ] Scan Reddit for hot topics
- [ ] Create a case to match that topic
- [ ] Generate a verdict and commit the case and verdict to the chain
- [ ] Update the cases table

### Transaction Monitor Job
- [ ] Create transaction monitor job (runs every 30 seconds)
- [ ] Query Neo blockchain for pending transactions
- [ ] Check transaction confirmations
- [ ] Update reward status (processing → completed/failed)
- [ ] Update user total_points on success
- [ ] Retry failed transactions
- [ ] Add alert for transaction failures

### Leaderboard Update Job
- [ ] Create leaderboard update job (runs every 15 minutes)
- [ ] Calculate user rankings by total_points
- [ ] Update leaderboard_cache table
- [ ] Add ties handling
- [ ] Optimize query performance

### Badge Checker Job
- [ ] Create badge checker job (runs hourly)
- [ ] Define badge criteria logic
- [ ] Check for 5 wins badge
- [ ] Check for top 3 arguments badge
- [ ] Check for participation badges
- [ ] Award badges to qualifying users
- [ ] Award bonus tokens for badges
- [ ] Prevent duplicate badge awards

## Phase 9: Profile & Leaderboard

### User Profile
- [x] Build `GET /profile` endpoint
- [x] Return user stats (wins, total_points, cases participated)
- [ ] Return badges earned
- [x] Return recent activity
- [ ] Add profile update capabilities
- [ ] Return Neo wallet connection status
- [ ] Return reward summary
- [x] Build `GET /profile/stats` endpoint (detailed statistics)

### Leaderboard
- [x] Build `GET /leaderboard` endpoint
- [x] Return top users by points
- [x] Add pagination
- [x] Add time-based filters (daily, weekly, all-time)
- [ ] Show user's current rank
- [x] Optimize leaderboard query performance

### Community Features
- [ ] Build `GET /community/posts` endpoint
- [ ] Implement community post creation
- [ ] Add post types (discussion, achievement, etc.)
- [ ] Add pagination for community feed
- [ ] Build `GET /earnings/info` endpoint

## Phase 10: Testing

### Integration Tests
- [ ] Test complete voting flow
- [ ] Test case lifecycle (creation → closing)
- [ ] Test reward distribution flow
- [ ] Test wallet connection flow
- [ ] Test blockchain transaction flow
- [ ] Test AI case generation flow