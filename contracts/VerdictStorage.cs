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
    /// Verdict Storage Smart Contract for Moral Duel Platform
    /// 
    /// Purpose: Store immutable verdict hashes for moral dilemma cases
    /// to ensure AI verdicts cannot be changed after case creation.
    /// 
    /// Key Features:
    /// - Commit verdict hash before case goes live
    /// - Retrieve verdict hash after case closes
    /// - Verify verdict integrity
    /// - Prevent double commitment for same case
    /// </summary>
    [DisplayName("MoralDuel.VerdictStorage")]
    [ManifestExtra("Author", "Moral Duel Team")]
    [ManifestExtra("Email", "dev@moralduel.com")]
    [ManifestExtra("Description", "Immutable verdict storage for moral dilemma cases")]
    [ContractPermission("*", "*")]
    public class VerdictStorage : SmartContract
    {
        // Storage prefix keys
        private static readonly byte[] VerdictPrefix = new byte[] { 0x01 };
        private static readonly byte[] CaseMetaPrefix = new byte[] { 0x02 };
        private static readonly byte[] OwnerPrefix = new byte[] { 0x03 };

        // Events
        [DisplayName("VerdictCommitted")]
        public static event Action<BigInteger, ByteString, BigInteger> OnVerdictCommitted;

        [DisplayName("VerdictRevealed")]
        public static event Action<BigInteger, ByteString> OnVerdictRevealed;

        /// <summary>
        /// Initialize contract with owner
        /// </summary>
        public static void _deploy(object data, bool update)
        {
            if (!update)
            {
                // Set initial owner to deployer
                Storage.Put(Storage.CurrentContext, OwnerPrefix, (ByteString)Runtime.ExecutingScriptHash);
            }
        }

        /// <summary>
        /// Commit a verdict hash to the blockchain
        /// This is called BEFORE the case goes live to users
        /// </summary>
        /// <param name="caseId">Unique case identifier</param>
        /// <param name="verdictHash">SHA-256 hash of the verdict</param>
        /// <param name="closesAt">Unix timestamp when case closes</param>
        /// <returns>True if commitment successful</returns>
        public static bool CommitVerdict(BigInteger caseId, ByteString verdictHash, BigInteger closesAt)
        {
            // Validate inputs
            if (caseId <= 0)
                throw new Exception("Invalid case ID");

            if (verdictHash.Length != 32)
                throw new Exception("Verdict hash must be 32 bytes (SHA-256)");

            if (closesAt <= Runtime.Time / 1000)
                throw new Exception("Case close time must be in the future");

            // Check if verdict already exists
            ByteString key = VerdictPrefix + caseId.ToByteArray();
            if (Storage.Get(Storage.CurrentContext, key) != null)
                throw new Exception("Verdict already committed for this case");

            // Store verdict hash
            Storage.Put(Storage.CurrentContext, key, verdictHash);

            // Store metadata (timestamp, closes_at)
            ByteString metaKey = CaseMetaPrefix + caseId.ToByteArray();
            CaseMetadata meta = new CaseMetadata
            {
                CommittedAt = Runtime.Time / 1000,
                ClosesAt = closesAt,
                Revealed = false
            };
            Storage.Put(Storage.CurrentContext, metaKey, StdLib.Serialize(meta));

            // Emit event
            OnVerdictCommitted(caseId, verdictHash, closesAt);

            return true;
        }

        /// <summary>
        /// Get verdict hash for a case (can be called anytime)
        /// This returns the committed hash without revealing the actual verdict
        /// </summary>
        /// <param name="caseId">Case identifier</param>
        /// <returns>Verdict hash or null if not found</returns>
        public static ByteString GetVerdictHash(BigInteger caseId)
        {
            ByteString key = VerdictPrefix + caseId.ToByteArray();
            return Storage.Get(Storage.CurrentContext, key);
        }

        /// <summary>
        /// Verify that a verdict hash matches what's stored on blockchain
        /// </summary>
        /// <param name="caseId">Case identifier</param>
        /// <param name="providedHash">Hash to verify</param>
        /// <returns>True if hashes match</returns>
        public static bool VerifyVerdict(BigInteger caseId, ByteString providedHash)
        {
            ByteString storedHash = GetVerdictHash(caseId);
            
            if (storedHash == null)
                return false;

            return storedHash.Equals(providedHash);
        }

        /// <summary>
        /// Get case metadata including commitment timestamp and close time
        /// </summary>
        /// <param name="caseId">Case identifier</param>
        /// <returns>Serialized metadata or null</returns>
        public static CaseMetadata GetCaseMetadata(BigInteger caseId)
        {
            ByteString metaKey = CaseMetaPrefix + caseId.ToByteArray();
            ByteString data = Storage.Get(Storage.CurrentContext, metaKey);
            
            if (data == null)
                return null;

            return (CaseMetadata)StdLib.Deserialize(data);
        }

        /// <summary>
        /// Mark verdict as revealed (called after case closes)
        /// This doesn't change the hash, just marks it as revealed
        /// </summary>
        /// <param name="caseId">Case identifier</param>
        /// <returns>True if marked successfully</returns>
        public static bool MarkRevealed(BigInteger caseId)
        {
            ByteString metaKey = CaseMetaPrefix + caseId.ToByteArray();
            CaseMetadata meta = GetCaseMetadata(caseId);

            if (meta == null)
                throw new Exception("Case not found");

            if (meta.Revealed)
                throw new Exception("Verdict already revealed");

            // Update metadata
            meta.Revealed = true;
            meta.RevealedAt = Runtime.Time / 1000;
            Storage.Put(Storage.CurrentContext, metaKey, StdLib.Serialize(meta));

            // Emit event
            ByteString hash = GetVerdictHash(caseId);
            OnVerdictRevealed(caseId, hash);

            return true;
        }

        /// <summary>
        /// Get contract version
        /// </summary>
        public static string Version()
        {
            return "1.0.0";
        }
    }

    /// <summary>
    /// Metadata for stored verdicts
    /// </summary>
    public class CaseMetadata
    {
        public BigInteger CommittedAt;
        public BigInteger ClosesAt;
        public bool Revealed;
        public BigInteger RevealedAt;
    }
}
