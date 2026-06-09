package com.nuclearvortex.vortexventures.pool;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * A shared money pool that multiple members can contribute to.
 *
 * <h2>Concept</h2>
 * <p>A {@code MoneyPool} lets a group of people (e.g. roommates) each contribute
 * toward a common obligation (e.g. monthly rent) that is then disbursed directly
 * to an external payout account (e.g. the property manager's bank account).</p>
 *
 * <h2>Key rules</h2>
 * <ol>
 *   <li>The pool creator designates a <em>payout account ID</em> at creation time.
 *       This represents the external account that will ultimately receive the funds
 *       (e.g. a property manager's bank account).</li>
 *   <li>The creator invites members by calling {@link #addMember(String)}.
 *       The creator's own account ID is automatically added as a member.</li>
 *   <li>Any member may call {@link #contribute(String, BigDecimal)} to add funds.</li>
 *   <li><strong>Contributions are irrevocable by members.</strong>  Once money is
 *       placed into the pool it cannot be withdrawn by any member — only the
 *       payout account holder may receive it via {@link #disburse(String)}.</li>
 *   <li>Only the holder of the designated {@code payoutAccountId} may disburse
 *       the pool's balance.  Passing any other account ID to {@link #disburse}
 *       throws {@link SecurityException}.</li>
 * </ol>
 *
 * <h2>Usage example</h2>
 * <pre>{@code
 * MoneyPool rentPool = new MoneyPool(
 *         UUID.randomUUID(), "April Rent", "3-bedroom apt",
 *         "creator-roommate-1", "property-manager-bank-acct",
 *         new BigDecimal("3000.00"), LocalDate.now());
 *
 * rentPool.addMember("roommate-2");
 * rentPool.addMember("roommate-3");
 *
 * rentPool.contribute("creator-roommate-1", new BigDecimal("1000.00"));
 * rentPool.contribute("roommate-2",          new BigDecimal("1000.00"));
 * rentPool.contribute("roommate-3",          new BigDecimal("1000.00"));
 *
 * rentPool.disburse("property-manager-bank-acct"); // only this ID may disburse
 * }</pre>
 *
 * <p>Instances are created and stored by {@link MoneyPoolRegistry}.</p>
 *
 * <p>This class is <em>not</em> thread-safe.</p>
 */
public final class MoneyPool {

    private final UUID id;
    private final String name;
    private final String description;
    private final String creatorId;
    private final String payoutAccountId;
    private final BigDecimal targetAmount;
    private final LocalDate dateCreated;
    private final Set<String> memberIds = new LinkedHashSet<>();
    private final List<PoolContribution> contributions = new ArrayList<>();
    private PoolStatus status;

    /**
     * Constructs a new open money pool.
     *
     * <p>Package-private; use {@link MoneyPoolRegistry#createPool} to create pools.</p>
     *
     * @param id              unique identifier; must not be {@code null}
     * @param name            human-readable pool name (e.g. "April Rent"); must not be blank
     * @param description     additional context; must not be {@code null}
     * @param creatorId       account ID of the person creating the pool; must not be blank.
     *                        The creator is automatically added as a member.
     * @param payoutAccountId account ID of the external recipient (e.g. property manager);
     *                        must not be blank and must differ from {@code creatorId}
     * @param targetAmount    optional target total (e.g. full monthly rent); {@code null} means
     *                        no specific target.  If provided, must be positive.
     * @param dateCreated     creation date; must not be {@code null}
     * @throws NullPointerException     if {@code id}, {@code name}, {@code description},
     *                                  {@code creatorId}, {@code payoutAccountId}, or
     *                                  {@code dateCreated} is {@code null}
     * @throws IllegalArgumentException if {@code name}, {@code creatorId}, or
     *                                  {@code payoutAccountId} is blank; if {@code creatorId}
     *                                  equals {@code payoutAccountId}; or if a non-null
     *                                  {@code targetAmount} is not positive
     */
    MoneyPool(UUID id, String name, String description, String creatorId,
            String payoutAccountId, BigDecimal targetAmount, LocalDate dateCreated) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(name, "name must not be null");
        if (name.isBlank()) {
            throw new IllegalArgumentException("name must not be blank");
        }
        this.name = name;
        this.description = Objects.requireNonNull(description, "description must not be null");
        Objects.requireNonNull(creatorId, "creatorId must not be null");
        if (creatorId.isBlank()) {
            throw new IllegalArgumentException("creatorId must not be blank");
        }
        Objects.requireNonNull(payoutAccountId, "payoutAccountId must not be null");
        if (payoutAccountId.isBlank()) {
            throw new IllegalArgumentException("payoutAccountId must not be blank");
        }
        if (creatorId.equals(payoutAccountId)) {
            throw new IllegalArgumentException(
                    "creatorId and payoutAccountId must be different accounts");
        }
        if (targetAmount != null && targetAmount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("targetAmount must be positive when specified");
        }
        this.creatorId = creatorId;
        this.payoutAccountId = payoutAccountId;
        this.targetAmount = targetAmount;
        this.dateCreated = Objects.requireNonNull(dateCreated, "dateCreated must not be null");
        this.status = PoolStatus.OPEN;
        this.memberIds.add(creatorId); // creator is automatically a member
    }

    // -----------------------------------------------------------------------
    // Accessors
    // -----------------------------------------------------------------------

    /** @return unique identifier, never {@code null} */
    public UUID getId() {
        return id;
    }

    /** @return pool name, never blank */
    public String getName() {
        return name;
    }

    /** @return pool description, never {@code null} */
    public String getDescription() {
        return description;
    }

    /** @return account ID of the pool creator, never blank */
    public String getCreatorId() {
        return creatorId;
    }

    /**
     * Returns the account ID of the designated payout recipient.
     *
     * <p>Only this account ID may call {@link #disburse(String)} successfully.</p>
     *
     * @return payout account ID, never blank
     */
    public String getPayoutAccountId() {
        return payoutAccountId;
    }

    /**
     * Returns the optional target contribution amount for this pool (e.g. total monthly rent).
     *
     * @return target amount, or {@code null} if no target was set
     */
    public BigDecimal getTargetAmount() {
        return targetAmount;
    }

    /** @return date the pool was created, never {@code null} */
    public LocalDate getDateCreated() {
        return dateCreated;
    }

    /** @return current {@link PoolStatus} */
    public PoolStatus getStatus() {
        return status;
    }

    /** @return {@code true} if this pool is currently {@link PoolStatus#OPEN} */
    public boolean isOpen() {
        return status == PoolStatus.OPEN;
    }

    // -----------------------------------------------------------------------
    // Member management
    // -----------------------------------------------------------------------

    /**
     * Invites a user to this pool by adding their account ID to the member list.
     *
     * <p>Adding a member who is already in the pool is a no-op.</p>
     *
     * @param memberId the account ID to add; must not be blank
     * @throws NullPointerException     if {@code memberId} is {@code null}
     * @throws IllegalArgumentException if {@code memberId} is blank
     * @throws IllegalStateException    if the pool is not {@link PoolStatus#OPEN}
     */
    public void addMember(String memberId) {
        Objects.requireNonNull(memberId, "memberId must not be null");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("memberId must not be blank");
        }
        requireOpen("add a member to");
        memberIds.add(memberId);
    }

    /**
     * Removes a member from the pool.
     *
     * <p>The creator cannot be removed.  Removing a member who has already
     * contributed does not reverse their contributions.</p>
     *
     * @param memberId the account ID to remove; must not be blank
     * @throws NullPointerException     if {@code memberId} is {@code null}
     * @throws IllegalArgumentException if {@code memberId} is blank or is the creator's ID
     * @throws IllegalStateException    if the pool is not {@link PoolStatus#OPEN},
     *                                  or if {@code memberId} is not currently a member
     */
    public void removeMember(String memberId) {
        Objects.requireNonNull(memberId, "memberId must not be null");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("memberId must not be blank");
        }
        if (memberId.equals(creatorId)) {
            throw new IllegalArgumentException("The pool creator cannot be removed from the pool");
        }
        requireOpen("remove a member from");
        if (!memberIds.remove(memberId)) {
            throw new IllegalStateException("Member '" + memberId + "' is not in this pool");
        }
    }

    /**
     * Returns an unmodifiable view of the current member account IDs.
     *
     * @return member IDs in insertion order, never {@code null}
     */
    public Set<String> getMemberIds() {
        return Collections.unmodifiableSet(memberIds);
    }

    /**
     * Returns {@code true} if the given account ID is a member of this pool.
     *
     * @param memberId the account ID to test; must not be {@code null}
     * @return {@code true} if the member is in the pool
     */
    public boolean isMember(String memberId) {
        Objects.requireNonNull(memberId, "memberId must not be null");
        return memberIds.contains(memberId);
    }

    // -----------------------------------------------------------------------
    // Contributions
    // -----------------------------------------------------------------------

    /**
     * Records a monetary contribution from a member.
     *
     * <p><strong>Contributions are irrevocable by members.</strong> Once placed into the
     * pool the funds cannot be withdrawn by any member — they can only be disbursed to
     * the designated payout account via {@link #disburse(String)}.</p>
     *
     * @param memberId the contributing member's account ID; must be a current pool member
     * @param amount   the amount to contribute; must be positive
     * @return the newly created {@link PoolContribution} record
     * @throws NullPointerException     if either argument is {@code null}
     * @throws IllegalArgumentException if {@code memberId} is blank or {@code amount} is not positive
     * @throws IllegalStateException    if the pool is not {@link PoolStatus#OPEN},
     *                                  or if {@code memberId} is not a member of this pool
     */
    public PoolContribution contribute(String memberId, BigDecimal amount) {
        Objects.requireNonNull(memberId, "memberId must not be null");
        Objects.requireNonNull(amount, "amount must not be null");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("memberId must not be blank");
        }
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("contribution amount must be positive");
        }
        requireOpen("contribute to");
        if (!memberIds.contains(memberId)) {
            throw new IllegalStateException(
                    "Account '" + memberId + "' is not a member of pool '" + name + "'");
        }
        PoolContribution contribution =
                new PoolContribution(UUID.randomUUID(), memberId, amount, LocalDate.now());
        contributions.add(contribution);
        return contribution;
    }

    /**
     * Returns an unmodifiable list of all contributions to this pool.
     *
     * @return contributions in the order they were recorded, never {@code null}
     */
    public List<PoolContribution> getContributions() {
        return Collections.unmodifiableList(contributions);
    }

    /**
     * Returns an unmodifiable list of contributions made by the given member.
     *
     * @param memberId account ID to filter by; must not be blank
     * @return the member's contributions in chronological order, never {@code null}
     * @throws NullPointerException     if {@code memberId} is {@code null}
     * @throws IllegalArgumentException if {@code memberId} is blank
     */
    public List<PoolContribution> getContributionsByMember(String memberId) {
        Objects.requireNonNull(memberId, "memberId must not be null");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("memberId must not be blank");
        }
        return contributions.stream()
                .filter(c -> c.getMemberId().equals(memberId))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns the total amount contributed by a specific member.
     *
     * @param memberId account ID to total; must not be blank
     * @return total contributed by this member, rounded to 2 decimal places
     * @throws NullPointerException     if {@code memberId} is {@code null}
     * @throws IllegalArgumentException if {@code memberId} is blank
     */
    public BigDecimal totalContributedByMember(String memberId) {
        return getContributionsByMember(memberId).stream()
                .map(PoolContribution::getAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the current total balance of all contributions in this pool.
     *
     * @return sum of all contributions, rounded to 2 decimal places
     */
    public BigDecimal balance() {
        return contributions.stream()
                .map(PoolContribution::getAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the remaining amount needed to reach the target, or {@link BigDecimal#ZERO}
     * if no target was set or the target has already been met.
     *
     * @return amount still needed, never negative, rounded to 2 decimal places
     */
    public BigDecimal amountRemaining() {
        if (targetAmount == null) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        BigDecimal remaining = targetAmount.subtract(balance());
        return remaining.max(BigDecimal.ZERO).setScale(2, RoundingMode.HALF_UP);
    }

    // -----------------------------------------------------------------------
    // Disbursement (payout account only) & pool closure
    // -----------------------------------------------------------------------

    /**
     * Disburses all pooled funds to the designated payout account.
     *
     * <p><strong>Only the holder of the {@link #getPayoutAccountId() payout account}
     * may call this method.</strong>  No member can withdraw contributions — they can
     * only be sent to the payout account by the account holder themselves.</p>
     *
     * <p>After a successful disbursement the pool transitions to
     * {@link PoolStatus#DISBURSED} and no further contributions are accepted.</p>
     *
     * @param requestingAccountId the account ID initiating the disbursement;
     *                            must equal {@link #getPayoutAccountId()}
     * @return the total amount disbursed
     * @throws NullPointerException  if {@code requestingAccountId} is {@code null}
     * @throws SecurityException     if {@code requestingAccountId} does not match
     *                               {@link #getPayoutAccountId()}
     * @throws IllegalStateException if the pool is not {@link PoolStatus#OPEN},
     *                               or if the pool balance is zero
     */
    public BigDecimal disburse(String requestingAccountId) {
        Objects.requireNonNull(requestingAccountId, "requestingAccountId must not be null");
        if (!payoutAccountId.equals(requestingAccountId)) {
            throw new SecurityException(
                    "Only the payout account holder ('" + payoutAccountId
                    + "') may disburse pool funds. Requested by: '" + requestingAccountId + "'");
        }
        requireOpen("disburse");
        BigDecimal total = balance();
        if (total.compareTo(BigDecimal.ZERO) == 0) {
            throw new IllegalStateException(
                    "Pool '" + name + "' has a zero balance; nothing to disburse");
        }
        status = PoolStatus.DISBURSED;
        return total;
    }

    /**
     * Closes the pool without disbursing funds.
     *
     * <p>Only the pool creator may close the pool.  Once closed, no further
     * contributions or disbursements are accepted.</p>
     *
     * @param requestingAccountId the account ID requesting closure;
     *                            must equal {@link #getCreatorId()}
     * @throws NullPointerException  if {@code requestingAccountId} is {@code null}
     * @throws SecurityException     if {@code requestingAccountId} does not match
     *                               {@link #getCreatorId()}
     * @throws IllegalStateException if the pool is not {@link PoolStatus#OPEN}
     */
    public void close(String requestingAccountId) {
        Objects.requireNonNull(requestingAccountId, "requestingAccountId must not be null");
        if (!creatorId.equals(requestingAccountId)) {
            throw new SecurityException(
                    "Only the pool creator ('" + creatorId + "') may close this pool");
        }
        requireOpen("close");
        status = PoolStatus.CLOSED;
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    private void requireOpen(String action) {
        if (status != PoolStatus.OPEN) {
            throw new IllegalStateException(
                    "Cannot " + action + " pool '" + name + "': pool status is " + status);
        }
    }

    @Override
    public String toString() {
        return String.format(
                "MoneyPool{id=%s, name='%s', creator='%s', payout='%s', balance=%s, status=%s}",
                id, name, creatorId, payoutAccountId, balance(), status);
    }
}
