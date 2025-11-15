"""
Neo SDK Service - Real blockchain integration using neo-mamba

This service provides:
- Smart contract invocation
- Transaction building and signing
- Wallet management
- Contract deployment helpers
"""
import logging
import hashlib
import json
from typing import Dict, Optional, Any
from datetime import datetime

try:
    from neo3.api import noderpc
    from neo3.wallet import wallet
    from neo3.core import cryptography, types
    from neo3.contracts import contract, abi
    from neo3.network import payloads
    NEO_SDK_AVAILABLE = True
except ImportError:
    NEO_SDK_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class NeoSDKService:
    """Service for Neo N3 SDK operations"""
    
    def __init__(self):
        """Initialize Neo SDK service"""
        self.enabled = NEO_SDK_AVAILABLE
        self.rpc_url = settings.NEO_RPC_URL
        self.network = settings.NEO_NETWORK
        self.platform_address = settings.NEO_PLATFORM_ADDRESS
        self.verdict_contract_hash = settings.NEO_VERDICT_CONTRACT_HASH
        self.token_contract_hash = settings.NEO_TOKEN_CONTRACT_HASH
        
        self.client = None
        self.wallet_account = None
        
        if not self.enabled:
            logger.warning("Neo SDK not available - install neo-mamba package")
            return
        
        # Check configuration
        configured = bool(
            self.rpc_url and not self.rpc_url.startswith("your-") and
            self.platform_address and not self.platform_address.startswith("your-")
        )
        
        if not configured:
            logger.warning("Neo SDK available but not configured")
            self.enabled = False
            return
        
        try:
            # Initialize RPC client
            self.client = noderpc.NeoRpcClient(host=self.rpc_url)
            
            # Load wallet if private key is configured
            private_key_wif = getattr(settings, 'NEO_PLATFORM_PRIVATE_KEY', None)
            if private_key_wif and not private_key_wif.startswith("your-"):
                self.wallet_account = self._load_wallet(private_key_wif)
                if self.wallet_account:
                    logger.info(f"✓ Neo SDK wallet loaded: {self.platform_address}")
                else:
                    logger.warning("Failed to load wallet - transactions will not be signed")
            else:
                logger.warning("No private key configured - read-only mode")
            
            logger.info(f"✓ Neo SDK initialized: {self.network} @ {self.rpc_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo SDK: {str(e)}")
            self.enabled = False
    
    def _load_wallet(self, private_key_wif: str) -> Optional[Any]:
        """
        Load wallet from WIF private key
        
        Args:
            private_key_wif: Private key in WIF format
            
        Returns:
            Wallet account or None
        """
        try:
            # Create keypair from WIF
            key_pair = cryptography.KeyPair.from_wif(private_key_wif)
            
            # Create account
            script_hash = types.UInt160.from_string(self.platform_address)
            account = wallet.Account(script_hash=script_hash, key_pair=key_pair)
            
            return account
            
        except Exception as e:
            logger.error(f"Failed to load wallet: {str(e)}")
            return None
    
    async def invoke_contract(
        self,
        contract_hash: str,
        method: str,
        params: list,
        signer_account: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Invoke a smart contract method
        
        Args:
            contract_hash: Contract script hash (0x...)
            method: Method name to invoke
            params: List of parameters
            signer_account: Account to sign transaction (uses platform wallet if None)
            
        Returns:
            Transaction result
        """
        if not self.enabled:
            raise Exception("Neo SDK not initialized")
        
        if not self.client:
            raise Exception("RPC client not available")
        
        try:
            logger.info(f"Invoking contract {contract_hash[:10]}... method: {method}")
            
            # Parse contract hash
            contract_script_hash = types.UInt160.from_string(contract_hash)
            
            # Use platform wallet if no signer provided
            if signer_account is None:
                if not self.wallet_account:
                    raise Exception("No wallet configured for signing")
                signer_account = self.wallet_account
            
            # Build invocation script
            # Note: This is a simplified version - actual implementation
            # needs proper parameter encoding based on contract ABI
            
            # For now, return structure for future implementation
            result = {
                "success": False,
                "message": "Contract invocation requires full SDK integration",
                "contract": contract_hash,
                "method": method,
                "params": params,
                "note": "Use neo3-python or neo-mamba to build and sign transactions"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Contract invocation failed: {str(e)}")
            raise
    
    async def commit_verdict(
        self,
        case_id: int,
        verdict_hash: str,
        timestamp: int
    ) -> Dict[str, Any]:
        """
        Commit verdict to VerdictStorage contract
        
        Args:
            case_id: Case ID
            verdict_hash: SHA-256 hash of verdict
            timestamp: Unix timestamp
            
        Returns:
            Transaction details
        """
        if not self.enabled or not self.verdict_contract_hash:
            raise Exception("Verdict contract not configured")
        
        try:
            # Invoke commitVerdict(caseId: int, verdictHash: string, timestamp: int)
            result = await self.invoke_contract(
                contract_hash=self.verdict_contract_hash,
                method="commitVerdict",
                params=[case_id, verdict_hash, timestamp]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to commit verdict: {str(e)}")
            raise
    
    async def verify_verdict(
        self,
        case_id: int,
        verdict_hash: str
    ) -> Dict[str, Any]:
        """
        Verify verdict from contract storage
        
        Args:
            case_id: Case ID
            verdict_hash: Expected verdict hash
            
        Returns:
            Verification result
        """
        if not self.enabled or not self.verdict_contract_hash:
            return {"verified": False, "reason": "Verdict contract not configured"}
        
        try:
            # Invoke getVerdictHash(caseId: int) -> string
            # Note: This would need contract state query
            
            result = {
                "verified": False,
                "message": "Contract state query requires additional implementation",
                "case_id": case_id,
                "expected_hash": verdict_hash
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Verdict verification failed: {str(e)}")
            return {"verified": False, "error": str(e)}
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction status from blockchain
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details
        """
        if not self.enabled or not self.client:
            return {"status": "unavailable", "message": "RPC client not initialized"}
        
        try:
            # Query transaction
            tx_hash_bytes = types.UInt256.from_string(tx_hash)
            
            # Use RPC to get transaction
            # Note: Actual implementation depends on neo-mamba API
            result = await self.client.get_raw_transaction(tx_hash_bytes.to_str())
            
            return {
                "status": "confirmed" if result else "not_found",
                "tx_hash": tx_hash,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to get transaction: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_network_info(self) -> Dict[str, Any]:
        """
        Get network information
        
        Returns:
            Network details
        """
        if not self.enabled or not self.client:
            return {
                "available": False,
                "message": "Neo SDK not initialized"
            }
        
        try:
            # Get block count
            block_count = await self.client.get_block_count()
            
            # Get version
            version = await self.client.get_version()
            
            return {
                "available": True,
                "network": self.network,
                "rpc_url": self.rpc_url,
                "block_height": block_count,
                "version": version,
                "verdict_contract": self.verdict_contract_hash,
                "token_contract": self.token_contract_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to get network info: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }


# Global SDK service instance
neo_sdk_service = NeoSDKService()
