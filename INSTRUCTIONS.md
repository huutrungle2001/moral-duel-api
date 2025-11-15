# Moral Duel - Backend Development Plan (High-Level)

## Project Overview

**Moral Duel** is a blockchain-powered debate platform where users engage in moral dilemmas, vote on cases, and earn NEO-based token rewards. An AI Oracle analyzes winning sides as a case is created. Each verdict is permanently recorded on Neo N3 blockchain, and rewards are distributed via smart contracts.

### Tech Stack
- **Backend**: Python FastAPI
- **Database**: SQLite + Redis (caching)
- **ORM**: Prisma
- **Auth**: JWT + Neo Wallet Authentication
- **AI**: OpenAI GPT-4 / Anthropic Claude / Google Gemini, SpoonOS ([Agentic OS](https://xspoonai.github.io/docs/getting-started/installation/))
- **Blockchain**: Neo N3 (@cityofzion/neon-js)
- **Smart Contracts**: NEP-17 tokens, C# contracts
- **Wallets**: NeoLine, O3, OneGate

---

## 1. Database Schema

### Core Tables
- **users**: email, password, name, neo_wallet_address, total_points
- **cases**: title, context, status, ai_verdict (hidden until closed), verdict_hash, blockchain_tx_hash, smart_contract_id, reward_pool, is_ai_generated
- **arguments**: case_id, user_id, content (max 300 chars), side, votes, is_top_3
- **user_votes**: user_id, case_id, side, voted_arguments (3 max)
- **rewards**: user_id, case_id, amount, type, status, blockchain_tx_hash, neo_wallet_address
- **badges**: name, description, criteria
- **community_posts**: user_id, content, type
- **leaderboard_cache**: user_id, rank, points, wins

---

## 2. API Endpoints (High-Level)

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - User login
- `POST /auth/wallet/connect` - Connect Neo wallet with signature verification
- `GET /auth/wallet/verify` - Check wallet connection & balance

### Cases
- `GET /cases` - List all cases (with filters)
- `GET /cases/:id` - Get case details + arguments + user vote
- `POST /cases` - Create user-submitted case (AI moderation only, no pre-verdict)
- `GET /cases/:id/blockchain` - Get blockchain verification data
- `GET /cases/:id/ai-verdict` - Get AI verdict + reasoning (closed cases only)

**Note**: AI-generated cases (with pre-committed verdicts) are created automatically every 12 hours via background job.

### Arguments & Voting
- `POST /cases/:caseId/vote` - Vote YES/NO
- `POST /cases/:caseId/arguments` - Submit argument (after voting + liking 3 args)
- `POST /arguments/:argumentId/vote` - Like an argument (max 3)
- `DELETE /arguments/:argumentId/vote` - Unlike

### Profile & Rewards
- `GET /profile` - User stats, badges, recent activity
- `GET /profile/rewards` - List rewards (pending/completed)
- `POST /profile/rewards/claim` - Claim rewards via smart contract (batch)
- `GET /profile/rewards/:id/status` - Check blockchain confirmation status

### Blockchain
- `GET /blockchain/network-info` - Neo network status
- `GET /blockchain/transaction/:txHash` - Transaction details
- `POST /blockchain/verify-verdict` - Verify verdict hash integrity

### Other
- `GET /leaderboard` - Top users by points
- `GET /community/posts` - Community feed
- `GET /earnings/info` - Reward distribution rules

---

## 3. Background Jobs

### AI Case Generator (Every 12 hours)
1. Generate new moral dilemma using GPT-4
2. Generate AI verdict BEFORE case goes live (pre-commitment)
3. Create verdict hash and commit to Neo blockchain
4. Store case with hidden verdict (revealed when closes)
5. Set case status to `active` with 24h timer

**Integrity**: Verdict is created and committed to blockchain before users vote, preventing manipulation.

### Case Closure (Every 5 min)
1. Find cases where `closes_at <= NOW()`
2. Reveal pre-committed verdict from blockchain
3. Calculate and record rewards (pending status)
4. Update case status to `closed`

### Transaction Monitor (Every 30 sec)
- Check Neo blockchain for transaction confirmations
- Update reward status: `processing` → `completed`/`failed`
- Update user total_points on success

### Leaderboard Update (Every 15 min)
- Recalculate user rankings based on total_points
- Update leaderboard_cache table

### Badge Checker (Hourly)
- Check users for badge criteria (5 wins, top 3 arguments, etc.)
- Award badges and bonus tokens

---

## 4. Blockchain Integration

### Neo Smart Contracts Required

**1. Verdict Storage Contract**
- Store verdict hashes immutably
- Methods: `commitVerdict()`, `getVerdict()`, `verifyVerdict()`

**2. NEP-17 Reward Token Contract**
- Fungible token for rewards
- Standard methods: `transfer()`, `balanceOf()`, `totalSupply()`

### Key Operations

**Commit Verdict to Blockchain:**
```typescript
// Generate verdict hash
const verdictHash = crypto.createHash('sha256')
  .update(JSON.stringify({ caseId, verdict, confidence, timestamp }))
  .digest('hex');

// Invoke smart contract
const tx = await neoContract.invoke('commitVerdict', [caseId, verdictHash, verdict]);
```

**Distribute Rewards via Smart Contract:**
```typescript
// Batch transfer NEP-17 tokens
const tx = await tokenContract.invoke('transfer', [
  platformAddress,
  userNeoAddress,
  amount,
  metadata
]);
```

### Reward Distribution Logic
- **40%** to winning side voters (only if voted correctly)
- **30%** to top 3 arguments (weighted by votes)
- **20%** to all participants
- **10%** to case creator (if ≥100 participants)

---

## 5. Business Rules

### Voting Flow
1. User votes YES/NO
2. User likes 3 arguments
3. User writes own argument (20-300 chars)
4. Vote complete → Eligible for rewards if side wins

### Case Lifecycle
```
AI-Generated Case: verdict_created → blockchain_committed → active (24h) → closed (verdict revealed)
User-Created Case: pending_moderation → active (24h) → closed (verdict generated) → blockchain_committed
```

**Key Difference**: AI cases have pre-committed verdicts for integrity; user cases generate verdicts after voting.

### Reward Claiming
- Users MUST have Neo wallet connected
- Only winning side voters get rewards
- Rewards claimed via blockchain transaction
- Platform pays GAS fees

---

## 6. Security

### Authentication
- JWT tokens (7-day expiry)
- bcrypt password hashing
- Neo wallet signature verification

### Blockchain Security
- Platform private key in secure vault (AWS Secrets Manager)
- Multi-sig for high-value operations
- Transaction replay protection
- Monitor platform wallet GAS balance

### Rate Limiting
- Auth: 5 req/min
- Voting: 10 req/min
- Case creation: 3/hour

---

## 7. Environment Variables

```bash
# Server
PORT=3000
NODE_ENV=production

# Database
DATABASE_URL=sqlite://./moralduel.db
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=<secret>

# OpenAI
OPENAI_API_KEY=<key>

# Neo Blockchain
NEO_NETWORK=TestNet
NEO_RPC_URL=https://testnet1.neo.org:443
NEO_PLATFORM_PRIVATE_KEY=<wif>
NEO_TOKEN_CONTRACT_HASH=<hash>
NEO_VERDICT_CONTRACT_HASH=<hash>
```

---

## 8. Development Phases

### Phase 1: Foundation (Week 1-2)
- Setup Node.js + TypeScript + Prisma
- Auth system + Neo wallet connection
- Basic CRUD operations

### Phase 2: Core Features (Week 3-4)
- Voting system
- Arguments submission
- AI moderation

### Phase 3: Blockchain Integration (Week 5-6)
- AI case generator (every 12 hours with pre-verdict)
- Verdict pre-commitment to blockchain
- Smart contract deployment
- Case closure with verdict reveal
- Transaction monitoring

### Phase 4: Rewards & Polish (Week 7-8)
- Smart contract reward distribution
- Reward claiming interface
- Leaderboard + badges
- Testing & deployment

---

## 9. Success Metrics

- **Wallet Connection Rate**: % users with Neo wallets
- **Reward Claim Rate**: % rewards claimed on-chain
- **Transaction Success Rate**: % successful blockchain txs
- **Case Completion Rate**: % cases reaching 100+ participants
- **User Retention**: 7-day and 30-day
- **AI Verdict Accuracy**: User satisfaction score

---

## Conclusion

This backend powers a **blockchain-transparent** debate platform where:
- ✅ AI generates ethical verdicts (pre-committed every 12h for integrity)
- ✅ Verdicts stored immutably on Neo N3 BEFORE voting begins
- ✅ Rewards distributed via NEP-17 smart contracts
- ✅ Users earn tokens directly to Neo wallets
- ✅ Anyone can verify verdict integrity on-chain

**Key Innovation**: AI-generated cases have verdicts pre-committed to blockchain before users vote, ensuring absolute integrity and preventing any possibility of manipulation. New cases created automatically every 12 hours.
