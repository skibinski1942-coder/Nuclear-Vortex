package com.nuclearvortex.core;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class NuclearVortexTest {

    private static Company makeCompany(String name, String tagline, String mission,
                                       String domain, int score) {
        return new Company() {
            public String getName() { return name; }
            public String getTagline() { return tagline; }
            public String getMission() { return mission; }
            public String getTechnologyDomain() { return domain; }
            public int getSimplicityScore() { return score; }
        };
    }

    @Test
    void holdsNameAndTagline() {
        NuclearVortex nv = new NuclearVortex(List.of());
        assertEquals("Nuclear-Vortex", nv.getName());
        assertFalse(nv.getTagline().isBlank());
        assertFalse(nv.getVision().isBlank());
    }

    @Test
    void portfolioIsUnmodifiable() {
        NuclearVortex nv = new NuclearVortex(List.of());
        assertThrows(UnsupportedOperationException.class,
                () -> nv.getPortfolio().add(makeCompany("X", "t", "m", "d", 5)));
    }

    @Test
    void averageSimplicityScoreEmptyPortfolio() {
        NuclearVortex nv = new NuclearVortex(List.of());
        assertEquals(0.0, nv.averageSimplicityScore());
    }

    @Test
    void averageSimplicityScoreWithCompanies() {
        Company a = makeCompany("A", "t", "m", "d", 8);
        Company b = makeCompany("B", "t", "m", "d", 6);
        NuclearVortex nv = new NuclearVortex(List.of(a, b));
        assertEquals(7.0, nv.averageSimplicityScore(), 0.001);
    }

    @Test
    void portfolioNullThrows() {
        assertThrows(NullPointerException.class, () -> new NuclearVortex(null));
    }

    @Test
    void printOverviewDoesNotThrow() {
        Company c = makeCompany("TestCo", "tagline", "mission", "SaaS", 9);
        NuclearVortex nv = new NuclearVortex(List.of(c));
        assertDoesNotThrow(nv::printOverview);
    }
}
