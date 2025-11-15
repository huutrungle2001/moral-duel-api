# Moral Duel Smart Contracts

Neo N3 smart contracts for the Moral Duel platform.

## Contracts

### 1. VerdictStorage.cs
**Purpose**: Immutable storage of AI verdict hashes

**Key Features**:
- Commit verdict hash before case goes live
- Retrieve and verify verdict integrity
- Prevent tampering with AI verdicts
- Timestamped commitment records

**Methods**:
- `CommitVerdict(caseId, verdictHash, closesAt)` - Store verdict hash on blockchain
- `GetVerdictHash(caseId)` - Retrieve committed verdict hash
- `VerifyVerdict(caseId, providedHash)` - Verify hash integrity
- `GetCaseMetadata(caseId)` - Get commitment timestamp and metadata
- `MarkRevealed(caseId)` - Mark verdict as revealed after case closes

**Events**:
- `VerdictCommitted` - Emitted when verdict is committed
- `VerdictRevealed` - Emitted when verdict is marked as revealed

### 2. MoralDuelToken.cs (NEP-17)
**Purpose**: Reward token for platform participants

**Token Details**:
- **Name**: Moral Duel Token
- **Symbol**: MORAL
- **Decimals**: 8
- **Initial Supply**: 1,000,000,000 MORAL

**Standard Methods** (NEP-17):
- `Symbol()` - Get token symbol
- `Decimals()` - Get decimal places
- `TotalSupply()` - Get total token supply
- `BalanceOf(account)` - Get account balance
- `Transfer(from, to, amount, data)` - Transfer tokens

**Additional Methods**:
- `Mint(to, amount)` - Mint new tokens (authorized minters only)
- `Burn(from, amount)` - Burn tokens (reduce supply)
- `AddMinter(address)` - Add authorized minter (owner only)
- `RemoveMinter(address)` - Remove minter authorization
- `GetOwner()` - Get contract owner
- `TransferOwnership(newOwner)` - Transfer contract ownership

## Deployment

### Prerequisites
1. Install Neo SDK: `dotnet add package Neo.SmartContract.Framework`
2. Install Neo compiler: `dotnet tool install -g Neo.Compiler.CSharp`

### Compile Contracts
```bash
# Compile VerdictStorage
nccs VerdictStorage.cs

# Compile MoralDuelToken
nccs MoralDuelToken.cs
```

### Deploy to Neo N3 TestNet
```bash
# Using neo-cli
neo> deploy VerdictStorage.nef

# Using neo-express (local development)
neoxp contract deploy VerdictStorage.nef
```

### Update Environment Variables
After deployment, add contract hashes to `.env`:
```env
NEO_VERDICT_CONTRACT_HASH=0x1234567890abcdef...
NEO_TOKEN_CONTRACT_HASH=0xabcdef1234567890...
```

## Usage Examples

### Commit Verdict (from platform backend)
```csharp
// Platform backend calls this when generating AI case
var result = VerdictStorage.CommitVerdict(
    caseId: 123,
    verdictHash: "a1b2c3d4...",  // SHA-256 hash
    closesAt: 1732579200         // Unix timestamp
);
```

### Verify Verdict (anyone can call)
```csharp
// Verify verdict wasn't tampered with
bool isValid = VerdictStorage.VerifyVerdict(
    caseId: 123,
    providedHash: "a1b2c3d4..."
);
```

### Reward Distribution
```csharp
// Platform mints tokens to reward users
MoralDuelToken.Mint(
    to: userWalletAddress,
    amount: 1000_00000000  // 1000 MORAL tokens
);
```

## Reward Distribution Logic

The platform backend calculates rewards when a case closes:

**Total Pool**: Case reward pool (accumulated fees/sponsorships)

**Distribution**:
- **40%** → Users who voted for the winning side
- **30%** → Top 3 argument authors (weighted: 15%, 10%, 5%)
- **20%** → All participants (voters + arguers)
- **10%** → Case creator (if ≥100 participants)

The backend then calls `Mint()` to distribute tokens to eligible users.

## Security Considerations

### VerdictStorage
- ✅ Immutable once committed (cannot modify hash)
- ✅ Prevents double commitment for same case
- ✅ Timestamped for auditability
- ✅ Public verification (anyone can verify)

### MoralDuelToken
- ✅ Only authorized minters can mint tokens
- ✅ Owner-controlled minter authorization
- ✅ Standard NEP-17 implementation
- ✅ Transfer authorization checks
- ✅ Overflow protection in calculations

## Testing

### Local Testing with Neo-Express
```bash
# Start local blockchain
neoxp run

# Deploy contracts
neoxp contract deploy VerdictStorage.nef
neoxp contract deploy MoralDuelToken.nef

# Test verdict commitment
neoxp contract invoke VerdictStorage commitVerdict 1 "abc123..." 1732579200

# Test token transfer
neoxp contract invoke MoralDuelToken transfer <from> <to> 1000
```

### Integration with Backend
The Python backend integrates with these contracts via:
- `app/services/blockchain_service.py` - Transaction creation and monitoring
- `app/services/reward_service.py` - Reward calculation and distribution
- `app/jobs/case_generator.py` - Verdict commitment during case creation

## Gas Fees

Estimated GAS costs on Neo N3:

| Operation | Estimated GAS |
|-----------|---------------|
| Deploy VerdictStorage | ~10 GAS |
| Deploy MoralDuelToken | ~15 GAS |
| Commit Verdict | ~0.1 GAS |
| Verify Verdict | ~0.01 GAS (free read) |
| Mint Tokens | ~0.1 GAS |
| Transfer Tokens | ~0.05 GAS |

**Note**: Platform wallet must maintain sufficient GAS balance for operations.

## Upgradeability

Both contracts support upgrades via Neo's contract update mechanism:
- Update logic in `_deploy()` method
- Preserves storage during updates
- Owner-controlled upgrade process

## License

MIT License - See LICENSE file for details

## Support

For contract-related issues:
- Check Neo documentation: https://docs.neo.org
- Neo Discord: https://discord.io/neo
- GitHub Issues: Submit bugs/feature requests
