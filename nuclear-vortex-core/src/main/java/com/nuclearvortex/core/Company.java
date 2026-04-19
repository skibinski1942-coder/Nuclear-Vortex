package com.nuclearvortex.core;

/**
 * Represents a company within the Nuclear-Vortex family.
 *
 * <p>Every sub-company in the Nuclear-Vortex conglomerate implements this
 * interface, ensuring a consistent model for describing what each entity
 * does, what problem it solves, and how it creates value.</p>
 */
public interface Company {

    /**
     * Returns the official name of this company.
     *
     * @return company name
     */
    String getName();

    /**
     * Returns a short tagline that captures the company's essence in one sentence.
     *
     * @return tagline
     */
    String getTagline();

    /**
     * Returns a human-readable description of the core problem this company solves.
     *
     * @return mission statement
     */
    String getMission();

    /**
     * Returns the primary technology domain this company operates in.
     *
     * @return technology domain
     */
    String getTechnologyDomain();

    /**
     * Returns the simplicity score of this company's flagship product on a
     * scale from 1 (complex) to 10 (extremely simple/accessible).
     *
     * <p>Nuclear-Vortex measures all its products against human simplicity as
     * a core KPI.</p>
     *
     * @return simplicity score between 1 and 10 (inclusive)
     */
    int getSimplicityScore();
}
