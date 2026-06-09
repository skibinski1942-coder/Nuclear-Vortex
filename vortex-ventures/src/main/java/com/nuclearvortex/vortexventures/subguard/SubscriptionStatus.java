package com.nuclearvortex.vortexventures.subguard;

/**
 * Lifecycle status of a tracked subscription.
 *
 * <ul>
 *   <li>{@link #ACTIVE}           — the subscription is current and in good standing.</li>
 *   <li>{@link #CANCELLED}        — the subscription has been cancelled by the user.</li>
 *   <li>{@link #FLAGGED_DOUBLE_DIP} — the agent has detected that the user is being
 *       charged more than once for effectively the same service and has opened a
 *       recovery claim.</li>
 * </ul>
 */
public enum SubscriptionStatus {

    /**
     * Subscription is active and being tracked normally.
     */
    ACTIVE,

    /**
     * Subscription has been cancelled; no further charges expected.
     */
    CANCELLED,

    /**
     * The subscription has been flagged as a double-dip: the same (or
     * substantially equivalent) service is being billed twice or more.
     * A {@link DoubleDipClaim} will have been raised for this subscription.
     */
    FLAGGED_DOUBLE_DIP
}
