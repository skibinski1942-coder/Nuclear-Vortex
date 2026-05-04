package com.nuclearvortex.vortexventures;

import java.util.Objects;

/**
 * Immutable result returned by {@link XrpLedgerService#approve(XrpTransaction)}.
 *
 * <p>Every result carries an {@link ApprovalStatus} and a human-readable
 * {@code reason} that explains why the transaction was approved, rejected, or
 * placed in a pending state.</p>
 */
public final class ApprovalResult {

    private final ApprovalStatus status;
    private final String reason;

    /**
     * Creates an approval result.
     *
     * @param status the approval status; must not be null
     * @param reason a short, human-readable explanation; must not be null or blank
     */
    public ApprovalResult(ApprovalStatus status, String reason) {
        this.status = Objects.requireNonNull(status, "status must not be null");
        Objects.requireNonNull(reason, "reason must not be null");
        if (reason.isBlank()) {
            throw new IllegalArgumentException("reason must not be blank");
        }
        this.reason = reason;
    }

    /** Returns the approval status of the transaction. */
    public ApprovalStatus getStatus() {
        return status;
    }

    /** Returns a human-readable explanation for the approval decision. */
    public String getReason() {
        return reason;
    }

    /** Convenience check: returns {@code true} when status is {@link ApprovalStatus#APPROVED}. */
    public boolean isApproved() {
        return status == ApprovalStatus.APPROVED;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ApprovalResult)) return false;
        ApprovalResult that = (ApprovalResult) o;
        return status == that.status && Objects.equals(reason, that.reason);
    }

    @Override
    public int hashCode() {
        return Objects.hash(status, reason);
    }

    @Override
    public String toString() {
        return "ApprovalResult{status=" + status + ", reason='" + reason + "'}";
    }
}
