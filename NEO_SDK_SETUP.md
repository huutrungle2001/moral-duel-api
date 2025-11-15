# Neo N3 SDK Integration Guide

This document explains how to set up and use the Neo N3 SDK integration in the Moral Duel API.

## Overview

The Moral Duel platform integrates with Neo N3 blockchain to:
- **Store verdict hashes immutably** on the blockchain
- **Verify case verdicts** cannot be tampered with
- **Distribute MORAL token rewards** to users
- **Connect Neo wallets** for enhanced security

## Installation

### 1. Install Neo SDK Dependencies

The required packages are already in `requirements.txt`:

```bash
pip install neo-mamba>=2.0.0
pip install neo3-boa>=1.3.0
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "from neo3.api import noderpc; print('✓ Neo SDK installed')"
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Neo N3 Configuration
NEO_RPC_URL=https://testnet1.neo.org:443
NEO_NETWORK=testnet
NEO_PLATFORM_ADDRESS=NXXXxxxxxYourAddressHerexxxxXXXX
NEO_PLATFORM_PRIVATE_KEY=your_private_key_in_WIF_format

# Smart Contract Hashes (after deployment)
NEO_VERDICT_CONTRACT_HASH=0xYourVerdictContractHash
NEO_TOKEN_CONTRACT_HASH=0xYourTokenContractHash
```

### Getting Started Without Full Configuration

The system gracefully degrades:
- **No RPC URL**: Uses mock transactions for development
- **No Private Key**: Read-only blockchain access
- **No Contracts**: Simulated contract calls

This allows development and testing without a fully configured blockchain.

## Services

### 1. Neo SDK Service (`neo_sdk_service.py`)

Core Neo blockchain operations:

```python
from app.services.neo_sdk_service import neo_sdk_service

# Check if SDK is available
if neo_sdk_service.enabled:
    # Commit verdict to contract
    result = await neo_sdk_service.commit_verdict(
        case_id=1,
        verdict_hash="abc123...",
        timestamp=1234567890
    )
    
    # Verify verdict
    verification = await neo_sdk_service.verify_verdict(
        case_id=1,
        verdict_hash="abc123..."
    )
    
    # Get network info
    info = await neo_sdk_service.get_network_info()
```

**Features:**
- Smart contract invocation
- Transaction building and signing
- Wallet management
- Network queries

### 2. Blockchain Service (`blockchain_service.py`)

High-level blockchain integration:

```python
from app.services.blockchain_service import blockchain_service

# Commit verdict (with fallback to simulation)
result = await blockchain_service.commit_verdict_hash(
    case_id=1,
    verdict_hash="abc123...",
    verdict="YES",
    closes_at=datetime.now()
)

# Get network info
network_info = await blockchain_service.get_network_info()

# Verify verdict
verification = await blockchain_service.verify_verdict(
    case_id=1,
    verdict_hash="abc123...",
    blockchain_tx_hash="0xabcd..."
)
```

**Features:**
- Auto-fallback to simulation mode
- Transaction monitoring
- Verdict verification
- Network status checking

### 3. Wallet Service (`wallet_service.py`)

Neo wallet operations:

```python
from app.services.wallet_service import wallet_service

# Verify signature
verification = wallet_service.verify_signature(
    neo_address="NXXxxxxx...",
    message="Connect wallet to Moral Duel",
    signature="base64_signature..."
)

# Validate address
validation = wallet_service.validate_address("NXXxxxxx...")

# Get balance
balance = await wallet_service.get_balance("NXXxxxxx...")
```

**Features:**
- Signature verification for wallet connection
- Address validation
- Balance queries (NEO, GAS, custom tokens)

## API Endpoints

### Wallet Connection

**POST `/auth/wallet/connect`**

Connect a Neo wallet to user account:

```bash
curl -X POST http://localhost:8000/auth/wallet/connect \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "neo_address": "NXXxxxxx...",
    "signature": "base64_signature...",
    "message": "Connect wallet to Moral Duel"
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Neo wallet successfully connected",
  "neo_address": "NXXxxxxx...",
  "user_id": 1,
  "verification": {
    "verified": true,
    "address": "NXXxxxxx..."
  }
}
```

### Wallet Verification

**GET `/auth/wallet/verify`**

Verify wallet connection and get balance:

```bash
curl -X GET http://localhost:8000/auth/wallet/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "connected": true,
  "neo_address": "NXXxxxxx...",
  "validation": {
    "valid": true,
    "address": "NXXxxxxx...",
    "script_hash": "0x..."
  },
  "balance": {
    "available": true,
    "balances": {
      "NEO": "10",
      "GAS": "5.5",
      "MORAL": "1000"
    }
  }
}
```

### Blockchain Info

**GET `/blockchain/network-info`**

Get Neo network status:

```bash
curl http://localhost:8000/blockchain/network-info
```

### Transaction Lookup

**GET `/blockchain/transaction/{tx_hash}`**

Get transaction details:

```bash
curl http://localhost:8000/blockchain/transaction/0xabcd1234...
```

