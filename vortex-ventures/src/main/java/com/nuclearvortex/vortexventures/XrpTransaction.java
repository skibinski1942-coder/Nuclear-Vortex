package com.nuclearvortex.vortexventures;

import java.util.Objects;

/**
 * Represents an XRP payment transaction on the XRP Ledger.
 *
 * <p>All monetary amounts are expressed in <em>drops</em> — the smallest
 * indivisible unit of XRP (1 XRP = 1,000,000 drops). Keeping amounts as
 * {@code long} drops avoids floating-point rounding errors and matches the
 * native representation used by the XRP Ledger protocol.</p>
 *
 * <p>XRP account addresses follow the rippled Base58Check encoding scheme:
 * they always begin with the character {@code 'r'} and are between 25 and
 * 34 characters long.</p>
 */
public final class XrpTransaction {

    /** Conversion factor: 1 XRP = 1,000,000 drops. */
    public static final long DROPS_PER_XRP = 1_000_000L;

    private final String senderAddress;
    private final String receiverAddress;
    /** Amount in drops. */
    private final long amountDrops;
    private final String memo;

    /**
     * Constructs an XRP payment transaction.
     *
     * @param senderAddress   the XRP Ledger address of the sender; must not be null
     * @param receiverAddress the XRP Ledger address of the receiver; must not be null
     * @param amountDrops     the payment amount in drops; must be positive
     * @param memo            an optional human-readable note; may be null or blank
     * @throws NullPointerException     if senderAddress or receiverAddress is null
     * @throws IllegalArgumentException if amountDrops is not positive
     */
    public XrpTransaction(String senderAddress,
                          String receiverAddress,
                          long amountDrops,
                          String memo) {
        this.senderAddress   = Objects.requireNonNull(senderAddress,   "senderAddress must not be null");
        this.receiverAddress = Objects.requireNonNull(receiverAddress, "receiverAddress must not be null");
        if (amountDrops <= 0) {
            throw new IllegalArgumentException("amountDrops must be positive");
        }
        this.amountDrops = amountDrops;
        this.memo        = memo;
    }

    /** Returns the sender's XRP Ledger address. */
    public String getSenderAddress() {
        return senderAddress;
    }

    /** Returns the receiver's XRP Ledger address. */
    public String getReceiverAddress() {
        return receiverAddress;
    }

    /** Returns the payment amount in drops (1 XRP = 1,000,000 drops). */
    public long getAmountDrops() {
        return amountDrops;
    }

    /** Returns the payment amount in whole XRP (drops / 1,000,000). */
    public double getAmountXrp() {
        return (double) amountDrops / DROPS_PER_XRP;
    }

    /** Returns the optional memo attached to this transaction, or {@code null}. */
    public String getMemo() {
        return memo;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof XrpTransaction)) return false;
        XrpTransaction that = (XrpTransaction) o;
        return amountDrops == that.amountDrops
                && Objects.equals(senderAddress, that.senderAddress)
                && Objects.equals(receiverAddress, that.receiverAddress)
                && Objects.equals(memo, that.memo);
    }

    @Override
    public int hashCode() {
        return Objects.hash(senderAddress, receiverAddress, amountDrops, memo);
    }

    @Override
    public String toString() {
        return "XrpTransaction{"
                + "sender='" + senderAddress + '\''
                + ", receiver='" + receiverAddress + '\''
                + ", amountDrops=" + amountDrops
                + ", memo='" + memo + '\''
                + '}';
    }
}
