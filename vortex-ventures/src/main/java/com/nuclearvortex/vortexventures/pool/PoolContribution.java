package com.nuclearvortex.vortexventures.pool;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

/**
 * An immutable record of a single monetary contribution made by a pool member.
 *
 * <p>Contributions are append-only: once recorded they cannot be modified or
 * reversed by the contributing member.  Only the payout account holder may
 * receive the accumulated funds via {@link MoneyPool#disburse(String)}.</p>
 *
 * <p>Instances are created exclusively through {@link MoneyPool#contribute(String, BigDecimal)}.</p>
 */
public final class PoolContribution {

    private final UUID id;
    private final String memberId;
    private final BigDecimal amount;
    private final LocalDate dateContributed;

    /**
     * Package-private constructor called by {@link MoneyPool}.
     *
     * @param id               unique identifier; must not be {@code null}
     * @param memberId         the contributing member's account ID; must not be blank
     * @param amount           the contribution amount; must be positive
     * @param dateContributed  the date of the contribution; must not be {@code null}
     */
    PoolContribution(UUID id, String memberId, BigDecimal amount, LocalDate dateContributed) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(memberId, "memberId must not be null");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("memberId must not be blank");
        }
        Objects.requireNonNull(amount, "amount must not be null");
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
        this.memberId = memberId;
        this.amount = amount;
        this.dateContributed = Objects.requireNonNull(dateContributed, "dateContributed must not be null");
    }

    /** @return unique identifier of this contribution record, never {@code null} */
    public UUID getId() {
        return id;
    }

    /** @return account ID of the member who made this contribution, never blank */
    public String getMemberId() {
        return memberId;
    }

    /** @return the amount contributed, always positive */
    public BigDecimal getAmount() {
        return amount;
    }

    /** @return date this contribution was recorded, never {@code null} */
    public LocalDate getDateContributed() {
        return dateContributed;
    }

    @Override
    public String toString() {
        return String.format("PoolContribution{id=%s, member='%s', amount=%s, date=%s}",
                id, memberId, amount, dateContributed);
    }
}
