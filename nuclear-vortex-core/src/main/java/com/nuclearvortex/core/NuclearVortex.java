package com.nuclearvortex.core;

import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * The Nuclear-Vortex holding company.
 *
 * <p>Nuclear-Vortex is a human-centered technology conglomerate whose mission
 * is to deliver extraordinary simplicity and clarity through its portfolio of
 * sub-companies. Wealth is created by genuinely solving hard human problems
 * with elegant, accessible technology.</p>
 */
public final class NuclearVortex {

    private static final String NAME = "Nuclear-Vortex";
    private static final String TAGLINE = "A brand that leads in the world of confused with clarity.";
    private static final String VISION =
            "To be the world's most human-centered technology conglomerate — "
            + "growing extraordinary wealth by delivering extraordinary simplicity.";

    private final List<Company> portfolio;

    /**
     * Creates a new Nuclear-Vortex holding company with the given sub-company
     * portfolio.
     *
     * @param portfolio the list of sub-companies; must not be null
     */
    public NuclearVortex(List<Company> portfolio) {
        this.portfolio = Collections.unmodifiableList(
                Objects.requireNonNull(portfolio, "portfolio must not be null"));
    }

    /** Returns the holding company's name. */
    public String getName() {
        return NAME;
    }

    /** Returns the holding company's tagline. */
    public String getTagline() {
        return TAGLINE;
    }

    /** Returns the holding company's long-term vision. */
    public String getVision() {
        return VISION;
    }

    /**
     * Returns an unmodifiable view of all sub-companies in the portfolio.
     *
     * @return sub-company portfolio
     */
    public List<Company> getPortfolio() {
        return portfolio;
    }

    /**
     * Computes the portfolio-wide average simplicity score across all
     * sub-companies.
     *
     * <p>A higher average score signals that the conglomerate is living up to
     * its core principle of human-centered simplicity.</p>
     *
     * @return average simplicity score, or 0.0 if the portfolio is empty
     */
    public double averageSimplicityScore() {
        return portfolio.stream()
                .mapToInt(Company::getSimplicityScore)
                .average()
                .orElse(0.0);
    }

    /**
     * Prints a human-readable overview of Nuclear-Vortex and its portfolio to
     * standard output.
     */
    public void printOverview() {
        System.out.println("=== " + NAME + " ===");
        System.out.println(TAGLINE);
        System.out.println();
        System.out.println("Vision: " + VISION);
        System.out.println();
        System.out.println("Portfolio (" + portfolio.size() + " companies):");
        for (Company company : portfolio) {
            System.out.printf("  • %-20s | %s%n", company.getName(), company.getTagline());
            System.out.printf("    Domain: %-16s | Simplicity: %d/10%n",
                    company.getTechnologyDomain(), company.getSimplicityScore());
        }
        System.out.printf("%nPortfolio avg. simplicity score: %.1f / 10%n",
                averageSimplicityScore());
    }
}
