package com.nuclearvortex.vortexventures.iou;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

/**
 * An immutable record of a single I.O.U. (I Owe You) debt.
 *
 * <p>Each {@code Iou} tracks a one-directional financial obligation from a
 * {@code debtor} to a {@code creditor} for a fixed {@code amount}.  The record
 * is created in {@link IouStatus#PENDING} state and transitions to
 * {@link IouStatus#SETTLED} when the debt is repaid via
 * {@link IouLedger#settle(UUID)}.</p>
 *
 * <p>Instances are obtained through {@link IouLedger}, not constructed directly.</p>
 */
public final class Iou {

    private final UUID id;
    private final String debtor;
    private final String creditor;
    private final BigDecimal amount;
    private final String description;
    private final LocalDate dateCreated;
    private IouStatus status;

    /**
     * Constructs a new pending I.O.U.
     *
     * @param id          unique identifier; must not be {@code null}
     * @param debtor      name of the person who owes money; must not be blank
     * @param creditor    name of the person who is owed money; must not be blank
     * @param amount      the amount owed; must be positive
     * @param description a short human-readable note about the debt; must not be {@code null}
     * @param dateCreated the date the I.O.U. was recorded; must not be {@code null}
     * @throws NullPointerException     if any argument is {@code null}
     * @throws IllegalArgumentException if {@code debtor} or {@code creditor} is blank,
     *                                  if {@code debtor} equals {@code creditor},
     *                                  or if {@code amount} is not positive
     */
    Iou(UUID id, String debtor, String creditor, BigDecimal amount,
            String description, LocalDate dateCreated) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(debtor, "debtor must not be null");
        Objects.requireNonNull(creditor, "creditor must not be null");
        if (debtor.isBlank()) {
            throw new IllegalArgumentException("debtor must not be blank");
        }
        if (creditor.isBlank()) {
            throw new IllegalArgumentException("creditor must not be blank");
        }
        if (debtor.equalsIgnoreCase(creditor)) {
            throw new IllegalArgumentException("debtor and creditor must be different people");
        }
        Objects.requireNonNull(amount, "amount must not be null");
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
        this.debtor = debtor;
        this.creditor = creditor;
        this.amount = amount;
        this.description = Objects.requireNonNull(description, "description must not be null");
        this.dateCreated = Objects.requireNonNull(dateCreated, "dateCreated must not be null");
        this.status = IouStatus.PENDING;
    }

    /**
     * Returns the unique identifier of this I.O.U.
     *
     * @return UUID, never {@code null}
     */
    public UUID getId() {
        return id;
    }

    /**
     * Returns the name of the person who owes money.
     *
     * @return debtor name, never blank
     */
    public String getDebtor() {
        return debtor;
    }

    /**
     * Returns the name of the person who is owed money.
     *
     * @return creditor name, never blank
     */
    public String getCreditor() {
        return creditor;
    }

    /**
     * Returns the amount owed.
     *
     * @return positive monetary amount
     */
    public BigDecimal getAmount() {
        return amount;
    }

    /**
     * Returns the human-readable note attached to this debt.
     *
     * @return description string, never {@code null}
     */
    public String getDescription() {
        return description;
    }

    /**
     * Returns the date this I.O.U. was created.
     *
     * @return creation date, never {@code null}
     */
    public LocalDate getDateCreated() {
        return dateCreated;
    }

    /**
     * Returns the current status of this I.O.U.
     *
     * @return {@link IouStatus#PENDING} or {@link IouStatus#SETTLED}
     */
    public IouStatus getStatus() {
        return status;
    }

    /**
     * Returns {@code true} if this debt has not yet been repaid.
     *
     * @return {@code true} when status is {@link IouStatus#PENDING}
     */
    public boolean isPending() {
        return status == IouStatus.PENDING;
    }

    /**
     * Marks this I.O.U. as settled.  Package-private so only
     * {@link IouLedger} can trigger a status change.
     */
    void markSettled() {
        this.status = IouStatus.SETTLED;
    }

    @Override
    public String toString() {
        return String.format("Iou{id=%s, debtor='%s', creditor='%s', amount=%s, status=%s, date=%s}",
                id, debtor, creditor, amount, status, dateCreated);
    }
}
