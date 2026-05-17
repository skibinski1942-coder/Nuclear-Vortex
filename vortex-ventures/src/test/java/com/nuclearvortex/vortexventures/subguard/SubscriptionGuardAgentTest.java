package com.nuclearvortex.vortexventures.subguard;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class SubscriptionGuardAgentTest {

    private SubscriptionGuardAgent agent;

    @BeforeEach
    void setUp() {
        agent = new SubscriptionGuardAgent("alice@example.com");
    }

    // -----------------------------------------------------------------------
    // Constructor & constants
    // -----------------------------------------------------------------------

    @Test
    void monthlyFeeIsOneNinetyNine() {
        assertEquals(0,
                SubscriptionGuardAgent.MONTHLY_AGENT_FEE.compareTo(new BigDecimal("1.99")));
    }

    @Test
    void platformFeeRateIsTenPercent() {
        assertEquals(0,
                SubscriptionGuardAgent.PLATFORM_FEE_RATE.compareTo(new BigDecimal("0.10")));
    }

    @Test
    void constructorStoresUserIdentifier() {
        assertEquals("alice@example.com", agent.getUserIdentifier());
    }

    @Test
    void constructorNullUserThrows() {
        assertThrows(NullPointerException.class,
                () -> new SubscriptionGuardAgent(null));
    }

    @Test
    void constructorBlankUserThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> new SubscriptionGuardAgent("   "));
    }

    // -----------------------------------------------------------------------
    // trackSubscription()
    // -----------------------------------------------------------------------

    @Test
    void trackSubscriptionReturnsUniqueIds() {
        UUID id1 = agent.trackSubscription("Netflix", "iPhone", new BigDecimal("15.99"));
        UUID id2 = agent.trackSubscription("Netflix", "iPad", new BigDecimal("15.99"));
        assertNotEquals(id1, id2);
        assertEquals(2, agent.subscriptionCount());
    }

    @Test
    void trackedSubscriptionIsActiveByDefault() {
        UUID id = agent.trackSubscription("Spotify", "MacBook", new BigDecimal("9.99"));
        Subscription sub = agent.getSubscription(id);
        assertEquals(SubscriptionStatus.ACTIVE, sub.getStatus());
        assertTrue(sub.isActive());
    }

    @Test
    void trackedSubscriptionStoresFields() {
        UUID id = agent.trackSubscription("Disney+", "Samsung TV", new BigDecimal("13.99"));
        Subscription sub = agent.getSubscription(id);
        assertEquals("Disney+", sub.getServiceName());
        assertEquals("Samsung TV", sub.getDeviceName());
        assertEquals(0, sub.getMonthlyAmount().compareTo(new BigDecimal("13.99")));
        assertNotNull(sub.getStartDate());
    }

    @Test
    void trackSubscriptionNullServiceThrows() {
        assertThrows(NullPointerException.class,
                () -> agent.trackSubscription(null, "Phone", new BigDecimal("9.99")));
    }

    @Test
    void trackSubscriptionBlankDeviceThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> agent.trackSubscription("Netflix", "  ", new BigDecimal("9.99")));
    }

    @Test
    void trackSubscriptionZeroAmountThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> agent.trackSubscription("Netflix", "Phone", BigDecimal.ZERO));
    }

    @Test
    void trackSubscriptionNegativeAmountThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> agent.trackSubscription("Netflix", "Phone", new BigDecimal("-1.00")));
    }

    // -----------------------------------------------------------------------
    // getSubscription() / cancelSubscription()
    // -----------------------------------------------------------------------

    @Test
    void getSubscriptionUnknownIdThrows() {
        assertThrows(NoSuchElementException.class,
                () -> agent.getSubscription(UUID.randomUUID()));
    }

    @Test
    void getSubscriptionNullThrows() {
        assertThrows(NullPointerException.class,
                () -> agent.getSubscription(null));
    }

    @Test
    void cancelSubscriptionChangesStatus() {
        UUID id = agent.trackSubscription("Apple TV+", "iPhone", new BigDecimal("8.99"));
        agent.cancelSubscription(id);
        assertEquals(SubscriptionStatus.CANCELLED, agent.getSubscription(id).getStatus());
    }

    @Test
    void cancelAlreadyCancelledThrows() {
        UUID id = agent.trackSubscription("HBO Max", "Tablet", new BigDecimal("15.99"));
        agent.cancelSubscription(id);
        assertThrows(IllegalStateException.class, () -> agent.cancelSubscription(id));
    }

    // -----------------------------------------------------------------------
    // listAllSubscriptions() / listActiveSubscriptions()
    // -----------------------------------------------------------------------

    @Test
    void listAllSubscriptionsIncludesCancelledAndFlagged() {
        UUID id1 = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID id2 = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        agent.cancelSubscription(id1);
        agent.flagDoubleDip(id2, agent.trackSubscription("Netflix", "Laptop", new BigDecimal("15.99")),
                "Same Netflix account billed on two devices");

        assertEquals(3, agent.listAllSubscriptions().size());
    }

    @Test
    void listActiveSubscriptionsExcludesCancelledAndFlagged() {
        UUID active = agent.trackSubscription("Spotify", "Phone", new BigDecimal("9.99"));
        UUID cancelled = agent.trackSubscription("Apple TV+", "TV", new BigDecimal("8.99"));
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "Laptop", new BigDecimal("15.99"));
        agent.cancelSubscription(cancelled);
        agent.flagDoubleDip(primary, dup, "Duplicate Netflix subscription");

        List<Subscription> active_list = agent.listActiveSubscriptions();
        assertEquals(1, active_list.size());
        assertEquals(active, active_list.get(0).getId());
    }

    @Test
    void listAllSubscriptionsIsUnmodifiable() {
        agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        assertThrows(UnsupportedOperationException.class,
                () -> agent.listAllSubscriptions().remove(0));
    }

    // -----------------------------------------------------------------------
    // listByService() / listByDevice()
    // -----------------------------------------------------------------------

    @Test
    void listByServiceCaseInsensitive() {
        agent.trackSubscription("netflix", "Phone", new BigDecimal("15.99"));
        agent.trackSubscription("NETFLIX", "TV", new BigDecimal("15.99"));
        agent.trackSubscription("Spotify", "Phone", new BigDecimal("9.99"));

        assertEquals(2, agent.listByService("Netflix").size());
    }

    @Test
    void listByServiceBlankThrows() {
        assertThrows(IllegalArgumentException.class, () -> agent.listByService("  "));
    }

    @Test
    void listByDeviceCaseInsensitive() {
        agent.trackSubscription("Netflix", "iphone 15", new BigDecimal("15.99"));
        agent.trackSubscription("Spotify", "IPHONE 15", new BigDecimal("9.99"));
        agent.trackSubscription("Disney+", "Samsung TV", new BigDecimal("13.99"));

        assertEquals(2, agent.listByDevice("iPhone 15").size());
    }

    @Test
    void listByDeviceNullThrows() {
        assertThrows(NullPointerException.class, () -> agent.listByDevice(null));
    }

    // -----------------------------------------------------------------------
    // totalMonthlyActiveCost()
    // -----------------------------------------------------------------------

    @Test
    void totalMonthlyActiveCostSumsActiveOnly() {
        agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        agent.trackSubscription("Spotify", "Phone", new BigDecimal("9.99"));
        UUID cancelled = agent.trackSubscription("Apple TV+", "TV", new BigDecimal("8.99"));
        agent.cancelSubscription(cancelled);

        assertEquals(0,
                agent.totalMonthlyActiveCost().compareTo(new BigDecimal("25.98")));
    }

    @Test
    void totalMonthlyActiveCostEmptyIsZero() {
        assertEquals(0,
                agent.totalMonthlyActiveCost().compareTo(new BigDecimal("0.00")));
    }

    // -----------------------------------------------------------------------
    // flagDoubleDip()
    // -----------------------------------------------------------------------

    @Test
    void flagDoubleDipReturnsClaim() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));

        UUID claimId = agent.flagDoubleDip(primary, dup,
                "Same Netflix account charged on two devices");

        assertNotNull(claimId);
        assertEquals(1, agent.claimCount());
    }

    @Test
    void flagDoubleDipMarksBothSubscriptionsAsFlagged() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        agent.flagDoubleDip(primary, dup, "Double-dip detected");

        assertEquals(SubscriptionStatus.FLAGGED_DOUBLE_DIP,
                agent.getSubscription(primary).getStatus());
        assertEquals(SubscriptionStatus.FLAGGED_DOUBLE_DIP,
                agent.getSubscription(dup).getStatus());
    }

    @Test
    void flagDoubleDipClaimIsInitiallyOpen() {
        UUID primary = agent.trackSubscription("Hulu", "Phone", new BigDecimal("17.99"));
        UUID dup = agent.trackSubscription("Hulu", "TV", new BigDecimal("17.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Hulu billed twice");

        assertEquals(DoubleDipClaim.ClaimStatus.OPEN, agent.getClaim(claimId).getClaimStatus());
    }

    @Test
    void flagDoubleDipSameIdThrows() {
        UUID id = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        assertThrows(IllegalArgumentException.class,
                () -> agent.flagDoubleDip(id, id, "self-reference"));
    }

    @Test
    void flagDoubleDipUnknownPrimaryThrows() {
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        assertThrows(NoSuchElementException.class,
                () -> agent.flagDoubleDip(UUID.randomUUID(), dup, "bad primary"));
    }

    @Test
    void flagDoubleDipCancelledSubscriptionThrows() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        agent.cancelSubscription(dup);

        assertThrows(IllegalStateException.class,
                () -> agent.flagDoubleDip(primary, dup, "cancelled dup"));
    }

    @Test
    void flagDoubleDipBlankReasonThrows() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        assertThrows(IllegalArgumentException.class,
                () -> agent.flagDoubleDip(primary, dup, "  "));
    }

    // -----------------------------------------------------------------------
    // recordRecovery() / rejectClaim()
    // -----------------------------------------------------------------------

    @Test
    void recordRecoveryTransitionsClaimToRecovered() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Double charge");

        agent.recordRecovery(claimId, new BigDecimal("15.99"));

        DoubleDipClaim claim = agent.getClaim(claimId);
        assertEquals(DoubleDipClaim.ClaimStatus.RECOVERED, claim.getClaimStatus());
        assertEquals(0, claim.getRecoveredAmount().compareTo(new BigDecimal("15.99")));
    }

    @Test
    void recordRecoveryOnAlreadyRecoveredClaimThrows() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Double charge");
        agent.recordRecovery(claimId, new BigDecimal("15.99"));

        assertThrows(IllegalStateException.class,
                () -> agent.recordRecovery(claimId, new BigDecimal("5.00")));
    }

    @Test
    void recordRecoveryZeroAmountThrows() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Double charge");

        assertThrows(IllegalArgumentException.class,
                () -> agent.recordRecovery(claimId, BigDecimal.ZERO));
    }

    @Test
    void rejectClaimTransitionsToRejected() {
        UUID primary = agent.trackSubscription("Hulu", "Phone", new BigDecimal("17.99"));
        UUID dup = agent.trackSubscription("Hulu", "TV", new BigDecimal("17.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Hulu double-dip");

        agent.rejectClaim(claimId);

        assertEquals(DoubleDipClaim.ClaimStatus.REJECTED,
                agent.getClaim(claimId).getClaimStatus());
    }

    @Test
    void rejectAlreadyRejectedClaimThrows() {
        UUID primary = agent.trackSubscription("Hulu", "Phone", new BigDecimal("17.99"));
        UUID dup = agent.trackSubscription("Hulu", "TV", new BigDecimal("17.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Hulu double-dip");
        agent.rejectClaim(claimId);

        assertThrows(IllegalStateException.class, () -> agent.rejectClaim(claimId));
    }

    @Test
    void getClaimUnknownIdThrows() {
        assertThrows(NoSuchElementException.class,
                () -> agent.getClaim(UUID.randomUUID()));
    }

    // -----------------------------------------------------------------------
    // listOpenClaims()
    // -----------------------------------------------------------------------

    @Test
    void listOpenClaimsExcludesResolvedClaims() {
        UUID p1 = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID d1 = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID claim1 = agent.flagDoubleDip(p1, d1, "Double Netflix");

        UUID p2 = agent.trackSubscription("Hulu", "Phone", new BigDecimal("17.99"));
        UUID d2 = agent.trackSubscription("Hulu", "Tablet", new BigDecimal("17.99"));
        agent.flagDoubleDip(p2, d2, "Double Hulu");

        agent.recordRecovery(claim1, new BigDecimal("15.99"));

        List<DoubleDipClaim> open = agent.listOpenClaims();
        assertEquals(1, open.size());
        assertEquals(DoubleDipClaim.ClaimStatus.OPEN, open.get(0).getClaimStatus());
    }

    // -----------------------------------------------------------------------
    // Platform fee & financial summaries
    // -----------------------------------------------------------------------

    @Test
    void platformFeeIsTenPercentOfRecoveredAmount() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Double charge");
        agent.recordRecovery(claimId, new BigDecimal("100.00"));

        DoubleDipClaim claim = agent.getClaim(claimId);
        assertEquals(0, claim.getPlatformFee().compareTo(new BigDecimal("10.00")));
    }

    @Test
    void totalRecoveredSumsAllRecoveredClaims() {
        UUID p1 = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID d1 = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID c1 = agent.flagDoubleDip(p1, d1, "Netflix double-dip");

        UUID p2 = agent.trackSubscription("Spotify", "Phone", new BigDecimal("9.99"));
        UUID d2 = agent.trackSubscription("Spotify", "Laptop", new BigDecimal("9.99"));
        UUID c2 = agent.flagDoubleDip(p2, d2, "Spotify double-dip");

        agent.recordRecovery(c1, new BigDecimal("15.99"));
        agent.recordRecovery(c2, new BigDecimal("9.99"));

        assertEquals(0, agent.totalRecovered().compareTo(new BigDecimal("25.98")));
    }

    @Test
    void totalPlatformFeesIsTenPercentOfTotalRecovered() {
        UUID p1 = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID d1 = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID c1 = agent.flagDoubleDip(p1, d1, "Netflix");

        agent.recordRecovery(c1, new BigDecimal("200.00"));

        // 10% of 200 = 20.00
        assertEquals(0, agent.totalPlatformFees().compareTo(new BigDecimal("20.00")));
    }

    @Test
    void totalClientShareIsNinetyPercentOfRecovered() {
        UUID p1 = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID d1 = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID c1 = agent.flagDoubleDip(p1, d1, "Netflix");
        agent.recordRecovery(c1, new BigDecimal("100.00"));

        // client gets 90%
        assertEquals(0, agent.totalClientShare().compareTo(new BigDecimal("90.00")));
    }

    @Test
    void rejectedClaimDoesNotContributeToRecovery() {
        UUID p1 = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID d1 = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID c1 = agent.flagDoubleDip(p1, d1, "Netflix");
        agent.rejectClaim(c1);

        assertEquals(0, agent.totalRecovered().compareTo(new BigDecimal("0.00")));
        assertEquals(0, agent.totalPlatformFees().compareTo(new BigDecimal("0.00")));
    }

    @Test
    void totalRecoveredEmptyIsZero() {
        assertEquals(0, agent.totalRecovered().compareTo(new BigDecimal("0.00")));
    }

    // -----------------------------------------------------------------------
    // DoubleDipClaim.toString() / Subscription.toString()
    // -----------------------------------------------------------------------

    @Test
    void claimToStringContainsKeyFields() {
        UUID primary = agent.trackSubscription("Netflix", "Phone", new BigDecimal("15.99"));
        UUID dup = agent.trackSubscription("Netflix", "TV", new BigDecimal("15.99"));
        UUID claimId = agent.flagDoubleDip(primary, dup, "Double charge");
        String str = agent.getClaim(claimId).toString();
        assertTrue(str.contains("OPEN"));
    }

    @Test
    void subscriptionToStringContainsKeyFields() {
        UUID id = agent.trackSubscription("Spotify", "iPhone", new BigDecimal("9.99"));
        String str = agent.getSubscription(id).toString();
        assertTrue(str.contains("Spotify"));
        assertTrue(str.contains("iPhone"));
        assertTrue(str.contains("9.99"));
        assertTrue(str.contains("ACTIVE"));
    }
}
