package com.nuclearvortex.vortexventures;

/**
 * The outcome of evaluating an XRP transaction approval request.
 *
 * <ul>
 *   <li>{@link #APPROVED} — the transaction passed all validation and policy
 *       checks and may be submitted to the XRP Ledger.</li>
 *   <li>{@link #REJECTED} — the transaction violated one or more rules and
 *       must not be submitted.</li>
 *   <li>{@link #PENDING} — the transaction requires additional review (e.g.
 *       manual compliance check) before a final decision can be made.</li>
 * </ul>
 */
public enum ApprovalStatus {

    /** Transaction is valid and authorised. */
    APPROVED,

    /** Transaction has been declined due to a policy or validation failure. */
    REJECTED,

    /** Transaction requires further review before it can be approved. */
    PENDING
}
