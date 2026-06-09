package com.nuclearvortex.vortexventures;

import com.nuclearvortex.core.Company;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

/**
 * Vortex Ventures — financial technology and wealth operations.
 *
 * <p>Vortex Ventures builds the financial infrastructure that powers the
 * Nuclear-Vortex conglomerate and its customers. Its platform provides
 * simple, jargon-free access to investing, compound-growth modeling, and
 * revenue attribution across all sub-companies.</p>
 *
 * <p>Revenue model: percentage-of-assets-under-management (AUM) plus
 * transaction fees on the Vortex Pay network.</p>
 */
public final class VortexVentures implements Company {

    private static final String NAME = "Vortex Ventures";
    private static final String TAGLINE = "Your money, amplified.";
    private static final String MISSION =
            "Democratize wealth creation by making sophisticated financial tools "
            + "as easy to use as a pocket calculator — for individuals, small "
            + "businesses, and enterprises alike.";
    private static final String DOMAIN = "Financial Technology";
    private static final int SIMPLICITY_SCORE = 9;

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public String getTagline() {
        return TAGLINE;
    }

    @Override
    public String getMission() {
        return MISSION;
    }

    @Override
    public String getTechnologyDomain() {
        return DOMAIN;
    }

    @Override
    public int getSimplicityScore() {
        return SIMPLICITY_SCORE;
    }

    /**
     * Projects the future value of an investment using compound interest.
     *
     * <p>Formula: {@code FV = principal * (1 + rate) ^ years}</p>
     *
     * @param principal  the initial investment amount; must be positive
     * @param annualRate the annual interest/growth rate as a decimal
     *                   (e.g. {@code 0.07} for 7%); must be non-negative
     * @param years      the number of compounding periods in years; must be
     *                   positive
     * @return the projected future value, rounded to 2 decimal places
     * @throws IllegalArgumentException if any argument is out of range
     */
    public BigDecimal projectWealth(BigDecimal principal, double annualRate, int years) {
        Objects.requireNonNull(principal, "principal must not be null");
        if (principal.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("principal must be positive");
        }
        if (annualRate < 0) {
            throw new IllegalArgumentException("annualRate must be non-negative");
        }
        if (years <= 0) {
            throw new IllegalArgumentException("years must be positive");
        }

        double futureValue = principal.doubleValue() * Math.pow(1 + annualRate, years);
        return BigDecimal.valueOf(futureValue).setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Calculates the return on investment (ROI) as a percentage.
     *
     * @param initialInvestment the amount invested; must be positive
     * @param finalValue        the value at exit; must be non-negative
     * @return ROI percentage, rounded to 2 decimal places
     * @throws IllegalArgumentException if initialInvestment is not positive
     */
    public BigDecimal calculateRoi(BigDecimal initialInvestment, BigDecimal finalValue) {
        Objects.requireNonNull(initialInvestment, "initialInvestment must not be null");
        Objects.requireNonNull(finalValue, "finalValue must not be null");
        if (initialInvestment.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("initialInvestment must be positive");
        }
        if (finalValue.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("finalValue must be non-negative");
        }

        BigDecimal gain = finalValue.subtract(initialInvestment);
        BigDecimal roi = gain.divide(initialInvestment, 10, RoundingMode.HALF_UP)
                             .multiply(BigDecimal.valueOf(100));
        return roi.setScale(2, RoundingMode.HALF_UP);
    }
}
