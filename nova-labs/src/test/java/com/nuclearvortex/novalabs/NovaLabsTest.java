package com.nuclearvortex.novalabs;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class NovaLabsTest {

    private NovaLabs novaLabs;

    @BeforeEach
    void setUp() {
        novaLabs = new NovaLabs();
    }

    @Test
    void implementsCompanyContract() {
        assertEquals("Nova Labs", novaLabs.getName());
        assertFalse(novaLabs.getTagline().isBlank());
        assertFalse(novaLabs.getMission().isBlank());
        assertEquals("Research & Development", novaLabs.getTechnologyDomain());
    }

    @Test
    void simplicityScoreInValidRange() {
        int score = novaLabs.getSimplicityScore();
        assertTrue(score >= 1 && score <= 10, "score must be 1-10, got " + score);
    }

    @Test
    void clarityIndexAllShortWords() {
        // "The cat sat" — all words ≤ 6 chars → 100
        assertEquals(100, novaLabs.clarityIndex("The cat sat"));
    }

    @Test
    void clarityIndexAllLongWords() {
        // "Sophisticated architecture framework" — all > 6 chars → 0
        assertEquals(0, novaLabs.clarityIndex("Sophisticated architecture framework"));
    }

    @Test
    void clarityIndexMixed() {
        // "Big complicated thing" — "Big" and "thing" are ≤6 chars, "complicated" is not → 2/3 ≈ 67
        int score = novaLabs.clarityIndex("Big complicated thing");
        assertEquals(67, score);
    }

    @Test
    void clarityIndexNullThrows() {
        assertThrows(IllegalArgumentException.class, () -> novaLabs.clarityIndex(null));
    }

    @Test
    void clarityIndexBlankThrows() {
        assertThrows(IllegalArgumentException.class, () -> novaLabs.clarityIndex("  "));
    }

    @Test
    void generateInnovationBriefContainsRequiredSections() {
        String brief = novaLabs.generateInnovationBrief("Users cannot find the settings menu");
        assertTrue(brief.contains("Problem"));
        assertTrue(brief.contains("Hypothesis"));
        assertTrue(brief.contains("Metric"));
        assertTrue(brief.contains("Users cannot find the settings menu"));
    }

    @Test
    void generateInnovationBriefNullThrows() {
        assertThrows(NullPointerException.class,
                () -> novaLabs.generateInnovationBrief(null));
    }

    @Test
    void generateInnovationBriefBlankThrows() {
        assertThrows(IllegalArgumentException.class,
                () -> novaLabs.generateInnovationBrief("   "));
    }
}
