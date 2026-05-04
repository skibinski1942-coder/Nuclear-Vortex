package com.nuclearvortex.vortexventures;

import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Pattern;

/**
 * Validates and approves XRP payment transactions on behalf of users.
 *
 * <h2>Validation rules</h2>
 * <ol>
 *   <li><b>Address format</b> — both sender and receiver must be well-formed
 *       XRP Ledger addresses (start with {@code 'r'}, 25–34 alphanumeric
 *       characters).</li>
 *   <li><b>Self-transfer</b> — sender and receiver must be different
 *       addresses.</li>
 *   <li><b>Minimum amount</b> — the payment must be at least 1 drop
 *       (enforced by {@link XrpTransaction}).</li>
 *   <li><b>Per-transaction limit</b> — a single transaction may not exceed
 *       the configured {@code maxSingleTransactionDrops}.</li>
 *   <li><b>Daily limit per sender</b> — the running total of all approved
 *       payments from a sender address must not exceed
 *       {@code maxDailyDropsPerSender} within the current day.  Callers are
 *       responsible for resetting daily totals at day boundaries (e.g. via
 *       {@link #resetDailyTotals()}).</li>
 *   <li><b>Blocked addresses</b> — any transaction involving a blocked sender
 *       or receiver is immediately rejected.</li>
 *   <li><b>Large-transaction review</b> — payments that exceed the
 *       {@code largeTransactionThresholdDrops} are placed in {@link
 *       ApprovalStatus#PENDING} for manual compliance review instead of being
 *       auto-approved.</li>
 * </ol>
 *
 * <p>All monetary limits are expressed in <em>drops</em>
 * (1 XRP = 1,000,000 drops).</p>
 *
 * <p>This class is thread-safe with respect to daily-total tracking.</p>
 */
public final class XrpLedgerService {

    /**
     * Regex that matches valid XRP Ledger account addresses:
     * starts with 'r', followed by 24–33 Base58 alphanumeric characters
     * (total length 25–34).
     */
    private static final Pattern XRP_ADDRESS_PATTERN =
            Pattern.compile("^r[1-9A-HJ-NP-Za-km-z]{24,33}$");

    /**
     * Default per-transaction limit: 100,000 XRP in drops.
     * Transactions above {@link #largeTransactionThresholdDrops} but at or
     * below this value are auto-approved; those above go to PENDING.
     */
    public static final long DEFAULT_MAX_SINGLE_TRANSACTION_DROPS =
            100_000L * XrpTransaction.DROPS_PER_XRP;

    /**
     * Default daily limit per sender: 500,000 XRP in drops.
     */
    public static final long DEFAULT_MAX_DAILY_DROPS_PER_SENDER =
            500_000L * XrpTransaction.DROPS_PER_XRP;

    /**
     * Default large-transaction threshold: 10,000 XRP in drops.
     * Transactions above this amount are routed to PENDING review.
     */
    public static final long DEFAULT_LARGE_TRANSACTION_THRESHOLD_DROPS =
            10_000L * XrpTransaction.DROPS_PER_XRP;

    private final long maxSingleTransactionDrops;
    private final long maxDailyDropsPerSender;
    private final long largeTransactionThresholdDrops;

    /** Addresses that are unconditionally blocked from sending or receiving. */
    private final Set<String> blockedAddresses;

    /** Running daily totals per sender address (in drops). */
    private final Map<String, Long> dailySentDrops = new ConcurrentHashMap<>();

    // -------------------------------------------------------------------------
    // Constructors
    // -------------------------------------------------------------------------

    /**
     * Creates an {@code XrpLedgerService} with default limits and no blocked
     * addresses.
     */
    public XrpLedgerService() {
        this(DEFAULT_MAX_SINGLE_TRANSACTION_DROPS,
             DEFAULT_MAX_DAILY_DROPS_PER_SENDER,
             DEFAULT_LARGE_TRANSACTION_THRESHOLD_DROPS,
             Collections.emptySet());
    }

