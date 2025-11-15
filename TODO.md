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
- [ ] Create user session management
- [x] Add password validation rules
- [x] Implement rate limiting for auth endpoints (5 req/min)

## Phase 2: Neo Wallet Integration

### Wallet Connection
- [ ] Research Neo N3 wallet signature verification
- [ ] Install Neo N3 Python SDK
- [ ] Build `POST /auth/wallet/connect` endpoint
- [ ] Implement Neo wallet signature verification
- [ ] Build `GET /auth/wallet/verify` endpoint
- [ ] Store Neo wallet address in user profile
- [ ] Test with NeoLine wallet
- [ ] Test with O3 wallet
- [ ] Test with OneGate wallet

### Blockchain Connection
- [ ] Set up Neo N3 TestNet connection
- [ ] Configure Neo RPC URL
- [ ] Test blockchain connectivity
- [ ] Create utility functions for Neo interactions
- [ ] Build `GET /blockchain/network-info` endpoint
- [ ] Build `GET /blockchain/transaction/:txHash` endpoint
- [ ] Implement transaction status checking
- [ ] Set up platform wallet management

## Phase 3: Core Case Management

### Case CRUD Operations
- [ ] Build `GET /cases` endpoint (list all cases with filters)
- [ ] Build `GET /cases/:id` endpoint (case details)
- [ ] Build `POST /cases` endpoint (user-submitted cases)
- [ ] Implement case status management (pending, active, closed)
- [ ] Add pagination for case listings
- [ ] Add filtering by status, date, popularity
- [ ] Add sorting options
- [ ] Build `GET /cases/:id/blockchain` endpoint
- [ ] Build `GET /cases/:id/ai-verdict` endpoint (closed cases only)

### Case Validation
- [ ] Implement case content moderation rules
- [ ] Validate case title (min/max length)
- [ ] Validate case context
- [ ] Implement rate limiting for case creation (3/hour)
- [ ] Add duplicate case detection

## Phase 4: AI Integration

### AI Service Setup
- [ ] Set up OpenAI API connection
- [ ] Create AI service abstraction layer
- [ ] Implement AI case generation prompt
- [ ] Implement AI verdict generation prompt
- [ ] Implement AI moderation for user-submitted cases
- [ ] Add confidence scoring for AI verdicts
- [ ] Test AI response quality
- [ ] Add fallback for AI service failures
- [ ] Implement AI response caching

### AI Case Generator (Background Job)
- [ ] Set up background job scheduler (APScheduler or Celery)
- [ ] Create AI case generation job (runs every 12 hours)
- [ ] Generate moral dilemma using AI
- [ ] Generate AI verdict BEFORE case goes live
- [ ] Create verdict hash (SHA-256)
- [ ] Store case with hidden verdict
- [ ] Set case timer (24 hours)
- [ ] Add job error handling and retry logic
- [ ] Add job monitoring and logging

## Phase 5: Voting System

### Vote Management
- [ ] Build `POST /cases/:caseId/vote` endpoint (YES/NO vote)
- [ ] Validate user can only vote once per case
- [ ] Track vote timestamp
- [ ] Update vote counts in real-time
- [ ] Implement rate limiting for voting (10 req/min)
- [ ] Add vote validation rules
- [ ] Prevent voting on closed cases

### Argument System
- [ ] Build `POST /arguments/:argumentId/vote` endpoint (like argument)
- [ ] Build `DELETE /arguments/:argumentId/vote` endpoint (unlike)
- [ ] Enforce max 3 argument likes per user per case
- [ ] Build `POST /cases/:caseId/arguments` endpoint
- [ ] Validate argument length (20-300 chars)
- [ ] Require user voted before submitting argument
- [ ] Require user liked 3 arguments before submitting
- [ ] Track argument vote counts
- [ ] Identify top 3 arguments by votes

## Phase 6: Blockchain Smart Contracts

### Smart Contract Development
- [ ] Write C# Verdict Storage Contract
- [ ] Implement `commitVerdict()` method
- [ ] Implement `getVerdict()` method
- [ ] Implement `verifyVerdict()` method
- [ ] Write NEP-17 Reward Token Contract
- [ ] Implement `transfer()` method
- [ ] Implement `balanceOf()` method
- [ ] Implement `totalSupply()` method
- [ ] Test smart contracts on Neo N3 TestNet
- [ ] Deploy Verdict Storage Contract
- [ ] Deploy NEP-17 Token Contract
- [ ] Store contract hashes in environment variables

### Verdict Commitment
- [ ] Implement verdict hash generation
- [ ] Create blockchain transaction builder
- [ ] Build verdict commitment function
- [ ] Invoke smart contract for verdict storage
- [ ] Store blockchain transaction hash in database
- [ ] Add transaction confirmation monitoring
- [ ] Build `POST /blockchain/verify-verdict` endpoint
- [ ] Implement verdict integrity verification

## Phase 7: Reward System

### Reward Calculation
- [ ] Implement reward pool calculation logic
- [ ] Calculate 40% to winning side voters
- [ ] Calculate 30% to top 3 arguments (weighted)
- [ ] Calculate 20% to all participants
- [ ] Calculate 10% to case creator (if ≥100 participants)
- [ ] Validate user voted on winning side
- [ ] Create reward records in database
- [ ] Set reward status (pending, processing, completed, failed)

