using Neo;
using Neo.SmartContract;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Native;
using Neo.SmartContract.Framework.Services;
using System;
using System.ComponentModel;
using System.Numerics;

namespace MoralDuelContracts
{
    /// <summary>
    /// Moral Duel Reward Token (NEP-17 Standard)
    /// 
    /// Purpose: Distribute rewards to users who participate in moral debates
    /// 
    /// Token Economics:
    /// - Rewards for correct predictions
    /// - Rewards for top-rated arguments
    /// - Rewards for participation
    /// - Rewards for case creation
    /// 
    /// NEP-17 Standard Implementation:
    /// - Transfer tokens between addresses
    /// - Check balances
    /// - Total supply tracking
    /// </summary>
    [DisplayName("MoralDuelToken")]
    [ManifestExtra("Author", "Moral Duel Team")]
    [ManifestExtra("Email", "dev@moralduel.com")]
    [ManifestExtra("Description", "Reward token for Moral Duel platform")]
    [SupportedStandards("NEP-17")]
    [ContractPermission("*", "onNEP17Payment")]
    public class MoralDuelToken : SmartContract
    {
        // Token settings
        private static readonly string TokenName = "Moral Duel Token";
        private static readonly string TokenSymbol = "MORAL";
        private static readonly byte Decimals = 8;
        private static readonly BigInteger InitialSupply = 1_000_000_000_00000000; // 1 billion tokens

        // Storage prefixes
        private static readonly byte[] BalancePrefix = new byte[] { 0x01 };
        private static readonly byte[] SupplyKey = new byte[] { 0x02 };
        private static readonly byte[] OwnerKey = new byte[] { 0x03 };
        private static readonly byte[] MinterPrefix = new byte[] { 0x04 };

        // NEP-17 Transfer event
        [DisplayName("Transfer")]
        public static event Action<UInt160, UInt160, BigInteger> OnTransfer;

        /// <summary>
        /// Initialize the contract
        /// </summary>
        public static void _deploy(object data, bool update)
        {
            if (!update)
            {
                // Set deployer as owner
                UInt160 owner = (UInt160)Runtime.ExecutingScriptHash;
                Storage.Put(Storage.CurrentContext, OwnerKey, owner);
                
                // Set initial supply
                Storage.Put(Storage.CurrentContext, SupplyKey, InitialSupply);
                
                // Give initial supply to owner
                ByteString balanceKey = BalancePrefix + owner;
                Storage.Put(Storage.CurrentContext, balanceKey, InitialSupply);
                
                // Emit transfer event
                OnTransfer(null, owner, InitialSupply);
            }
        }

        /// <summary>
        /// Get token symbol
        /// </summary>
        [Safe]
        public static string Symbol() => TokenSymbol;

        /// <summary>
        /// Get token decimals
        /// </summary>
        [Safe]
        public static byte Decimals() => Decimals;

        /// <summary>
        /// Get total token supply
        /// </summary>
        [Safe]
        public static BigInteger TotalSupply()
        {
            return (BigInteger)Storage.Get(Storage.CurrentContext, SupplyKey);
        }

        /// <summary>
        /// Get balance of an address
        /// </summary>
        [Safe]
        public static BigInteger BalanceOf(UInt160 account)
        {
            if (!IsValidAddress(account))
                throw new Exception("Invalid address");

            ByteString key = BalancePrefix + account;
            ByteString value = Storage.Get(Storage.CurrentContext, key);
            
            return value != null ? (BigInteger)value : 0;
        }

        /// <summary>
        /// Transfer tokens from one address to another
        /// NEP-17 Standard method
        /// </summary>
        public static bool Transfer(UInt160 from, UInt160 to, BigInteger amount, object data)
        {
            // Validate inputs
            if (!IsValidAddress(from) || !IsValidAddress(to))
                throw new Exception("Invalid address");

            if (amount < 0)
                throw new Exception("Amount cannot be negative");

            if (amount == 0)
                return true;

            // Check if caller has permission
            if (!Runtime.CheckWitness(from) && !IsAuthorizedMinter(Runtime.CallingScriptHash))
                throw new Exception("Unauthorized transfer");

            // Check balance
            BigInteger fromBalance = BalanceOf(from);
            if (fromBalance < amount)
                throw new Exception("Insufficient balance");

            // Update balances
            BigInteger toBalance = BalanceOf(to);
            
            Storage.Put(Storage.CurrentContext, BalancePrefix + from, fromBalance - amount);
            Storage.Put(Storage.CurrentContext, BalancePrefix + to, toBalance + amount);

            // Emit transfer event
            OnTransfer(from, to, amount);

            // Call onNEP17Payment if recipient is a contract
            if (ContractManagement.GetContract(to) != null)
            {
                Contract.Call(to, "onNEP17Payment", CallFlags.All, from, amount, data);
            }

            return true;
        }

