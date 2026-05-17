package com.nuclearvortex.vortexventures.iou;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class IouLedgerTest {

    private IouLedger ledger;

    @BeforeEach
    void setUp() {
        ledger = new IouLedger();
    }

    // -----------------------------------------------------------------------
    // add()
    // -----------------------------------------------------------------------

    @Test
    void addReturnsUniqueIds() {
        UUID id1 = ledger.add("Alice", "Bob", new BigDecimal("10.00"), "coffee");
        UUID id2 = ledger.add("Alice", "Bob", new BigDecimal("20.00"), "lunch");
        assertNotEquals(id1, id2);
        assertEquals(2, ledger.size());
    }

    @Test
    void addedIouIsInitiallyPending() {
        UUID id = ledger.add("Alice", "Bob", new BigDecimal("15.00"), "taxi");
        Iou iou = ledger.get(id);
        assertEquals(IouStatus.PENDING, iou.getStatus());
        assertTrue(iou.isPending());
    }

    @Test
    void addStoresAllFields() {
        UUID id = ledger.add("Charlie", "Dana", new BigDecimal("99.99"), "rent share");
        Iou iou = ledger.get(id);
        assertEquals("Charlie", iou.getDebtor());
        assertEquals("Dana", iou.getCreditor());
        assertEquals(0, iou.getAmount().compareTo(new BigDecimal("99.99")));
        assertEquals("rent share", iou.getDescription());
        assertNotNull(iou.getDateCreated());
    }

    @Test
    void addNullDebtorThrows() {
        assertThrows(NullPointerException.class,
                () -> ledger.add(null, "Bob", new BigDecimal("10.00"), "note"));
    }

    @Test
    void addBlankDebtorThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> ledger.add("  ", "Bob", new BigDecimal("10.00"), "note"));
    }

    @Test
    void addNullCreditorThrows() {
        assertThrows(NullPointerException.class,
                () -> ledger.add("Alice", null, new BigDecimal("10.00"), "note"));
    }

    @Test
    void addBlankCreditorThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> ledger.add("Alice", "", new BigDecimal("10.00"), "note"));
    }

    @Test
    void addSamePersonThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> ledger.add("Alice", "alice", new BigDecimal("10.00"), "self loan"));
    }

    @Test
    void addZeroAmountThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> ledger.add("Alice", "Bob", BigDecimal.ZERO, "nothing"));
    }

    @Test
    void addNegativeAmountThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> ledger.add("Alice", "Bob", new BigDecimal("-5.00"), "negative"));
    }

    @Test
    void addNullAmountThrows() {
        assertThrows(NullPointerException.class,
                () -> ledger.add("Alice", "Bob", null, "note"));
    }

    // -----------------------------------------------------------------------
    // settle()
    // -----------------------------------------------------------------------

    @Test
    void settleChangesStatusToSettled() {
        UUID id = ledger.add("Alice", "Bob", new BigDecimal("30.00"), "dinner");
        ledger.settle(id);
        assertEquals(IouStatus.SETTLED, ledger.get(id).getStatus());
        assertFalse(ledger.get(id).isPending());
    }

    @Test
    void settleAlreadySettledThrows() {
        UUID id = ledger.add("Alice", "Bob", new BigDecimal("10.00"), "coffee");
        ledger.settle(id);
        assertThrows(IllegalStateException.class, () -> ledger.settle(id));
    }

    @Test
    void settleUnknownIdThrows() {
        assertThrows(NoSuchElementException.class, () -> ledger.settle(UUID.randomUUID()));
    }

    @Test
    void settleNullIdThrows() {
        assertThrows(NullPointerException.class, () -> ledger.settle(null));
    }

    // -----------------------------------------------------------------------
    // get()
    // -----------------------------------------------------------------------

    @Test
    void getUnknownIdThrows() {
        assertThrows(NoSuchElementException.class, () -> ledger.get(UUID.randomUUID()));
    }

    @Test
    void getNullIdThrows() {
        assertThrows(NullPointerException.class, () -> ledger.get(null));
    }

    // -----------------------------------------------------------------------
    // listAll() / listPending()
    // -----------------------------------------------------------------------

    @Test
    void listAllReturnsAllRecords() {
        ledger.add("Alice", "Bob", new BigDecimal("10.00"), "a");
        ledger.add("Bob", "Carol", new BigDecimal("20.00"), "b");
        assertEquals(2, ledger.listAll().size());
    }

    @Test
    void listAllIsUnmodifiable() {
        ledger.add("Alice", "Bob", new BigDecimal("10.00"), "a");
        List<Iou> all = ledger.listAll();
        assertThrows(UnsupportedOperationException.class, () -> all.remove(0));
    }

    @Test
    void listPendingExcludesSettled() {
        UUID id1 = ledger.add("Alice", "Bob", new BigDecimal("10.00"), "a");
        UUID id2 = ledger.add("Alice", "Bob", new BigDecimal("20.00"), "b");
        ledger.settle(id1);

        List<Iou> pending = ledger.listPending();
        assertEquals(1, pending.size());
        assertEquals(id2, pending.get(0).getId());
    }

    @Test
    void listAllEmptyLedger() {
        assertTrue(ledger.listAll().isEmpty());
    }

    // -----------------------------------------------------------------------
    // listByPerson()
    // -----------------------------------------------------------------------

    @Test
    void listByPersonReturnsBothRoles() {
        ledger.add("Alice", "Bob", new BigDecimal("10.00"), "as debtor");
        ledger.add("Carol", "Alice", new BigDecimal("5.00"), "as creditor");
        ledger.add("Bob", "Carol", new BigDecimal("7.00"), "unrelated");

        List<Iou> aliceRecords = ledger.listByPerson("Alice");
        assertEquals(2, aliceRecords.size());
    }

    @Test
    void listByPersonCaseInsensitive() {
        ledger.add("alice", "Bob", new BigDecimal("10.00"), "note");
        assertEquals(1, ledger.listByPerson("ALICE").size());
    }

    @Test
    void listByPersonBlankThrows() {
        assertThrows(IllegalArgumentException.class, () -> ledger.listByPerson(" "));
    }

    @Test
    void listByPersonNullThrows() {
        assertThrows(NullPointerException.class, () -> ledger.listByPerson(null));
    }

    // -----------------------------------------------------------------------
    // netBalance()
    // -----------------------------------------------------------------------

    @Test
    void netBalanceWhenPersonAOwesPersonB() {
        // Alice owes Bob $50 → balance from Alice's perspective is −50
        ledger.add("Alice", "Bob", new BigDecimal("50.00"), "dinner");
        BigDecimal balance = ledger.netBalance("Alice", "Bob");
        assertEquals(0, balance.compareTo(new BigDecimal("-50.00")));
    }

    @Test
    void netBalanceWhenPersonBOwesPersonA() {
        // Bob owes Alice $30 → from Alice's perspective balance is +30
        ledger.add("Bob", "Alice", new BigDecimal("30.00"), "concert ticket");
        BigDecimal balance = ledger.netBalance("Alice", "Bob");
        assertEquals(0, balance.compareTo(new BigDecimal("30.00")));
    }

    @Test
    void netBalanceSquaredAfterSettle() {
        UUID id = ledger.add("Alice", "Bob", new BigDecimal("50.00"), "dinner");
        ledger.settle(id);
        BigDecimal balance = ledger.netBalance("Alice", "Bob");
        assertEquals(0, balance.compareTo(new BigDecimal("0.00")));
    }

    @Test
    void netBalanceMultipleDebtsNetted() {
        // Alice owes Bob $100, Bob owes Alice $40 → net: Alice owes Bob $60
        ledger.add("Alice", "Bob", new BigDecimal("100.00"), "holiday costs");
        ledger.add("Bob", "Alice", new BigDecimal("40.00"), "groceries");
        BigDecimal balance = ledger.netBalance("Alice", "Bob");
        assertEquals(0, balance.compareTo(new BigDecimal("-60.00")));
    }

    @Test
    void netBalanceEmptyLedger() {
        assertEquals(0,
                ledger.netBalance("Alice", "Bob").compareTo(new BigDecimal("0.00")));
    }

    @Test
    void netBalanceSamePersonThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> ledger.netBalance("Alice", "Alice"));
    }

    @Test
    void netBalanceNullPersonThrows() {
        assertThrows(NullPointerException.class,
                () -> ledger.netBalance(null, "Bob"));
        assertThrows(NullPointerException.class,
                () -> ledger.netBalance("Alice", null));
    }

    // -----------------------------------------------------------------------
    // totalOwedTo() / totalOwedBy()
    // -----------------------------------------------------------------------

    @Test
    void totalOwedToSumsAllPendingCredits() {
        ledger.add("Alice", "Bob", new BigDecimal("20.00"), "a");
        ledger.add("Carol", "Bob", new BigDecimal("30.00"), "b");
        ledger.add("Dana", "Bob", new BigDecimal("10.00"), "c");
        assertEquals(0,
                ledger.totalOwedTo("Bob").compareTo(new BigDecimal("60.00")));
    }

    @Test
    void totalOwedToExcludesSettled() {
        UUID id = ledger.add("Alice", "Bob", new BigDecimal("20.00"), "a");
        ledger.add("Carol", "Bob", new BigDecimal("30.00"), "b");
        ledger.settle(id);
        assertEquals(0,
                ledger.totalOwedTo("Bob").compareTo(new BigDecimal("30.00")));
    }

    @Test
    void totalOwedByReflectsDebtor() {
        ledger.add("Alice", "Bob", new BigDecimal("15.00"), "a");
        ledger.add("Alice", "Carol", new BigDecimal("25.00"), "b");
        assertEquals(0,
                ledger.totalOwedBy("Alice").compareTo(new BigDecimal("40.00")));
    }

    @Test
    void totalOwedToBlankThrows() {
        assertThrows(IllegalArgumentException.class, () -> ledger.totalOwedTo("  "));
    }

    @Test
    void totalOwedByNullThrows() {
        assertThrows(NullPointerException.class, () -> ledger.totalOwedBy(null));
    }

    // -----------------------------------------------------------------------
    // Iou.toString()
    // -----------------------------------------------------------------------

    @Test
    void iouToStringContainsKeyFields() {
        UUID id = ledger.add("Alice", "Bob", new BigDecimal("10.00"), "coffee");
        String str = ledger.get(id).toString();
        assertTrue(str.contains("Alice"));
        assertTrue(str.contains("Bob"));
        assertTrue(str.contains("10.00"));
        assertTrue(str.contains("PENDING"));
    }
}