### Reward Distribution
- [ ] Build `GET /profile/rewards` endpoint
- [ ] Build `POST /profile/rewards/claim` endpoint
- [ ] Validate user has Neo wallet connected
- [ ] Implement batch reward claiming
- [ ] Build smart contract invocation for token transfer
- [ ] Handle blockchain transaction signing
- [ ] Update reward status after transaction
- [ ] Build `GET /profile/rewards/:id/status` endpoint
- [ ] Add GAS fee estimation
- [ ] Monitor platform wallet GAS balance

## Phase 8: Background Jobs

### Case Closure Job
- [ ] Create case closure job (runs every 5 minutes)
- [ ] Find cases where `closes_at <= NOW()`
- [ ] Reveal pre-committed verdict from blockchain
- [ ] Calculate rewards for winners
- [ ] Update case status to closed
- [ ] Mark top 3 arguments
- [ ] Add job error handling
- [ ] Add job logging

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
- [ ] Build `GET /profile` endpoint
- [ ] Return user stats (wins, total_points, cases participated)
- [ ] Return badges earned
- [ ] Return recent activity
- [ ] Add profile update capabilities
- [ ] Return Neo wallet connection status
- [ ] Return reward summary

### Leaderboard
- [ ] Build `GET /leaderboard` endpoint
- [ ] Return top users by points
- [ ] Add pagination
- [ ] Add time-based filters (daily, weekly, all-time)
- [ ] Show user's current rank
- [ ] Optimize leaderboard query performance

### Community Features
- [ ] Build `GET /community/posts` endpoint
- [ ] Implement community post creation
- [ ] Add post types (discussion, achievement, etc.)
- [ ] Add pagination for community feed
- [ ] Build `GET /earnings/info` endpoint

## Phase 10: Security & Performance

### Security Implementation
- [ ] Implement rate limiting middleware
- [ ] Add input sanitization for all endpoints
- [ ] Implement SQL injection prevention
- [ ] Add CSRF protection
- [ ] Secure Neo private key storage (use environment variable)
- [ ] Implement transaction replay protection
- [ ] Add multi-sig for high-value operations
- [ ] Implement request validation schemas (Pydantic)
- [ ] Add API key authentication for admin endpoints

### Performance Optimization
- [ ] Implement Redis caching for frequently accessed data
- [ ] Cache case lists
- [ ] Cache leaderboard data
- [ ] Cache user profiles
- [ ] Add database indexes for common queries
- [ ] Optimize blockchain query batching
- [ ] Implement connection pooling
- [ ] Add response compression

## Phase 11: Testing

### Unit Tests
- [ ] Write tests for authentication service
- [ ] Write tests for case service
- [ ] Write tests for voting service
- [ ] Write tests for reward calculation
- [ ] Write tests for blockchain integration
- [ ] Write tests for AI service
- [ ] Write tests for background jobs
- [ ] Achieve 80%+ code coverage

### Integration Tests
- [ ] Test complete voting flow
- [ ] Test case lifecycle (creation → closing)
- [ ] Test reward distribution flow
- [ ] Test wallet connection flow
- [ ] Test blockchain transaction flow
- [ ] Test AI case generation flow

### End-to-End Tests
- [ ] Test complete user journey (register → vote → claim rewards)
- [ ] Test AI-generated case flow
- [ ] Test user-submitted case flow
- [ ] Test blockchain verification

## Phase 12: Deployment & Monitoring

### Deployment Setup
- [ ] Set up production server (AWS/GCP/DigitalOcean)
- [ ] Configure production environment variables
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Set up Redis instance
- [ ] Deploy Neo smart contracts to MainNet
- [ ] Configure CI/CD pipeline
- [ ] Set up Docker containers (optional)

### Monitoring & Logging
- [ ] Set up application monitoring (Sentry/DataDog)
- [ ] Set up error tracking
- [ ] Set up performance monitoring
- [ ] Monitor blockchain transaction success rate
- [ ] Monitor wallet connection rate
- [ ] Monitor reward claim rate
- [ ] Monitor AI service uptime
- [ ] Set up alerting for critical errors
- [ ] Set up log aggregation

### Documentation
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Document all endpoints
- [ ] Document authentication flow
- [ ] Document blockchain integration
- [ ] Document reward system
- [ ] Create deployment guide
- [ ] Create developer setup guide
- [ ] Document environment variables

## Phase 13: Polish & Launch

### Final Testing
- [ ] Perform security audit
- [ ] Load testing
- [ ] Stress testing background jobs
- [ ] Test with real Neo TestNet wallets
- [ ] Test all error scenarios
- [ ] Verify blockchain transaction handling

### Launch Preparation
- [ ] Set up production monitoring dashboards
- [ ] Prepare incident response plan
- [ ] Create user onboarding flow
- [ ] Test platform wallet has sufficient GAS
- [ ] Verify smart contracts on Neo MainNet
- [ ] Perform final security review
- [ ] Create launch checklist

### Post-Launch
- [ ] Monitor success metrics
- [ ] Track wallet connection rate
- [ ] Track reward claim rate
- [ ] Track transaction success rate
- [ ] Track case completion rate
- [ ] Gather user feedback
- [ ] Plan iterative improvements
