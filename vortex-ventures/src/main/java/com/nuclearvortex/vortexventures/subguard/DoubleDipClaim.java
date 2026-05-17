package com.nuclearvortex.vortexventures.subguard;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

/**
 * A recovery claim raised when the SubscriptionGuard agent detects a double-dip.
 *
 * <p>A <em>double-dip</em> occurs when a user is charged more than once for the
 * same or substantially equivalent subscription service — for example, being billed
 * for "Disney+" on both their phone and their smart TV when a single account should
 * cover all devices, or when two streaming bundles overlap and both charge for the
 * same underlying content library.</p>
 *
 * <p>When a claim is resolved, {@link #setRecoveredAmount(BigDecimal)} records how
 * much the service provider refunded.  The platform then earns a 10 % commission on
 * that recovered amount (see {@link #getPlatformFee()}).</p>
 *
 * <p>Instances are created exclusively by {@link SubscriptionGuardAgent}.</p>
 */
public final class DoubleDipClaim {

    /** Platform commission rate — 10 % of every recovered dollar. */
    static final BigDecimal PLATFORM_FEE_RATE = new BigDecimal("0.10");

    /**
     * Lifecycle state of a recovery claim.
     */
    public enum ClaimStatus {
        /** Claim has been filed and is awaiting response from the service provider. */
        OPEN,
        /** The service provider has refunded money to the user. */
        RECOVERED,
        /** The claim was reviewed but no refund was issued. */
        REJECTED
    }

    private final UUID id;
    private final UUID primarySubscriptionId;
    private final UUID duplicateSubscriptionId;
    private final String reason;
    private final LocalDate dateFiled;
    private ClaimStatus claimStatus;
    private BigDecimal recoveredAmount;

    /**
     * Constructs a new open double-dip recovery claim.
     *
     * @param id                     unique identifier for this claim; must not be {@code null}
     * @param primarySubscriptionId  the first (legitimate) subscription UUID; must not be {@code null}
     * @param duplicateSubscriptionId the subscription deemed a duplicate; must not be {@code null}
     * @param reason                 a human-readable explanation of the detected double-dip; must not be blank
     * @param dateFiled              the date the claim was raised; must not be {@code null}
     * @throws NullPointerException     if any argument is {@code null}
     * @throws IllegalArgumentException if {@code reason} is blank or both subscription IDs are equal
     */
    DoubleDipClaim(UUID id, UUID primarySubscriptionId, UUID duplicateSubscriptionId,
            String reason, LocalDate dateFiled) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.primarySubscriptionId =
                Objects.requireNonNull(primarySubscriptionId, "primarySubscriptionId must not be null");
        this.duplicateSubscriptionId =
                Objects.requireNonNull(duplicateSubscriptionId, "duplicateSubscriptionId must not be null");
        if (primarySubscriptionId.equals(duplicateSubscriptionId)) {
            throw new IllegalArgumentException(
                    "primarySubscriptionId and duplicateSubscriptionId must be different");
        }
        Objects.requireNonNull(reason, "reason must not be null");
        if (reason.isBlank()) {
            throw new IllegalArgumentException("reason must not be blank");
        }
        this.reason = reason;
        this.dateFiled = Objects.requireNonNull(dateFiled, "dateFiled must not be null");
        this.claimStatus = ClaimStatus.OPEN;
        this.recoveredAmount = BigDecimal.ZERO;
    }

    /** @return unique identifier of this claim, never {@code null} */
    public UUID getId() {
        return id;
    }

    /** @return UUID of the primary (legitimate) subscription, never {@code null} */
    public UUID getPrimarySubscriptionId() {
        return primarySubscriptionId;
    }

    /** @return UUID of the subscription identified as a duplicate, never {@code null} */
    public UUID getDuplicateSubscriptionId() {
        return duplicateSubscriptionId;
    }

    /** @return human-readable description of the double-dip detected, never blank */
    public String getReason() {
        return reason;
    }

    /** @return date the claim was filed, never {@code null} */
    public LocalDate getDateFiled() {
        return dateFiled;
    }

    /** @return current {@link ClaimStatus} of this recovery claim */
    public ClaimStatus getClaimStatus() {
        return claimStatus;
    }

    /**
     * Returns the amount recovered from the service provider.
     * This is {@link BigDecimal#ZERO} until the claim is resolved as
     * {@link ClaimStatus#RECOVERED}.
     *
     * @return recovered amount, never {@code null}, never negative
     */
    public BigDecimal getRecoveredAmount() {
        return recoveredAmount;
    }

    /**
     * Returns the 10 % platform fee earned on the recovered amount.
     *
     * <p>This is {@link BigDecimal#ZERO} until money has actually been recovered.</p>
     *
     * @return platform fee = recoveredAmount × 10 %, never {@code null}
     */
    public BigDecimal getPlatformFee() {
        return recoveredAmount.multiply(PLATFORM_FEE_RATE)
                .setScale(2, java.math.RoundingMode.HALF_UP);
    }

    /**
     * Records the recovered refund from the service provider and transitions
     * this claim to {@link ClaimStatus#RECOVERED}.
     *
     * <p>Package-private: only {@link SubscriptionGuardAgent} may resolve claims.</p>
     *
     * @param amount the amount refunded; must be positive
     * @throws IllegalArgumentException if {@code amount} is not positive
     * @throws IllegalStateException    if this claim is not currently {@link ClaimStatus#OPEN}
     */
    void setRecoveredAmount(BigDecimal amount) {
        Objects.requireNonNull(amount, "amount must not be null");
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("recovered amount must be positive");
        }
        if (claimStatus != ClaimStatus.OPEN) {
            throw new IllegalStateException("Claim " + id + " is not open; cannot record recovery");
        }
        this.recoveredAmount = amount;
        this.claimStatus = ClaimStatus.RECOVERED;
    }

    /**
     * Marks this claim as rejected (no refund issued).
     *
     * <p>Package-private: only {@link SubscriptionGuardAgent} may reject claims.</p>
     *
     * @throws IllegalStateException if this claim is not currently {@link ClaimStatus#OPEN}
     */
    void reject() {
        if (claimStatus != ClaimStatus.OPEN) {
            throw new IllegalStateException("Claim " + id + " is not open; cannot reject");
        }
        this.claimStatus = ClaimStatus.REJECTED;
    }

    @Override
    public String toString() {
        return String.format(
                "DoubleDipClaim{id=%s, status=%s, recovered=%s, platformFee=%s, filed=%s}",
                id, claimStatus, recoveredAmount, getPlatformFee(), dateFiled);
    }
}
