package com.nuclearvortex.vortexventures.pool;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Central registry for managing {@link MoneyPool} instances.
 *
 * <p>The {@code MoneyPoolRegistry} is the single entry point for creating and looking
 * up money pools.  It mirrors the design of the existing {@code IouLedger} in the
 * Vortex Ventures platform.</p>
 *
 * <h2>Usage example</h2>
 * <pre>{@code
 * MoneyPoolRegistry registry = new MoneyPoolRegistry();
 *
 * UUID poolId = registry.createPool(
 *         "April Rent",
 *         "3-bedroom apartment on Oak St",
 *         "roommate-alice",             // creator
 *         "property-manager-bank-acct", // payout account — only this ID can disburse
 *         new BigDecimal("3000.00"));   // optional target
 *
 * MoneyPool pool = registry.getPool(poolId);
 * pool.addMember("roommate-bob");
 * pool.addMember("roommate-carol");
 *
 * pool.contribute("roommate-alice", new BigDecimal("1000.00"));
 * pool.contribute("roommate-bob",   new BigDecimal("1000.00"));
 * pool.contribute("roommate-carol", new BigDecimal("1000.00"));
 *
 * // Only the property manager can receive the funds:
 * BigDecimal disbursed = pool.disburse("property-manager-bank-acct"); // 3000.00
 * }</pre>
 *
 * <p>This class is <em>not</em> thread-safe.</p>
 */
public final class MoneyPoolRegistry {

    private final Map<UUID, MoneyPool> pools = new LinkedHashMap<>();

    /**
     * Creates a new open money pool and registers it.
     *
     * @param name            human-readable pool name (e.g. "April Rent"); must not be blank
     * @param description     additional context for the pool; must not be {@code null}
     * @param creatorId       account ID of the person creating the pool; must not be blank.
     *                        The creator is automatically added as the first member.
     * @param payoutAccountId account ID of the designated payout recipient (e.g. a property
     *                        manager's bank account); must not be blank and must differ from
     *                        {@code creatorId}.  Only this account may disburse pool funds.
     * @param targetAmount    optional target total (e.g. full monthly rent amount).
     *                        Pass {@code null} for no specific target.  If provided, must be positive.
     * @return the unique {@link UUID} assigned to the newly created pool
     * @throws NullPointerException     if {@code name}, {@code description}, {@code creatorId},
     *                                  or {@code payoutAccountId} is {@code null}
     * @throws IllegalArgumentException if {@code name}, {@code creatorId}, or
     *                                  {@code payoutAccountId} is blank; if they are the same;
     *                                  or if a non-null {@code targetAmount} is not positive
     */
    public UUID createPool(String name, String description, String creatorId,
            String payoutAccountId, BigDecimal targetAmount) {
        MoneyPool pool = new MoneyPool(
                UUID.randomUUID(), name, description, creatorId,
                payoutAccountId, targetAmount, LocalDate.now());
        pools.put(pool.getId(), pool);
        return pool.getId();
    }

    /**
     * Retrieves a pool by its unique identifier.
     *
     * @param poolId the UUID of the pool; must not be {@code null}
     * @return the matching {@link MoneyPool}
     * @throws NullPointerException   if {@code poolId} is {@code null}
     * @throws NoSuchElementException if no pool with the given {@code poolId} exists
     */
    public MoneyPool getPool(UUID poolId) {
        Objects.requireNonNull(poolId, "poolId must not be null");
        MoneyPool pool = pools.get(poolId);
        if (pool == null) {
            throw new NoSuchElementException("No pool found with id: " + poolId);
        }
        return pool;
    }

    /**
     * Returns an unmodifiable list of all registered pools (all statuses).
     *
     * @return all pools in creation order, never {@code null}
     */
    public List<MoneyPool> listAll() {
        return Collections.unmodifiableList(List.copyOf(pools.values()));
    }

    /**
     * Returns an unmodifiable list of all {@link PoolStatus#OPEN} pools.
     *
     * @return open pools in creation order, never {@code null}
     */
    public List<MoneyPool> listOpen() {
        return pools.values().stream()
                .filter(MoneyPool::isOpen)
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns an unmodifiable list of pools created by the given account ID.
     *
     * @param creatorId the creator account ID to filter by; must not be blank
     * @return pools created by {@code creatorId}, in creation order
     * @throws NullPointerException     if {@code creatorId} is {@code null}
     * @throws IllegalArgumentException if {@code creatorId} is blank
     */
    public List<MoneyPool> listByCreator(String creatorId) {
        Objects.requireNonNull(creatorId, "creatorId must not be null");
        if (creatorId.isBlank()) {
            throw new IllegalArgumentException("creatorId must not be blank");
        }
        return pools.values().stream()
                .filter(p -> p.getCreatorId().equals(creatorId))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns an unmodifiable list of pools that include the given account ID as a member.
     *
     * @param memberId the member account ID to filter by; must not be blank
     * @return pools where {@code memberId} is a member, in creation order
     * @throws NullPointerException     if {@code memberId} is {@code null}
     * @throws IllegalArgumentException if {@code memberId} is blank
     */
    public List<MoneyPool> listByMember(String memberId) {
        Objects.requireNonNull(memberId, "memberId must not be null");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("memberId must not be blank");
        }
        return pools.values().stream()
                .filter(p -> p.isMember(memberId))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns the number of pools registered (all statuses).
     *
     * @return total pool count
     */
    public int size() {
        return pools.size();
    }
}
