package com.nuclearvortex.claritytech;

import com.nuclearvortex.core.Company;

/**
 * ClarityTech — the human-centered UI/UX and operating platform.
 *
 * <p>ClarityTech's mission is to make every interaction with technology feel
 * natural and effortless. Its flagship product is the <em>Clarity OS</em>: an
 * adaptive, voice-first operating layer that sits on top of any device and
 * strips away cognitive overload — one UI pattern at a time.</p>
 *
 * <p>Revenue model: SaaS licensing to enterprise, government, and education
 * sectors worldwide.</p>
 */
public final class ClarityTech implements Company {

    private static final String NAME = "ClarityTech";
    private static final String TAGLINE = "See clearly. Think simply.";
    private static final String MISSION =
            "Eliminate cognitive overload by designing technology interfaces so "
            + "intuitive that anyone — regardless of age, background, or ability — "
            + "can use them without instruction.";
    private static final String DOMAIN = "Human-Computer Interaction";
    private static final int SIMPLICITY_SCORE = 10;

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
     * Applies the Clarity OS simplification algorithm to raw user input.
     *
     * <p>In the real product this method would invoke a machine-learning model
     * that rewrites cluttered UI text into plain language. This implementation
     * provides a rules-based approximation that trims whitespace and converts
     * content to sentence case.</p>
     *
     * @param rawInput the raw text or label provided by a downstream system
     * @return a simplified, human-friendly version of the input
     * @throws IllegalArgumentException if rawInput is null or blank
     */
    public String simplify(String rawInput) {
        if (rawInput == null || rawInput.isBlank()) {
            throw new IllegalArgumentException("rawInput must not be null or blank");
        }
        String trimmed = rawInput.trim();
        return Character.toUpperCase(trimmed.charAt(0)) + trimmed.substring(1).toLowerCase();
    }
}
