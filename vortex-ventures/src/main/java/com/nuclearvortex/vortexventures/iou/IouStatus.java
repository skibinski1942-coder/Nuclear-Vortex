package com.nuclearvortex.vortexventures.iou;

/**
 * Lifecycle status of an I.O.U. record.
 *
 * <ul>
 *   <li>{@link #PENDING} — the debt has been recorded but not yet repaid.</li>
 *   <li>{@link #SETTLED} — the debtor has repaid the creditor in full.</li>
 * </ul>
 */
public enum IouStatus {

    /**
     * The I.O.U. is outstanding; the debtor still owes the creditor.
     */
    PENDING,

    /**
     * The debt has been fully repaid; no money is owed.
     */
    SETTLED
}