    /**
     * Creates an {@code XrpLedgerService} with custom limits.
     *
     * @param maxSingleTransactionDrops         per-transaction cap in drops; must be positive
     * @param maxDailyDropsPerSender            daily sender cap in drops; must be positive
     * @param largeTransactionThresholdDrops    threshold above which transactions go to PENDING;
     *                                          must be positive and ≤ maxSingleTransactionDrops
     * @param blockedAddresses                  set of XRP addresses that are unconditionally
     *                                          blocked; must not be null
     * @throws IllegalArgumentException if any limit is out of range
     */
    public XrpLedgerService(long maxSingleTransactionDrops,
                             long maxDailyDropsPerSender,
                             long largeTransactionThresholdDrops,
                             Set<String> blockedAddresses) {
        if (maxSingleTransactionDrops <= 0) {
            throw new IllegalArgumentException("maxSingleTransactionDrops must be positive");
        }
        if (maxDailyDropsPerSender <= 0) {
            throw new IllegalArgumentException("maxDailyDropsPerSender must be positive");
        }
        if (largeTransactionThresholdDrops <= 0) {
            throw new IllegalArgumentException("largeTransactionThresholdDrops must be positive");
        }
        if (largeTransactionThresholdDrops > maxSingleTransactionDrops) {
            throw new IllegalArgumentException(
                    "largeTransactionThresholdDrops must be <= maxSingleTransactionDrops");
        }
        this.maxSingleTransactionDrops      = maxSingleTransactionDrops;
        this.maxDailyDropsPerSender         = maxDailyDropsPerSender;
        this.largeTransactionThresholdDrops = largeTransactionThresholdDrops;
        this.blockedAddresses = Collections.unmodifiableSet(
                new HashSet<>(Objects.requireNonNull(blockedAddresses, "blockedAddresses must not be null")));
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Evaluates the given XRP transaction and returns an {@link ApprovalResult}.
     *
     * <p>Approved transactions have their amounts added to the sender's running
     * daily total. Rejected or pending transactions do not affect daily totals.</p>
     *
     * @param transaction the transaction to evaluate; must not be null
     * @return an {@link ApprovalResult} with the decision and reason
     */
    public ApprovalResult approve(XrpTransaction transaction) {
        Objects.requireNonNull(transaction, "transaction must not be null");

        // 1. Validate sender address format
        if (!isValidXrpAddress(transaction.getSenderAddress())) {
            return reject("Invalid sender address: " + transaction.getSenderAddress());
        }

        // 2. Validate receiver address format
        if (!isValidXrpAddress(transaction.getReceiverAddress())) {
            return reject("Invalid receiver address: " + transaction.getReceiverAddress());
        }

        // 3. Reject self-transfers
        if (transaction.getSenderAddress().equals(transaction.getReceiverAddress())) {
            return reject("Sender and receiver must be different addresses");
        }

        // 4. Check blocked addresses
        if (blockedAddresses.contains(transaction.getSenderAddress())) {
            return reject("Sender address is blocked: " + transaction.getSenderAddress());
        }
        if (blockedAddresses.contains(transaction.getReceiverAddress())) {
            return reject("Receiver address is blocked: " + transaction.getReceiverAddress());
        }

        // 5. Per-transaction limit
        if (transaction.getAmountDrops() > maxSingleTransactionDrops) {
            return reject(String.format(
                    "Transaction amount %d drops exceeds the per-transaction limit of %d drops",
                    transaction.getAmountDrops(), maxSingleTransactionDrops));
        }

        // 6. Large-transaction review threshold
        if (transaction.getAmountDrops() > largeTransactionThresholdDrops) {
            return pending(String.format(
                    "Transaction amount %d drops exceeds the large-transaction threshold of %d drops "
                    + "and requires manual compliance review",
                    transaction.getAmountDrops(), largeTransactionThresholdDrops));
        }

        // 7. Daily limit per sender — checked and updated atomically to prevent race conditions
        boolean[] limitExceeded = {false};
        long[]    newTotalRef   = {0};
        dailySentDrops.compute(transaction.getSenderAddress(), (addr, current) -> {
            long cur      = (current == null) ? 0L : current;
            long newTotal = cur + transaction.getAmountDrops();
            if (newTotal > maxDailyDropsPerSender) {
                limitExceeded[0] = true;
                newTotalRef[0]   = newTotal;
                return cur;   // leave the stored total unchanged
            }
            newTotalRef[0] = newTotal;
            return newTotal;
        });
        if (limitExceeded[0]) {
            return reject(String.format(
                    "Transaction would bring sender's daily total to %d drops, "
                    + "exceeding the daily limit of %d drops",
                    newTotalRef[0], maxDailyDropsPerSender));
        }
        return approve(String.format(
                "Transaction approved: %d drops from %s to %s",
                transaction.getAmountDrops(),
                transaction.getSenderAddress(),
                transaction.getReceiverAddress()));
    }

    /**
     * Resets all tracked daily sent totals.
     *
     * <p>Should be called once per calendar day (e.g. by a scheduled job at
     * midnight UTC) to allow senders to transact up to their daily limit again.</p>
     */
    public void resetDailyTotals() {
        dailySentDrops.clear();
    }

    /**
     * Returns the current running daily sent total for the given sender address,
     * in drops.  Returns {@code 0} if no approved transactions have been recorded
     * for this address in the current day.
     *
     * @param senderAddress the XRP Ledger address to query; must not be null
     * @return drops sent today, or {@code 0}
     */
    public long getDailySentDrops(String senderAddress) {
        Objects.requireNonNull(senderAddress, "senderAddress must not be null");
        return dailySentDrops.getOrDefault(senderAddress, 0L);
    }

    /**
     * Checks whether the given string is a syntactically valid XRP Ledger address.
     *
     * <p>A valid address starts with {@code 'r'} and is followed by 24–33
     * characters drawn from the Base58 alphabet (excludes {@code 0}, {@code O},
     * {@code I}, and {@code l} to avoid visual confusion).</p>
     *
     * @param address the string to validate; may be null
     * @return {@code true} if the address matches the expected format
     */
    public static boolean isValidXrpAddress(String address) {
        return address != null && XRP_ADDRESS_PATTERN.matcher(address).matches();
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private static ApprovalResult approve(String reason) {
        return new ApprovalResult(ApprovalStatus.APPROVED, reason);
    }

    private static ApprovalResult reject(String reason) {
        return new ApprovalResult(ApprovalStatus.REJECTED, reason);
    }

    private static ApprovalResult pending(String reason) {
        return new ApprovalResult(ApprovalStatus.PENDING, reason);
    }
}
