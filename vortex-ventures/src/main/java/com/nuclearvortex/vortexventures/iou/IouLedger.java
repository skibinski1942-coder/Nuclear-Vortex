package com.nuclearvortex.vortexventures.iou;

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
 * Central ledger for managing I.O.U. records within the Vortex Ventures platform.
 *
 * <p>The {@code IouLedger} is the single entry point for all I.O.U. operations:
 * recording new debts, settling them, and querying balances between parties.
 * All monetary amounts are handled as {@link BigDecimal} to guarantee precision.</p>
 *
 * <h2>Usage example</h2>
 * <pre>{@code
 * IouLedger ledger = new IouLedger();
 *
 * UUID id = ledger.add("Alice", "Bob", new BigDecimal("50.00"), "Dinner last Friday");
 * System.out.println(ledger.netBalance("Alice", "Bob")); // -50.00 (Alice owes Bob)
 *
 * ledger.settle(id);
 * System.out.println(ledger.netBalance("Alice", "Bob")); // 0.00
 * }</pre>
 *
 * <p>This class is <em>not</em> thread-safe.  External synchronization is required
 * when multiple threads share a single {@code IouLedger} instance.</p>
 */
public final class IouLedger {

    private final Map<UUID, Iou> records = new LinkedHashMap<>();

    /**
     * Records a new pending I.O.U.
     *
     * @param debtor      name of the person who owes money; must not be blank
     * @param creditor    name of the person who is owed money; must not be blank
     * @param amount      the amount owed; must be positive
     * @param description a short note about the debt (e.g. "dinner", "bus fare")
     * @return the unique {@link UUID} assigned to this I.O.U.
     * @throws NullPointerException     if any argument is {@code null}
     * @throws IllegalArgumentException if {@code debtor} or {@code creditor} is blank,
     *                                  if they are the same person,
     *                                  or if {@code amount} is not positive
     */
    public UUID add(String debtor, String creditor, BigDecimal amount, String description) {
        Iou iou = new Iou(UUID.randomUUID(), debtor, creditor, amount, description,
                LocalDate.now());
        records.put(iou.getId(), iou);
        return iou.getId();
    }

    /**
     * Marks an existing pending I.O.U. as settled.
     *
     * @param id the unique identifier of the I.O.U. to settle; must not be {@code null}
     * @throws NullPointerException     if {@code id} is {@code null}
     * @throws NoSuchElementException   if no I.O.U. with the given {@code id} exists
     * @throws IllegalStateException    if the I.O.U. is already settled
     */
    public void settle(UUID id) {
        Objects.requireNonNull(id, "id must not be null");
        Iou iou = records.get(id);
        if (iou == null) {
            throw new NoSuchElementException("No I.O.U. found with id: " + id);
        }
        if (!iou.isPending()) {
            throw new IllegalStateException("I.O.U. " + id + " is already settled");
        }
        iou.markSettled();
    }

    /**
     * Retrieves an I.O.U. by its unique identifier.
     *
     * @param id the UUID of the I.O.U.; must not be {@code null}
     * @return the matching {@link Iou}
     * @throws NullPointerException   if {@code id} is {@code null}
     * @throws NoSuchElementException if no I.O.U. with the given {@code id} exists
     */
    public Iou get(UUID id) {
        Objects.requireNonNull(id, "id must not be null");
        Iou iou = records.get(id);
        if (iou == null) {
            throw new NoSuchElementException("No I.O.U. found with id: " + id);
        }
        return iou;
    }

    /**
     * Returns an unmodifiable list of all I.O.U.s in insertion order.
     *
     * @return all records (pending and settled), never {@code null}
     */
    public List<Iou> listAll() {
        return Collections.unmodifiableList(List.copyOf(records.values()));
    }