### Verdict Verification

**POST `/blockchain/verify-verdict`**

Verify verdict integrity:

```bash
curl -X POST http://localhost:8000/blockchain/verify-verdict \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "verdict_hash": "abc123...",
    "blockchain_tx_hash": "0xabcd..."
  }'
```

## Smart Contract Deployment

### Prerequisites

1. Install Neo CLI tools
2. Fund your testnet account (get TestNet GAS from faucet)
3. Compile contracts

### Deploy Verdict Storage Contract

```bash
cd contracts
neo-express contract deploy VerdictStorage.nef \
  --wallet your_wallet.json \
  --address NXXxxxxx...
```

### Deploy MORAL Token Contract

```bash
neo-express contract deploy MoralDuelToken.nef \
  --wallet your_wallet.json \
  --address NXXxxxxx...
```

### Update Environment

After deployment, update `.env`:

```env
NEO_VERDICT_CONTRACT_HASH=0xYourDeployedContractHash
NEO_TOKEN_CONTRACT_HASH=0xYourTokenContractHash
```

## Testing

### Test Neo SDK Availability

```python
from app.services.neo_sdk_service import neo_sdk_service

print(f"SDK Enabled: {neo_sdk_service.enabled}")
print(f"RPC URL: {neo_sdk_service.rpc_url}")
print(f"Network: {neo_sdk_service.network}")
```

### Test Wallet Connection

```bash
python app/testing/test_wallet.py
```

### Test Blockchain Integration

```bash
python app/testing/test_blockchain.py
```

## Development Modes

### Mock Mode (No Configuration)

When blockchain isn't configured:
- Verdict commitments generate deterministic mock transaction hashes
- All operations succeed with simulated results
- Perfect for development without blockchain access

### Read-Only Mode (RPC Only)

With RPC URL but no private key:
- Can query blockchain state
- Can verify transactions
- Cannot create new transactions

### Full Mode (Complete Configuration)

With RPC URL and private key:
- Full transaction creation
- Smart contract invocation
- Reward distribution
- Wallet operations

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Moral Duel API                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Blockchain  │  │   Neo SDK    │  │   Wallet    │ │
│  │   Service    │──│   Service    │  │  Service    │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│         │                  │                 │         │
│         └──────────────────┴─────────────────┘         │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │    Neo N3 TestNet       │
              ├─────────────────────────┤
              │  - VerdictStorage       │
              │  - MoralDuelToken       │
              │  - Native NEO/GAS       │
              └─────────────────────────┘
```

## Troubleshooting

### Issue: "Neo SDK not available"

**Solution:** Install neo-mamba:
```bash
pip install neo-mamba>=2.0.0
```

### Issue: "Blockchain service disabled"

**Solution:** Check `.env` configuration:
```env
NEO_RPC_URL=https://testnet1.neo.org:443
NEO_PLATFORM_ADDRESS=NXXxxxxx...
```

### Issue: "Cannot import name 'noderpc'"

**Solution:** Update import statement:
```python
from neo3.api import noderpc  # Correct
# NOT: from neo3.api.wrappers import ...
```

### Issue: "Signature verification failed"

**Causes:**
- Invalid signature format (must be base64)
- Wrong message signed
- Address doesn't match signature

**Debug:**
```python
from app.services.wallet_service import wallet_service

result = wallet_service.verify_signature(
    neo_address="NXXxxxxx...",
    message="exact_message_that_was_signed",
    signature="base64_signature..."
)
print(result)
```

## Best Practices

1. **Always use TestNet first** - Never test on MainNet
2. **Keep private keys secure** - Never commit to version control
3. **Handle failures gracefully** - Network issues are common
4. **Monitor gas costs** - Track transaction fees
5. **Verify contracts** - Audit before deploying
6. **Test signature verification** - Critical for security
7. **Use environment variables** - For all configuration

## Resources

- [Neo N3 Documentation](https://docs.neo.org/)
- [neo-mamba GitHub](https://github.com/CityOfZion/neo-mamba)
- [Neo TestNet Faucet](https://neowish.ngd.network/)
- [Neo Smart Contract Examples](https://github.com/neo-project/examples)

## Next Steps

1. **Deploy Smart Contracts**
   - Compile VerdictStorage.cs
   - Deploy to TestNet
   - Update contract hashes

2. **Test Wallet Integration**
   - Connect with NeoLine
   - Test signature verification
   - Verify balance queries

3. **Implement Full Flow**
   - Create case with verdict commitment
   - Wait for case closure
   - Verify verdict on blockchain
   - Distribute rewards

4. **Monitor and Optimize**
   - Track transaction success rates
   - Monitor gas consumption
   - Optimize contract calls

## Support

For issues or questions:
1. Check logs: `tail -f server.log`
2. Test SDK: `python -c "from app.services.neo_sdk_service import neo_sdk_service; print(neo_sdk_service.enabled)"`
3. Review Neo documentation
4. Check TestNet status: https://neotube.io/testnet
