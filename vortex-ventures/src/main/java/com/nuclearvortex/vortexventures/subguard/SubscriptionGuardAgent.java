package com.nuclearvortex.vortexventures.subguard;

import java.math.BigDecimal;
import java.math.RoundingMode;
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
 * SubscriptionGuard — the $1.99/month add-on agent for Vortex Ventures.
 *
 * <h2>What it does</h2>
 * <ol>
 *   <li><strong>Tracks subscriptions</strong> across all connected devices (phone, tablet,
 *       smart TV, laptop, etc.).</li>
 *   <li><strong>Detects double-dips</strong> — services that are billing the same user more
 *       than once for the same or equivalent content (e.g. Netflix on two devices under
 *       separate accounts, or overlapping streaming bundles).</li>
 *   <li><strong>Files recovery claims</strong> against the offending service provider and
 *       tracks the refund lifecycle (open → recovered / rejected).</li>
 *   <li><strong>Earns a 10 % platform fee</strong> on every dollar successfully recovered
 *       for the client — the client keeps the other 90 %.</li>
 * </ol>
 *
 * <h2>Pricing</h2>
 * <p>The agent costs {@value #MONTHLY_AGENT_FEE_AMOUNT} USD per month per user
 * ({@link #MONTHLY_AGENT_FEE}).</p>
 *
 * <h2>Usage example</h2>
 * <pre>{@code
 * SubscriptionGuardAgent agent = new SubscriptionGuardAgent("alice@example.com");
 *
 * UUID netflixPhone = agent.trackSubscription("Netflix", "iPhone 15", new BigDecimal("15.99"));
 * UUID netflixTV    = agent.trackSubscription("Netflix", "Samsung TV", new BigDecimal("15.99"));
 *
 * UUID claimId = agent.flagDoubleDip(netflixPhone, netflixTV,
 *         "Netflix billed on two separate devices under the same account");
 *
 * agent.recordRecovery(claimId, new BigDecimal("15.99"));
 * System.out.println(agent.totalRecovered());   // 15.99
 * System.out.println(agent.totalPlatformFees()); // 1.60
 * }</pre>
 *
 * <p>This class is <em>not</em> thread-safe.</p>
 */
public final class SubscriptionGuardAgent {

    /** Monthly subscription fee for the SubscriptionGuard add-on agent. */
    public static final String MONTHLY_AGENT_FEE_AMOUNT = "1.99";

    /** Monthly agent fee as a {@link BigDecimal} for arithmetic use. */
    public static final BigDecimal MONTHLY_AGENT_FEE = new BigDecimal(MONTHLY_AGENT_FEE_AMOUNT);

    /** Platform commission rate on recovered amounts — 10 %. */
    public static final BigDecimal PLATFORM_FEE_RATE = DoubleDipClaim.PLATFORM_FEE_RATE;

    private final String userIdentifier;
    private final Map<UUID, Subscription> subscriptions = new LinkedHashMap<>();
    private final Map<UUID, DoubleDipClaim> claims = new LinkedHashMap<>();

    /**
     * Creates a new SubscriptionGuard agent for the given user.
     *
     * @param userIdentifier a unique identifier for the subscribing user (e.g. email or user ID);
     *                       must not be blank
     * @throws NullPointerException     if {@code userIdentifier} is {@code null}
     * @throws IllegalArgumentException if {@code userIdentifier} is blank
     */
    public SubscriptionGuardAgent(String userIdentifier) {
        Objects.requireNonNull(userIdentifier, "userIdentifier must not be null");
        if (userIdentifier.isBlank()) {
            throw new IllegalArgumentException("userIdentifier must not be blank");
        }
        this.userIdentifier = userIdentifier;
    }

    /**
     * Returns the user identifier this agent is managing subscriptions for.
     *
     * @return user identifier, never blank
     */
    public String getUserIdentifier() {
        return userIdentifier;
    }

    // -----------------------------------------------------------------------
    // Subscription tracking
    // -----------------------------------------------------------------------

    /**
     * Registers a new subscription detected on a connected device.
     *
     * @param serviceName   the name of the subscription service (e.g. "Spotify"); must not be blank
     * @param deviceName    the device where the subscription was detected; must not be blank
     * @param monthlyAmount the monthly charge; must be positive
     * @return the unique {@link UUID} assigned to this subscription
     * @throws NullPointerException     if any argument is {@code null}
     * @throws IllegalArgumentException if {@code serviceName} or {@code deviceName} is blank,
     *                                  or if {@code monthlyAmount} is not positive
     */
    public UUID trackSubscription(String serviceName, String deviceName, BigDecimal monthlyAmount) {
        Subscription sub = new Subscription(
                UUID.randomUUID(), serviceName, deviceName, monthlyAmount, LocalDate.now());
        subscriptions.put(sub.getId(), sub);
        return sub.getId();
    }

    /**
     * Retrieves a tracked subscription by its unique identifier.
     *
     * @param id the UUID of the subscription; must not be {@code null}
     * @return the matching {@link Subscription}
     * @throws NullPointerException   if {@code id} is {@code null}
     * @throws NoSuchElementException if no subscription with the given {@code id} exists
     */
    public Subscription getSubscription(UUID id) {
        Objects.requireNonNull(id, "id must not be null");
        Subscription sub = subscriptions.get(id);
        if (sub == null) {
            throw new NoSuchElementException("No subscription found with id: " + id);
        }
        return sub;
    }

    /**
     * Cancels a tracked subscription, marking it as {@link SubscriptionStatus#CANCELLED}.
     *
     * @param id the UUID of the subscription to cancel; must not be {@code null}
     * @throws NullPointerException   if {@code id} is {@code null}
     * @throws NoSuchElementException if no subscription with the given {@code id} exists
     * @throws IllegalStateException  if the subscription is already cancelled
     */
    public void cancelSubscription(UUID id) {
        Subscription sub = getSubscription(id);
        if (sub.getStatus() == SubscriptionStatus.CANCELLED) {
            throw new IllegalStateException("Subscription " + id + " is already cancelled");
        }
        sub.setStatus(SubscriptionStatus.CANCELLED);
    }

    /**
     * Returns an unmodifiable list of all tracked subscriptions (all statuses).
     *
     * @return all subscriptions in insertion order, never {@code null}
     */
    public List<Subscription> listAllSubscriptions() {
        return Collections.unmodifiableList(List.copyOf(subscriptions.values()));
    }

    /**
     * Returns an unmodifiable list of all {@link SubscriptionStatus#ACTIVE} subscriptions.
     *
     * @return active subscriptions in insertion order, never {@code null}
     */
    public List<Subscription> listActiveSubscriptions() {
        return subscriptions.values().stream()
                .filter(Subscription::isActive)
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns an unmodifiable list of subscriptions matching the given service name
     * (case-insensitive).
     *
     * @param serviceName the service name to filter by; must not be blank
     * @return matching subscriptions in insertion order, never {@code null}
     * @throws NullPointerException     if {@code serviceName} is {@code null}
     * @throws IllegalArgumentException if {@code serviceName} is blank
     */
    public List<Subscription> listByService(String serviceName) {
        Objects.requireNonNull(serviceName, "serviceName must not be null");
        if (serviceName.isBlank()) {
            throw new IllegalArgumentException("serviceName must not be blank");
        }
        return subscriptions.values().stream()
                .filter(s -> s.getServiceName().equalsIgnoreCase(serviceName))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns an unmodifiable list of subscriptions detected on the given device
     * (case-insensitive).
     *
     * @param deviceName the device name to filter by; must not be blank
     * @return matching subscriptions in insertion order, never {@code null}
     * @throws NullPointerException     if {@code deviceName} is {@code null}
     * @throws IllegalArgumentException if {@code deviceName} is blank
     */
    public List<Subscription> listByDevice(String deviceName) {
        Objects.requireNonNull(deviceName, "deviceName must not be null");
        if (deviceName.isBlank()) {
            throw new IllegalArgumentException("deviceName must not be blank");
        }
        return subscriptions.values().stream()
                .filter(s -> s.getDeviceName().equalsIgnoreCase(deviceName))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns the total monthly cost of all currently active subscriptions.
     *
     * @return sum of monthly amounts for active subscriptions, rounded to 2 decimal places
     */
    public BigDecimal totalMonthlyActiveCost() {
        return subscriptions.values().stream()
                .filter(Subscription::isActive)
                .map(Subscription::getMonthlyAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    // -----------------------------------------------------------------------
    // Double-dip detection and recovery claims
    // -----------------------------------------------------------------------

    /**
     * Flags a pair of subscriptions as a double-dip and opens a recovery claim.
     *
     * <p>Both subscriptions are marked {@link SubscriptionStatus#FLAGGED_DOUBLE_DIP}.
     * Only the duplicate will ultimately be refunded; the primary subscription
     * continues normally.</p>
     *
     * @param primarySubscriptionId   UUID of the legitimate subscription; must not be {@code null}
     * @param duplicateSubscriptionId UUID of the duplicate subscription; must not be {@code null}
     * @param reason                  human-readable explanation of the double-dip; must not be blank
     * @return the UUID of the newly created {@link DoubleDipClaim}
     * @throws NullPointerException     if any argument is {@code null}
     * @throws NoSuchElementException   if either subscription UUID does not exist
     * @throws IllegalArgumentException if both UUIDs are equal, or if {@code reason} is blank
     * @throws IllegalStateException    if either subscription is already cancelled
     */
    public UUID flagDoubleDip(UUID primarySubscriptionId, UUID duplicateSubscriptionId,
            String reason) {
        Objects.requireNonNull(reason, "reason must not be null");
        if (reason.isBlank()) {
            throw new IllegalArgumentException("reason must not be blank");
        }

        Subscription primary = getSubscription(primarySubscriptionId);
        Subscription duplicate = getSubscription(duplicateSubscriptionId);

        if (primary.getStatus() == SubscriptionStatus.CANCELLED) {
            throw new IllegalStateException(
                    "Primary subscription " + primarySubscriptionId + " is already cancelled");
        }
        if (duplicate.getStatus() == SubscriptionStatus.CANCELLED) {
            throw new IllegalStateException(
                    "Duplicate subscription " + duplicateSubscriptionId + " is already cancelled");
        }

        DoubleDipClaim claim = new DoubleDipClaim(
                UUID.randomUUID(),
                primarySubscriptionId,
                duplicateSubscriptionId,
                reason,
                LocalDate.now());
        claims.put(claim.getId(), claim);

        primary.setStatus(SubscriptionStatus.FLAGGED_DOUBLE_DIP);
        duplicate.setStatus(SubscriptionStatus.FLAGGED_DOUBLE_DIP);

        return claim.getId();
    }

    /**
     * Retrieves a recovery claim by its unique identifier.
     *
     * @param claimId the UUID of the claim; must not be {@code null}
     * @return the matching {@link DoubleDipClaim}
     * @throws NullPointerException   if {@code claimId} is {@code null}
     * @throws NoSuchElementException if no claim with the given {@code claimId} exists
     */
    public DoubleDipClaim getClaim(UUID claimId) {
        Objects.requireNonNull(claimId, "claimId must not be null");
        DoubleDipClaim claim = claims.get(claimId);
        if (claim == null) {
            throw new NoSuchElementException("No claim found with id: " + claimId);
        }
        return claim;
    }

    /**
     * Records a successful refund from the service provider and closes the claim as
     * {@link DoubleDipClaim.ClaimStatus#RECOVERED}.
     *
     * <p>The platform earns {@value DoubleDipClaim#PLATFORM_FEE_RATE} × recovered amount.
     * The client keeps the remaining 90 %.</p>
     *
     * @param claimId         the UUID of the open claim; must not be {@code null}
     * @param recoveredAmount the amount refunded by the provider; must be positive
     * @throws NullPointerException   if either argument is {@code null}
     * @throws NoSuchElementException if no claim with the given {@code claimId} exists
     * @throws IllegalArgumentException if {@code recoveredAmount} is not positive
     * @throws IllegalStateException  if the claim is not in {@link DoubleDipClaim.ClaimStatus#OPEN} state
     */
    public void recordRecovery(UUID claimId, BigDecimal recoveredAmount) {
        getClaim(claimId).setRecoveredAmount(recoveredAmount);
    }

    /**
     * Marks a claim as rejected — the service provider declined to issue a refund.
     *
     * @param claimId the UUID of the open claim; must not be {@code null}
     * @throws NullPointerException   if {@code claimId} is {@code null}
     * @throws NoSuchElementException if no claim with the given {@code claimId} exists
     * @throws IllegalStateException  if the claim is not in {@link DoubleDipClaim.ClaimStatus#OPEN} state
     */
    public void rejectClaim(UUID claimId) {
        getClaim(claimId).reject();
    }

    /**
     * Returns an unmodifiable list of all recovery claims (all statuses).
     *
     * @return all claims in insertion order, never {@code null}
     */
    public List<DoubleDipClaim> listAllClaims() {
        return Collections.unmodifiableList(List.copyOf(claims.values()));
    }

    /**
     * Returns an unmodifiable list of all open (pending) recovery claims.
     *
     * @return open claims in insertion order, never {@code null}
     */
    public List<DoubleDipClaim> listOpenClaims() {
        return claims.values().stream()
                .filter(c -> c.getClaimStatus() == DoubleDipClaim.ClaimStatus.OPEN)
                .collect(Collectors.toUnmodifiableList());
    }

    // -----------------------------------------------------------------------
    // Financial summaries
    // -----------------------------------------------------------------------

    /**
     * Returns the total amount successfully recovered for the client across all claims.
     *
     * @return sum of all recovered amounts, rounded to 2 decimal places
     */
    public BigDecimal totalRecovered() {
        return claims.values().stream()
                .map(DoubleDipClaim::getRecoveredAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the total platform fees earned (10 % of all recovered amounts).
     *
     * @return sum of platform fees across all recovered claims, rounded to 2 decimal places
     */
    public BigDecimal totalPlatformFees() {
        return claims.values().stream()
                .map(DoubleDipClaim::getPlatformFee)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the total amount returned to the client (recovered minus platform fees).
     *
     * @return clientShare = totalRecovered - totalPlatformFees, rounded to 2 decimal places
     */
    public BigDecimal totalClientShare() {
        return totalRecovered().subtract(totalPlatformFees())
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the number of subscriptions currently tracked by this agent.
     *
     * @return total subscription count (all statuses)
     */
    public int subscriptionCount() {
        return subscriptions.size();
    }

    /**
     * Returns the number of recovery claims filed by this agent.
     *
     * @return total claim count (all statuses)
     */
    public int claimCount() {
        return claims.size();
    }
}