    /**
     * Returns an unmodifiable list of all {@link IouStatus#PENDING} I.O.U.s.
     *
     * @return pending records in insertion order, never {@code null}
     */
    public List<Iou> listPending() {
        return records.values().stream()
                .filter(Iou::isPending)
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Returns an unmodifiable list of all I.O.U.s where the given person is
     * either the debtor or the creditor.
     *
     * @param person the name to filter by; must not be blank
     * @return matching records in insertion order, never {@code null}
     * @throws NullPointerException     if {@code person} is {@code null}
     * @throws IllegalArgumentException if {@code person} is blank
     */
    public List<Iou> listByPerson(String person) {
        Objects.requireNonNull(person, "person must not be null");
        if (person.isBlank()) {
            throw new IllegalArgumentException("person must not be blank");
        }
        return records.values().stream()
                .filter(iou -> iou.getDebtor().equalsIgnoreCase(person)
                        || iou.getCreditor().equalsIgnoreCase(person))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * Calculates the net balance between two parties across all <em>pending</em>
     * I.O.U.s.
     *
     * <p>A negative result means {@code personA} still owes {@code personB} that
     * amount.  A positive result means {@code personB} owes {@code personA}.
     * Zero means the two parties are square.</p>
     *
     * <p>Only {@link IouStatus#PENDING} records are included in the calculation;
     * settled debts are excluded.</p>
     *
     * @param personA name of the first party; must not be blank
     * @param personB name of the second party; must not be blank
     * @return net amount owed, rounded to 2 decimal places;
     *         negative ↔ {@code personA} owes {@code personB},
     *         positive ↔ {@code personB} owes {@code personA}
     * @throws NullPointerException     if either argument is {@code null}
     * @throws IllegalArgumentException if either name is blank or they are equal
     */
    public BigDecimal netBalance(String personA, String personB) {
        Objects.requireNonNull(personA, "personA must not be null");
        Objects.requireNonNull(personB, "personB must not be null");
        if (personA.isBlank()) {
            throw new IllegalArgumentException("personA must not be blank");
        }
        if (personB.isBlank()) {
            throw new IllegalArgumentException("personB must not be blank");
        }
        if (personA.equalsIgnoreCase(personB)) {
            throw new IllegalArgumentException("personA and personB must be different");
        }

        BigDecimal balance = BigDecimal.ZERO;
        for (Iou iou : records.values()) {
            if (!iou.isPending()) {
                continue;
            }
            if (iou.getDebtor().equalsIgnoreCase(personA)
                    && iou.getCreditor().equalsIgnoreCase(personB)) {
                // personA owes personB → negative for personA
                balance = balance.subtract(iou.getAmount());
            } else if (iou.getDebtor().equalsIgnoreCase(personB)
                    && iou.getCreditor().equalsIgnoreCase(personA)) {
                // personB owes personA → positive for personA
                balance = balance.add(iou.getAmount());
            }
        }
        return balance.setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the total outstanding amount owed <em>to</em> the given person
     * across all pending I.O.U.s where they are the creditor.
     *
     * @param creditor the creditor's name; must not be blank
     * @return total pending amount owed to {@code creditor}, rounded to 2 decimal places
     * @throws NullPointerException     if {@code creditor} is {@code null}
     * @throws IllegalArgumentException if {@code creditor} is blank
     */
    public BigDecimal totalOwedTo(String creditor) {
        Objects.requireNonNull(creditor, "creditor must not be null");
        if (creditor.isBlank()) {
            throw new IllegalArgumentException("creditor must not be blank");
        }
        return records.values().stream()
                .filter(Iou::isPending)
                .filter(iou -> iou.getCreditor().equalsIgnoreCase(creditor))
                .map(Iou::getAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the total outstanding amount <em>owed by</em> the given person
     * across all pending I.O.U.s where they are the debtor.
     *
     * @param debtor the debtor's name; must not be blank
     * @return total pending amount owed by {@code debtor}, rounded to 2 decimal places
     * @throws NullPointerException     if {@code debtor} is {@code null}
     * @throws IllegalArgumentException if {@code debtor} is blank
     */
    public BigDecimal totalOwedBy(String debtor) {
        Objects.requireNonNull(debtor, "debtor must not be null");
        if (debtor.isBlank()) {
            throw new IllegalArgumentException("debtor must not be blank");
        }
        return records.values().stream()
                .filter(Iou::isPending)
                .filter(iou -> iou.getDebtor().equalsIgnoreCase(debtor))
                .map(Iou::getAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Returns the number of I.O.U.s currently held in this ledger
     * (both pending and settled).
     *
     * @return total record count
     */
    public int size() {
        return records.size();
    }
}
