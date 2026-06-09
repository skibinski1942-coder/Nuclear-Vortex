package com.nuclearvortex.claritytech;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ClarityTechTest {

    private ClarityTech clarityTech;

    @BeforeEach
    void setUp() {
        clarityTech = new ClarityTech();
    }

    @Test
    void implementsCompanyContract() {
        assertEquals("ClarityTech", clarityTech.getName());
        assertFalse(clarityTech.getTagline().isBlank());
        assertFalse(clarityTech.getMission().isBlank());
        assertFalse(clarityTech.getTechnologyDomain().isBlank());
    }

    @Test
    void simplicityScoreIsMaximum() {
        assertEquals(10, clarityTech.getSimplicityScore());
    }

    @Test
    void simplifyTrimsAndSentenceCases() {
        assertEquals("Hello world", clarityTech.simplify("  HELLO WORLD  "));
    }

    @Test
    void simplifyPreservesFirstCharUppercase() {
        assertEquals("Simple", clarityTech.simplify("SIMPLE"));
    }

    @Test
    void simplifyNullThrows() {
        assertThrows(IllegalArgumentException.class, () -> clarityTech.simplify(null));
    }

    @Test
    void simplifyBlankThrows() {
        assertThrows(IllegalArgumentException.class, () -> clarityTech.simplify("   "));
    }

    @Test
    void simplifySingleCharacter() {
        assertEquals("A", clarityTech.simplify("a"));
    }
}