        /// <summary>
        /// Mint new tokens (only authorized minters)
        /// Used by platform to reward users
        /// </summary>
        public static bool Mint(UInt160 to, BigInteger amount)
        {
            // Only authorized minters can mint
            if (!IsAuthorizedMinter(Runtime.CallingScriptHash))
                throw new Exception("Unauthorized minting");

            if (!IsValidAddress(to))
                throw new Exception("Invalid recipient address");

            if (amount <= 0)
                throw new Exception("Amount must be positive");

            // Update recipient balance
            BigInteger balance = BalanceOf(to);
            Storage.Put(Storage.CurrentContext, BalancePrefix + to, balance + amount);

            // Update total supply
            BigInteger totalSupply = TotalSupply();
            Storage.Put(Storage.CurrentContext, SupplyKey, totalSupply + amount);

            // Emit transfer event (from null = minting)
            OnTransfer(null, to, amount);

            return true;
        }

        /// <summary>
        /// Burn tokens (reduce supply)
        /// </summary>
        public static bool Burn(UInt160 from, BigInteger amount)
        {
            if (!IsValidAddress(from))
                throw new Exception("Invalid address");

            if (!Runtime.CheckWitness(from))
                throw new Exception("Unauthorized burn");

            if (amount <= 0)
                throw new Exception("Amount must be positive");

            // Check balance
            BigInteger balance = BalanceOf(from);
            if (balance < amount)
                throw new Exception("Insufficient balance");

            // Update balance
            Storage.Put(Storage.CurrentContext, BalancePrefix + from, balance - amount);

            // Update total supply
            BigInteger totalSupply = TotalSupply();
            Storage.Put(Storage.CurrentContext, SupplyKey, totalSupply - amount);

            // Emit transfer event (to null = burning)
            OnTransfer(from, null, amount);

            return true;
        }

        /// <summary>
        /// Add an authorized minter (platform contract)
        /// Only owner can add minters
        /// </summary>
        public static bool AddMinter(UInt160 minter)
        {
            UInt160 owner = (UInt160)Storage.Get(Storage.CurrentContext, OwnerKey);
            if (!Runtime.CheckWitness(owner))
                throw new Exception("Only owner can add minters");

            if (!IsValidAddress(minter))
                throw new Exception("Invalid minter address");

            ByteString key = MinterPrefix + minter;
            Storage.Put(Storage.CurrentContext, key, 1);

            return true;
        }

        /// <summary>
        /// Remove an authorized minter
        /// </summary>
        public static bool RemoveMinter(UInt160 minter)
        {
            UInt160 owner = (UInt160)Storage.Get(Storage.CurrentContext, OwnerKey);
            if (!Runtime.CheckWitness(owner))
                throw new Exception("Only owner can remove minters");

            ByteString key = MinterPrefix + minter;
            Storage.Delete(Storage.CurrentContext, key);

            return true;
        }

        /// <summary>
        /// Check if an address is an authorized minter
        /// </summary>
        [Safe]
        private static bool IsAuthorizedMinter(UInt160 address)
        {
            // Owner is always authorized
            UInt160 owner = (UInt160)Storage.Get(Storage.CurrentContext, OwnerKey);
            if (address == owner)
                return true;

            // Check minter list
            ByteString key = MinterPrefix + address;
            return Storage.Get(Storage.CurrentContext, key) != null;
        }

        /// <summary>
        /// Validate address format
        /// </summary>
        [Safe]
        private static bool IsValidAddress(UInt160 address)
        {
            return address != null && address.IsValid && !address.IsZero;
        }

        /// <summary>
        /// Get contract owner
        /// </summary>
        [Safe]
        public static UInt160 GetOwner()
        {
            return (UInt160)Storage.Get(Storage.CurrentContext, OwnerKey);
        }

        /// <summary>
        /// Transfer ownership (only current owner)
        /// </summary>
        public static bool TransferOwnership(UInt160 newOwner)
        {
            UInt160 owner = (UInt160)Storage.Get(Storage.CurrentContext, OwnerKey);
            if (!Runtime.CheckWitness(owner))
                throw new Exception("Only owner can transfer ownership");

            if (!IsValidAddress(newOwner))
                throw new Exception("Invalid new owner address");

            Storage.Put(Storage.CurrentContext, OwnerKey, newOwner);
            return true;
        }

        /// <summary>
        /// Get contract version
        /// </summary>
        [Safe]
        public static string Version() => "1.0.0";
    }
}
