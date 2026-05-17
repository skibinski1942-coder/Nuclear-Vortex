package com.nuclearvortex.vortexventures.pool;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class MoneyPoolRegistryTest {

    private MoneyPoolRegistry registry;

    // Fixed test IDs to keep tests readable
    private static final String CREATOR   = "roommate-alice";
    private static final String MEMBER_B  = "roommate-bob";
    private static final String MEMBER_C  = "roommate-carol";
    private static final String PAYOUT    = "property-manager-bank-acct";
    private static final String STRANGER  = "stranger-account";

    @BeforeEach
    void setUp() {
        registry = new MoneyPoolRegistry();
    }

    // -----------------------------------------------------------------------
    // Registry — createPool() / getPool()
    // -----------------------------------------------------------------------

    @Test
    void createPoolReturnsUniqueIds() {
        UUID id1 = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        UUID id2 = registry.createPool("Utilities", "", CREATOR, PAYOUT, null);
        assertNotEquals(id1, id2);
        assertEquals(2, registry.size());
    }

    @Test
    void getPoolReturnsCreatedPool() {
        UUID id = registry.createPool("April Rent", "desc", CREATOR, PAYOUT, new BigDecimal("3000.00"));
        MoneyPool pool = registry.getPool(id);
        assertNotNull(pool);
        assertEquals("April Rent", pool.getName());
        assertEquals(CREATOR, pool.getCreatorId());
        assertEquals(PAYOUT, pool.getPayoutAccountId());
        assertEquals(PoolStatus.OPEN, pool.getStatus());
    }

    @Test
    void getPoolUnknownIdThrows() {
        assertThrows(NoSuchElementException.class, () -> registry.getPool(UUID.randomUUID()));
    }

    @Test
    void getPoolNullThrows() {
        assertThrows(NullPointerException.class, () -> registry.getPool(null));
    }

    @Test
    void createPoolNullNameThrows() {
        assertThrows(NullPointerException.class,
                () -> registry.createPool(null, "", CREATOR, PAYOUT, null));
    }

    @Test
    void createPoolBlankNameThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> registry.createPool("  ", "", CREATOR, PAYOUT, null));
    }

    @Test
    void createPoolCreatorEqualsPayoutThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> registry.createPool("Pool", "", CREATOR, CREATOR, null));
    }

    @Test
    void createPoolNegativeTargetThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> registry.createPool("Pool", "", CREATOR, PAYOUT, new BigDecimal("-1.00")));
    }

    @Test
    void createPoolZeroTargetThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> registry.createPool("Pool", "", CREATOR, PAYOUT, BigDecimal.ZERO));
    }

    // -----------------------------------------------------------------------
    // MoneyPool — member management
    // -----------------------------------------------------------------------

    @Test
    void creatorIsAutomaticallyAMember() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertTrue(registry.getPool(id).isMember(CREATOR));
    }

    @Test
    void addMemberAddsSuccessfully() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.addMember(MEMBER_B);
        assertTrue(pool.isMember(MEMBER_B));
        assertEquals(2, pool.getMemberIds().size());
    }

    @Test
    void addMemberDuplicateIsNoOp() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.addMember(MEMBER_B);
        pool.addMember(MEMBER_B); // duplicate
        assertEquals(2, pool.getMemberIds().size()); // still just creator + bob
    }

    @Test
    void addMemberNullThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(NullPointerException.class, () -> registry.getPool(id).addMember(null));
    }

    @Test
    void addMemberBlankThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(IllegalArgumentException.class, () -> registry.getPool(id).addMember("  "));
    }

    @Test
    void addMemberToClosedPoolThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.close(CREATOR);
        assertThrows(IllegalStateException.class, () -> pool.addMember(MEMBER_B));
    }

    @Test
    void removeMemberSucceeds() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.addMember(MEMBER_B);
        pool.removeMember(MEMBER_B);
        assertFalse(pool.isMember(MEMBER_B));
    }

    @Test
    void removeCreatorThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(IllegalArgumentException.class, () -> registry.getPool(id).removeMember(CREATOR));
    }

    @Test
    void removeNonMemberThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(IllegalStateException.class, () -> registry.getPool(id).removeMember(MEMBER_B));
    }

    @Test
    void getMemberIdsIsUnmodifiable() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(UnsupportedOperationException.class,
                () -> registry.getPool(id).getMemberIds().add(MEMBER_B));
    }

    // -----------------------------------------------------------------------
    // MoneyPool — contribute()
    // -----------------------------------------------------------------------

    @Test
    void memberCanContribute() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, new BigDecimal("3000.00"));
        MoneyPool pool = registry.getPool(id);
        pool.addMember(MEMBER_B);

        pool.contribute(CREATOR, new BigDecimal("1000.00"));
        pool.contribute(MEMBER_B, new BigDecimal("1000.00"));

        assertEquals(0, pool.balance().compareTo(new BigDecimal("2000.00")));
        assertEquals(2, pool.getContributions().size());
    }

    @Test
    void nonMemberCannotContribute() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        assertThrows(IllegalStateException.class,
                () -> pool.contribute(STRANGER, new BigDecimal("500.00")));
    }

    @Test
    void contributeZeroAmountThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(IllegalArgumentException.class,
                () -> registry.getPool(id).contribute(CREATOR, BigDecimal.ZERO));
    }

    @Test
    void contributeNegativeAmountThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(IllegalArgumentException.class,
                () -> registry.getPool(id).contribute(CREATOR, new BigDecimal("-10.00")));
    }

    @Test
    void contributeToClosedPoolThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.close(CREATOR);
        assertThrows(IllegalStateException.class,
                () -> pool.contribute(CREATOR, new BigDecimal("500.00")));
    }

    @Test
    void contributeToDisbursedPoolThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("100.00"));
        pool.disburse(PAYOUT);
        assertThrows(IllegalStateException.class,
                () -> pool.contribute(CREATOR, new BigDecimal("100.00")));
    }

    @Test
    void contributionsAreUnmodifiable() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("100.00"));
        assertThrows(UnsupportedOperationException.class,
                () -> pool.getContributions().clear());
    }

    @Test
    void totalContributedByMemberSumsCorrectly() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("500.00"));
        pool.contribute(CREATOR, new BigDecimal("500.00"));

        assertEquals(0,
                pool.totalContributedByMember(CREATOR).compareTo(new BigDecimal("1000.00")));
    }

    @Test
    void getContributionsByMemberFiltersCorrectly() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.addMember(MEMBER_B);
        pool.contribute(CREATOR, new BigDecimal("1000.00"));
        pool.contribute(MEMBER_B, new BigDecimal("500.00"));

        assertEquals(1, pool.getContributionsByMember(CREATOR).size());
        assertEquals(1, pool.getContributionsByMember(MEMBER_B).size());
        assertEquals(0, pool.getContributionsByMember(MEMBER_C).size());
    }

    // -----------------------------------------------------------------------
    // MoneyPool — balance() / amountRemaining()
    // -----------------------------------------------------------------------

    @Test
    void balanceStartsAtZero() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertEquals(0, registry.getPool(id).balance().compareTo(new BigDecimal("0.00")));
    }

    @Test
    void amountRemainingWithNoTarget() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertEquals(0, registry.getPool(id).amountRemaining().compareTo(new BigDecimal("0.00")));
    }

    @Test
    void amountRemainingDecreasesAsContributionsGrow() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, new BigDecimal("3000.00"));
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("1000.00"));

        assertEquals(0, pool.amountRemaining().compareTo(new BigDecimal("2000.00")));
    }

    @Test
    void amountRemainingIsNeverNegative() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, new BigDecimal("100.00"));
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("200.00")); // over-contribution

        assertEquals(0, pool.amountRemaining().compareTo(new BigDecimal("0.00")));
    }

    // -----------------------------------------------------------------------
    // MoneyPool — disburse() — ONLY payout account may withdraw
    // -----------------------------------------------------------------------

    @Test
    void payoutAccountCanDisburse() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("3000.00"));

        BigDecimal disbursed = pool.disburse(PAYOUT);

        assertEquals(0, disbursed.compareTo(new BigDecimal("3000.00")));
        assertEquals(PoolStatus.DISBURSED, pool.getStatus());
    }

    @Test
    void memberCannotDisburse() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("3000.00"));

        assertThrows(SecurityException.class, () -> pool.disburse(CREATOR));
    }

    @Test
    void strangerCannotDisburse() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("3000.00"));

        assertThrows(SecurityException.class, () -> pool.disburse(STRANGER));
    }

    @Test
    void disburseZeroBalanceThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(IllegalStateException.class,
                () -> registry.getPool(id).disburse(PAYOUT));
    }

    @Test
    void disburseAlreadyDisbursedThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("1000.00"));
        pool.disburse(PAYOUT);

        assertThrows(IllegalStateException.class, () -> pool.disburse(PAYOUT));
    }

    @Test
    void disburseClosedPoolThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.contribute(CREATOR, new BigDecimal("1000.00"));
        pool.close(CREATOR);

        assertThrows(IllegalStateException.class, () -> pool.disburse(PAYOUT));
    }

    // -----------------------------------------------------------------------
    // MoneyPool — close()
    // -----------------------------------------------------------------------

    @Test
    void creatorCanClosePool() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.close(CREATOR);

        assertEquals(PoolStatus.CLOSED, pool.getStatus());
        assertFalse(pool.isOpen());
    }

    @Test
    void nonCreatorCannotClosePool() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.addMember(MEMBER_B);

        assertThrows(SecurityException.class, () -> pool.close(MEMBER_B));
        assertThrows(SecurityException.class, () -> pool.close(STRANGER));
    }

    @Test
    void closeAlreadyClosedThrows() {
        UUID id = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        MoneyPool pool = registry.getPool(id);
        pool.close(CREATOR);

        assertThrows(IllegalStateException.class, () -> pool.close(CREATOR));
    }

    // -----------------------------------------------------------------------
    // Registry — list methods
    // -----------------------------------------------------------------------

    @Test
    void listAllIncludesAllStatuses() {
        UUID id1 = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        UUID id2 = registry.createPool("Utils", "", CREATOR, PAYOUT, null);
        registry.getPool(id2).close(CREATOR);

        assertEquals(2, registry.listAll().size());
    }

    @Test
    void listAllIsUnmodifiable() {
        registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        assertThrows(UnsupportedOperationException.class,
                () -> registry.listAll().remove(0));
    }

    @Test
    void listOpenExcludesClosedAndDisbursed() {
        UUID openId = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        UUID closedId = registry.createPool("Utils", "", CREATOR, PAYOUT, null);
        UUID disbursedId = registry.createPool("Groceries", "", CREATOR, PAYOUT, null);

        registry.getPool(closedId).close(CREATOR);
        MoneyPool gPool = registry.getPool(disbursedId);
        gPool.contribute(CREATOR, new BigDecimal("50.00"));
        gPool.disburse(PAYOUT);

        List<MoneyPool> open = registry.listOpen();
        assertEquals(1, open.size());
        assertEquals(openId, open.get(0).getId());
    }

    @Test
    void listByCreatorFilters() {
        registry.createPool("Pool A", "", CREATOR, PAYOUT, null);
        registry.createPool("Pool B", "", MEMBER_B, PAYOUT, null);

        assertEquals(1, registry.listByCreator(CREATOR).size());
        assertEquals(1, registry.listByCreator(MEMBER_B).size());
        assertEquals(0, registry.listByCreator(MEMBER_C).size());
    }

    @Test
    void listByCreatorBlankThrows() {
        assertThrows(IllegalArgumentException.class, () -> registry.listByCreator("  "));
    }

    @Test
    void listByMemberIncludesPoolsWhereMemberExists() {
        UUID id1 = registry.createPool("Rent", "", CREATOR, PAYOUT, null);
        UUID id2 = registry.createPool("Utils", "", CREATOR, PAYOUT, null);
        registry.getPool(id1).addMember(MEMBER_B);

        List<MoneyPool> alicePools = registry.listByMember(CREATOR); // creator of both
        assertEquals(2, alicePools.size());

        List<MoneyPool> bobPools = registry.listByMember(MEMBER_B); // member of pool 1 only
        assertEquals(1, bobPools.size());
        assertEquals(id1, bobPools.get(0).getId());
    }

    @Test
    void listByMemberNullThrows() {
        assertThrows(NullPointerException.class, () -> registry.listByMember(null));
    }

    // -----------------------------------------------------------------------
    // Full rent-pool scenario
    // -----------------------------------------------------------------------

    @Test
    void fullRentPoolScenario() {
        // Create the pool
        UUID poolId = registry.createPool(
                "April Rent",
                "3-bedroom apt on Oak St",
                CREATOR,
                PAYOUT,
                new BigDecimal("3000.00"));

        MoneyPool pool = registry.getPool(poolId);
        assertTrue(pool.isOpen());

        // Invite roommates
        pool.addMember(MEMBER_B);
        pool.addMember(MEMBER_C);
        assertEquals(3, pool.getMemberIds().size());

        // Each roommate contributes their share
        pool.contribute(CREATOR,  new BigDecimal("1000.00"));
        pool.contribute(MEMBER_B, new BigDecimal("1000.00"));
        pool.contribute(MEMBER_C, new BigDecimal("1000.00"));

        assertEquals(0, pool.balance().compareTo(new BigDecimal("3000.00")));
        assertEquals(0, pool.amountRemaining().compareTo(new BigDecimal("0.00")));

        // Members CANNOT withdraw funds
        assertThrows(SecurityException.class, () -> pool.disburse(CREATOR));
        assertThrows(SecurityException.class, () -> pool.disburse(MEMBER_B));
        assertThrows(SecurityException.class, () -> pool.disburse(MEMBER_C));

        // Only the property manager can disburse
        BigDecimal disbursed = pool.disburse(PAYOUT);

        assertEquals(0, disbursed.compareTo(new BigDecimal("3000.00")));
        assertEquals(PoolStatus.DISBURSED, pool.getStatus());

        // Pool is now closed to further contributions
        assertThrows(IllegalStateException.class,
                () -> pool.contribute(CREATOR, new BigDecimal("100.00")));
    }

    // -----------------------------------------------------------------------
    // toString()
    // -----------------------------------------------------------------------

    @Test
    void toStringContainsKeyFields() {
        UUID id = registry.createPool("April Rent", "desc", CREATOR, PAYOUT, null);
        String str = registry.getPool(id).toString();
        assertTrue(str.contains("April Rent"));
        assertTrue(str.contains(CREATOR));
        assertTrue(str.contains(PAYOUT));
        assertTrue(str.contains("OPEN"));
    }
}
