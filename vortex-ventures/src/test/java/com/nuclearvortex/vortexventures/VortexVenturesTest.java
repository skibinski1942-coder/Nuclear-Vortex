package com.nuclearvortex.vortexventures;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

class VortexVenturesTest {

    private VortexVentures vortexVentures;

    @BeforeEach
    void setUp() {
        vortexVentures = new VortexVentures();
    }

    @Test
    void implementsCompanyContract() {
        assertEquals("Vortex Ventures", vortexVentures.getName());
        assertFalse(vortexVentures.getTagline().isBlank());
        assertFalse(vortexVentures.getMission().isBlank());
        assertEquals("Financial Technology", vortexVentures.getTechnologyDomain());
    }

    @Test
    void simplicityScoreIsHigh() {
        int score = vortexVentures.getSimplicityScore();
        assertTrue(score >= 8 && score <= 10, "expected score 8-10, got " + score);
    }

    @Test
    void projectWealthBasicCompounding() {
        // $10,000 at 7% for 10 years → ~$19,671.51
        BigDecimal result = vortexVentures.projectWealth(
                BigDecimal.valueOf(10_000), 0.07, 10);
        assertEquals(0, result.compareTo(new BigDecimal("19671.51")));
    }

    @Test
    void projectWealthZeroRate() {
        // No growth: principal is returned unchanged
        BigDecimal result = vortexVentures.projectWealth(
                BigDecimal.valueOf(5_000), 0.0, 5);
        assertEquals(0, result.compareTo(new BigDecimal("5000.00")));
    }

    @Test
    void projectWealthNullPrincipalThrows() {
        assertThrows(NullPointerException.class,
                () -> vortexVentures.projectWealth(null, 0.05, 5));
    }

    @Test
    void projectWealthNegativePrincipalThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> vortexVentures.projectWealth(BigDecimal.valueOf(-1), 0.05, 5));
    }

    @Test
    void projectWealthNegativeRateThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> vortexVentures.projectWealth(BigDecimal.valueOf(1000), -0.1, 5));
    }

    @Test
    void projectWealthZeroYearsThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> vortexVentures.projectWealth(BigDecimal.valueOf(1000), 0.05, 0));
    }

    @Test
    void calculateRoiPositiveReturn() {
        // Bought for $1,000, sold for $1,500 → 50% ROI
        BigDecimal roi = vortexVentures.calculateRoi(
                BigDecimal.valueOf(1_000), BigDecimal.valueOf(1_500));
        assertEquals(0, roi.compareTo(new BigDecimal("50.00")));
    }

    @Test
    void calculateRoiTotalLoss() {
        // Lost everything → -100% ROI
        BigDecimal roi = vortexVentures.calculateRoi(
                BigDecimal.valueOf(1_000), BigDecimal.ZERO);
        assertEquals(0, roi.compareTo(new BigDecimal("-100.00")));
    }

    @Test
    void calculateRoiNullThrows() {
        assertThrows(NullPointerException.class,
                () -> vortexVentures.calculateRoi(null, BigDecimal.valueOf(100)));
        assertThrows(NullPointerException.class,
                () -> vortexVentures.calculateRoi(BigDecimal.valueOf(100), null));
    }

    @Test
    void calculateRoiNonPositiveInitialThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> vortexVentures.calculateRoi(BigDecimal.ZERO, BigDecimal.valueOf(100)));
    }
}
