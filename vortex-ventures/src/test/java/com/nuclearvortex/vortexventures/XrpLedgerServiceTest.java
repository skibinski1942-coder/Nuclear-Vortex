package com.nuclearvortex.vortexventures;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class XrpLedgerServiceTest {

    // Two valid XRP Ledger addresses used throughout the tests.
    // (XRP Base58 alphabet excludes 0, O, I, l — these addresses use only valid characters.)
    private static final String ALICE = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh";
    private static final String BOB   = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe";

    private XrpLedgerService service;

    @BeforeEach
    void setUp() {
        service = new XrpLedgerService();
    }

    // -------------------------------------------------------------------------
    // Address validation
    // -------------------------------------------------------------------------

    @Test
    void validAddressIsAccepted() {
        assertTrue(XrpLedgerService.isValidXrpAddress(ALICE));
        assertTrue(XrpLedgerService.isValidXrpAddress(BOB));
    }

    @Test
    void nullAddressIsRejected() {
        assertFalse(XrpLedgerService.isValidXrpAddress(null));
    }

    @Test
    void addressNotStartingWithRIsRejected() {
        assertFalse(XrpLedgerService.isValidXrpAddress("1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1"));
        assertFalse(XrpLedgerService.isValidXrpAddress("xHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"));
    }

    @Test
    void tooShortAddressIsRejected() {
        // fewer than 25 characters
        assertFalse(XrpLedgerService.isValidXrpAddress("rShort"));
    }

    @Test
    void tooLongAddressIsRejected() {
        // 35 characters starting with 'r'
        assertFalse(XrpLedgerService.isValidXrpAddress("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyThXX"));
    }

    @Test
    void addressWithInvalidBase58CharsIsRejected() {
        // '0', 'O', 'I', 'l' are excluded from the Base58 alphabet
        assertFalse(XrpLedgerService.isValidXrpAddress("rHb9CJAWyB4rj91VRWn96DkukG0bwdtyTh"));
    }

    // -------------------------------------------------------------------------
    // XrpTransaction construction guards
    // -------------------------------------------------------------------------

    @Test
    void transactionRejectsNullSender() {
        assertThrows(NullPointerException.class,
                () -> new XrpTransaction(null, BOB, 1_000_000L, null));
    }

    @Test
    void transactionRejectsNullReceiver() {
        assertThrows(NullPointerException.class,
                () -> new XrpTransaction(ALICE, null, 1_000_000L, null));
    }

    @Test
    void transactionRejectsNonPositiveAmount() {
        assertThrows(IllegalArgumentException.class,
                () -> new XrpTransaction(ALICE, BOB, 0L, null));
        assertThrows(IllegalArgumentException.class,
                () -> new XrpTransaction(ALICE, BOB, -1L, null));
    }

    @Test
    void transactionAmountXrpConversion() {
        XrpTransaction tx = new XrpTransaction(ALICE, BOB, 5_000_000L, null);
        assertEquals(5.0, tx.getAmountXrp(), 0.0001);
    }

    // -------------------------------------------------------------------------
    // Happy path
    // -------------------------------------------------------------------------

    @Test
    void smallValidTransactionIsApproved() {
        XrpTransaction tx = new XrpTransaction(ALICE, BOB, 1_000_000L, "coffee money");
        ApprovalResult result = service.approve(tx);

        assertEquals(ApprovalStatus.APPROVED, result.getStatus());
        assertTrue(result.isApproved());
        assertFalse(result.getReason().isBlank());
    }

    @Test
    void approvedTransactionAccumulatesDailyTotal() {
        long drops = 2_000_000L;
        service.approve(new XrpTransaction(ALICE, BOB, drops, null));
        service.approve(new XrpTransaction(ALICE, BOB, drops, null));

        assertEquals(drops * 2, service.getDailySentDrops(ALICE));
    }

    @Test
    void resetClearsDailyTotals() {
        service.approve(new XrpTransaction(ALICE, BOB, 1_000_000L, null));
        service.resetDailyTotals();

        assertEquals(0L, service.getDailySentDrops(ALICE));
    }

    // -------------------------------------------------------------------------
    // Rejection: invalid addresses
    // -------------------------------------------------------------------------

    @Test
    void invalidSenderAddressIsRejected() {
        XrpTransaction tx = new XrpTransaction("not-an-address", BOB, 1_000_000L, null);
        ApprovalResult result = service.approve(tx);

        assertEquals(ApprovalStatus.REJECTED, result.getStatus());
        assertFalse(result.isApproved());
    }

    @Test
    void invalidReceiverAddressIsRejected() {
        XrpTransaction tx = new XrpTransaction(ALICE, "bad-address", 1_000_000L, null);
        ApprovalResult result = service.approve(tx);

        assertEquals(ApprovalStatus.REJECTED, result.getStatus());
    }

    // -------------------------------------------------------------------------
    // Rejection: self-transfer
    // -------------------------------------------------------------------------

    @Test
    void selfTransferIsRejected() {
        XrpTransaction tx = new XrpTransaction(ALICE, ALICE, 1_000_000L, null);
        ApprovalResult result = service.approve(tx);

        assertEquals(ApprovalStatus.REJECTED, result.getStatus());
    }

    // -------------------------------------------------------------------------
    // Rejection: blocked addresses
    // -------------------------------------------------------------------------

    @Test
    void transactionFromBlockedSenderIsRejected() {
        XrpLedgerService svc = new XrpLedgerService(
                XrpLedgerService.DEFAULT_MAX_SINGLE_TRANSACTION_DROPS,
                XrpLedgerService.DEFAULT_MAX_DAILY_DROPS_PER_SENDER,
                XrpLedgerService.DEFAULT_LARGE_TRANSACTION_THRESHOLD_DROPS,
                Set.of(ALICE));

        ApprovalResult result = svc.approve(new XrpTransaction(ALICE, BOB, 1_000_000L, null));
        assertEquals(ApprovalStatus.REJECTED, result.getStatus());
        assertTrue(result.getReason().contains("blocked"));
    }

    @Test
    void transactionToBlockedReceiverIsRejected() {
        XrpLedgerService svc = new XrpLedgerService(
                XrpLedgerService.DEFAULT_MAX_SINGLE_TRANSACTION_DROPS,
                XrpLedgerService.DEFAULT_MAX_DAILY_DROPS_PER_SENDER,
                XrpLedgerService.DEFAULT_LARGE_TRANSACTION_THRESHOLD_DROPS,
                Set.of(BOB));

        ApprovalResult result = svc.approve(new XrpTransaction(ALICE, BOB, 1_000_000L, null));
        assertEquals(ApprovalStatus.REJECTED, result.getStatus());
        assertTrue(result.getReason().contains("blocked"));
    }

    // -------------------------------------------------------------------------
    // Rejection: per-transaction limit
    // -------------------------------------------------------------------------

    @Test
    void transactionExceedingPerTransactionLimitIsRejected() {
        long limit = 50L * XrpTransaction.DROPS_PER_XRP;  // 50 XRP
        XrpLedgerService svc = new XrpLedgerService(
                limit,
                XrpLedgerService.DEFAULT_MAX_DAILY_DROPS_PER_SENDER,
                limit / 2,
                Set.of());

        XrpTransaction tx = new XrpTransaction(ALICE, BOB, limit + 1, null);
        assertEquals(ApprovalStatus.REJECTED, svc.approve(tx).getStatus());
    }

    // -------------------------------------------------------------------------
    // Pending: large-transaction threshold
    // -------------------------------------------------------------------------

    @Test
    void transactionAboveLargeThresholdIsPending() {
        // Use a service where the threshold is 5 XRP and the cap is 200 XRP
        long threshold = 5L * XrpTransaction.DROPS_PER_XRP;
        long cap       = 200L * XrpTransaction.DROPS_PER_XRP;
        XrpLedgerService svc = new XrpLedgerService(cap, cap * 10, threshold, Set.of());

        // 10 XRP — above threshold but below cap → PENDING
        XrpTransaction tx = new XrpTransaction(ALICE, BOB, 10L * XrpTransaction.DROPS_PER_XRP, null);
        ApprovalResult result = svc.approve(tx);

        assertEquals(ApprovalStatus.PENDING, result.getStatus());
        assertTrue(result.getReason().contains("manual compliance review"));
    }

    @Test
    void transactionAtOrBelowLargeThresholdIsApproved() {
        long threshold = 5L * XrpTransaction.DROPS_PER_XRP;
        long cap       = 200L * XrpTransaction.DROPS_PER_XRP;
        XrpLedgerService svc = new XrpLedgerService(cap, cap * 10, threshold, Set.of());

        // Exactly at threshold → APPROVED
        XrpTransaction tx = new XrpTransaction(ALICE, BOB, threshold, null);
        assertEquals(ApprovalStatus.APPROVED, svc.approve(tx).getStatus());
    }

    // -------------------------------------------------------------------------
    // Rejection: daily limit
    // -------------------------------------------------------------------------

    @Test
    void transactionExceedingDailyLimitIsRejected() {
        long dailyLimit = 10L * XrpTransaction.DROPS_PER_XRP;
        // Set large-transaction threshold equal to the per-transaction cap so nothing goes PENDING
        XrpLedgerService svc = new XrpLedgerService(
                dailyLimit, dailyLimit, dailyLimit, Set.of());

        long amount = 4L * XrpTransaction.DROPS_PER_XRP;  // 4 XRP
        svc.approve(new XrpTransaction(ALICE, BOB, amount, null));  // total = 4 XRP — APPROVED
        svc.approve(new XrpTransaction(ALICE, BOB, amount, null));  // total = 8 XRP — APPROVED

        // This would push the daily total to 12 XRP, exceeding the 10 XRP limit → REJECTED
        ApprovalResult result = svc.approve(new XrpTransaction(ALICE, BOB, amount, null));
        assertEquals(ApprovalStatus.REJECTED, result.getStatus());
        assertTrue(result.getReason().contains("daily limit"));
    }

    @Test
    void differentSendersHaveIndependentDailyLimits() {
        String charlie = "rDsbeomae4FXwgQTJp9Rs64Qg9vDiTCdBv";
        long small = 1_000_000L;  // 1 XRP

        service.approve(new XrpTransaction(ALICE,   BOB,     small, null));
        service.approve(new XrpTransaction(charlie, BOB,     small, null));

        assertEquals(small, service.getDailySentDrops(ALICE));
        assertEquals(small, service.getDailySentDrops(charlie));
    }

    // -------------------------------------------------------------------------
    // Null guard on approve()
    // -------------------------------------------------------------------------

    @Test
    void approveNullTransactionThrows() {
        assertThrows(NullPointerException.class, () -> service.approve(null));
    }

    // -------------------------------------------------------------------------
    // Constructor validation
    // -------------------------------------------------------------------------

    @Test
    void constructorRejectsNonPositiveLimits() {
        assertThrows(IllegalArgumentException.class,
                () -> new XrpLedgerService(0, 1_000_000L, 1_000_000L, Set.of()));
        assertThrows(IllegalArgumentException.class,
                () -> new XrpLedgerService(1_000_000L, 0, 1_000_000L, Set.of()));
        assertThrows(IllegalArgumentException.class,
                () -> new XrpLedgerService(1_000_000L, 1_000_000L, 0, Set.of()));
    }

    @Test
    void constructorRejectsThresholdAboveCap() {
        assertThrows(IllegalArgumentException.class,
                () -> new XrpLedgerService(1_000_000L, 10_000_000L, 2_000_000L, Set.of()));
    }

    @Test
    void constructorRejectsNullBlockedAddresses() {
        assertThrows(NullPointerException.class,
                () -> new XrpLedgerService(1_000_000L, 10_000_000L, 500_000L, null));
    }
}
