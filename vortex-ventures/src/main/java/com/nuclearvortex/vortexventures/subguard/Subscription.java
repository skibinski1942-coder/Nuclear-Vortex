package com.nuclearvortex.vortexventures.subguard;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

/**
 * A single subscription tracked by the SubscriptionGuard agent on behalf of a user.
 *
 * <p>A {@code Subscription} represents one recurring charge from a service provider
 * on any of the user's connected devices (phone, tablet, smart TV, etc.). The agent
 * monitors all subscriptions and compares them to detect double-dips — cases where
 * the same or equivalent service is billed more than once.</p>
 *
 * <p>Instances are created and managed exclusively by {@link SubscriptionGuardAgent}.</p>
 */
public final class Subscription {

    private final UUID id;
    private final String serviceName;
    private final String deviceName;
    private final BigDecimal monthlyAmount;
    private final LocalDate startDate;
    private SubscriptionStatus status;

    /**
     * Constructs a new active subscription record.
     *
     * @param id            unique identifier; must not be {@code null}
     * @param serviceName   name of the subscription service (e.g. "Netflix"); must not be blank
     * @param deviceName    the connected device the subscription was detected on; must not be blank
     * @param monthlyAmount the monthly charge amount; must be positive
     * @param startDate     the date tracking began; must not be {@code null}
     * @throws NullPointerException     if any argument is {@code null}
     * @throws IllegalArgumentException if {@code serviceName} or {@code deviceName} is blank,
     *                                  or if {@code monthlyAmount} is not positive
     */
    Subscription(UUID id, String serviceName, String deviceName,
            BigDecimal monthlyAmount, LocalDate startDate) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(serviceName, "serviceName must not be null");
        Objects.requireNonNull(deviceName, "deviceName must not be null");
        if (serviceName.isBlank()) {
            throw new IllegalArgumentException("serviceName must not be blank");
        }
        if (deviceName.isBlank()) {
            throw new IllegalArgumentException("deviceName must not be blank");
        }
        Objects.requireNonNull(monthlyAmount, "monthlyAmount must not be null");
        if (monthlyAmount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("monthlyAmount must be positive");
        }
        this.serviceName = serviceName;
        this.deviceName = deviceName;
        this.monthlyAmount = monthlyAmount;
        this.startDate = Objects.requireNonNull(startDate, "startDate must not be null");
        this.status = SubscriptionStatus.ACTIVE;
    }

    /** @return unique identifier, never {@code null} */
    public UUID getId() {
        return id;
    }

    /** @return name of the subscription service, never blank */
    public String getServiceName() {
        return serviceName;
    }

    /** @return device name this subscription was detected on, never blank */
    public String getDeviceName() {
        return deviceName;
    }

    /** @return monthly billing amount, always positive */
    public BigDecimal getMonthlyAmount() {
        return monthlyAmount;
    }

    /** @return date tracking started for this subscription, never {@code null} */
    public LocalDate getStartDate() {
        return startDate;
    }

    /** @return current {@link SubscriptionStatus} */
    public SubscriptionStatus getStatus() {
        return status;
    }

    /** @return {@code true} if this subscription is currently active */
    public boolean isActive() {
        return status == SubscriptionStatus.ACTIVE;
    }

    /** Package-private: only {@link SubscriptionGuardAgent} may change status. */
    void setStatus(SubscriptionStatus status) {
        this.status = Objects.requireNonNull(status, "status must not be null");
    }

    @Override
    public String toString() {
        return String.format(
                "Subscription{id=%s, service='%s', device='%s', amount=%s/mo, status=%s}",
                id, serviceName, deviceName, monthlyAmount, status);
    }
}
