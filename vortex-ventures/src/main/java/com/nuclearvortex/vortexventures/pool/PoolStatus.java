package com.nuclearvortex.vortexventures.pool;

/**
 * Lifecycle status of a {@link MoneyPool}.
 *
 * <ul>
 *   <li>{@link #OPEN}      — the pool is accepting member contributions.</li>
 *   <li>{@link #DISBURSED} — the pooled funds have been sent to the payout account
 *       (e.g., the property manager's bank account).  No further contributions
 *       are accepted and no withdrawals by members are possible.</li>
 *   <li>{@link #CLOSED}    — the pool was closed by its creator before disbursement.
 *       No further contributions or disbursements are allowed.</li>
 * </ul>
 */
public enum PoolStatus {

    /**
     * The pool is open and accepting contributions from its members.
     */
    OPEN,

    /**
     * All pooled funds have been disbursed to the designated payout account.
     * The pool is now read-only.
     */
    DISBURSED,

    /**
     * The pool has been closed by the creator without disbursing funds.
     * No further activity is permitted.
     */
    CLOSED
}
