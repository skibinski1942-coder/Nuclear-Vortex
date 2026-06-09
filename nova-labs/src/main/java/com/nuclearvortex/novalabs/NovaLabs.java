package com.nuclearvortex.novalabs;

import com.nuclearvortex.core.Company;

import java.util.Objects;

/**
 * Nova Labs — the Research &amp; Development and innovation hub of
 * Nuclear-Vortex.
 *
 * <p>Nova Labs takes the hardest, most confusing problems in human-computer
 * interaction and systematically breaks them down into clear, solvable
 * challenges. Each solved challenge becomes a patent, a product feature, or
 * an entirely new company within the Nuclear-Vortex family.</p>
 *
 * <p>Revenue model: IP licensing, government research grants, and incubation
 * fees from spin-out companies.</p>
 */
public final class NovaLabs implements Company {

    private static final String NAME = "Nova Labs";
    private static final String TAGLINE = "Tomorrow's answers, today.";
    private static final String MISSION =
            "Pioneer the science and engineering of human-centered simplicity: "
            + "research how people think, build prototypes that test those insights, "
            + "and transfer proven innovations into products that improve everyday life.";
    private static final String DOMAIN = "Research & Development";
    private static final int SIMPLICITY_SCORE = 8;

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
     * Measures the Clarity Index of a given technology description.
     *
     * <p>The Clarity Index is a heuristic score (0–100) that estimates how
     * understandable a piece of technology is to a non-expert human, based on
     * the ratio of simple words to total words in its description.</p>
     *
     * <p>Simple words are defined here as words of 6 characters or fewer —
     * a well-established proxy used in readability research.</p>
     *
     * @param description a plain-text description of the technology; must not
     *                    be null or blank
     * @return Clarity Index score between 0 and 100 (higher is clearer)
     * @throws IllegalArgumentException if description is null or blank
     */
    public int clarityIndex(String description) {
        if (description == null || description.isBlank()) {
            throw new IllegalArgumentException("description must not be null or blank");
        }
        String[] words = description.trim().split("\\s+");
        long simpleWordCount = 0;
        for (String word : words) {
            String cleaned = word.replaceAll("[^a-zA-Z]", "");
            if (cleaned.length() <= 6) {
                simpleWordCount++;
            }
        }
        return (int) Math.round((simpleWordCount * 100.0) / words.length);
    }

    /**
     * Generates a concise innovation brief for the given problem statement.
     *
     * <p>The brief follows the Nova Labs three-part format:
     * <ol>
     *   <li>Problem (what is confusing?)</li>
     *   <li>Hypothesis (what might make it clearer?)</li>
     *   <li>Metric (how will we measure clarity?)</li>
     * </ol>
     * </p>
     *
     * @param problemStatement a description of the human problem to solve;
     *                         must not be null or blank
     * @return formatted innovation brief
     * @throws IllegalArgumentException if problemStatement is null or blank
     */
    public String generateInnovationBrief(String problemStatement) {
        Objects.requireNonNull(problemStatement, "problemStatement must not be null");
        if (problemStatement.isBlank()) {
            throw new IllegalArgumentException("problemStatement must not be blank");
        }
        return "=== Nova Labs Innovation Brief ===\n"
             + "Problem   : " + problemStatement.trim() + "\n"
             + "Hypothesis: If we reduce steps and plain-language the interface, "
             + "user comprehension will increase by ≥30%.\n"
             + "Metric    : Clarity Index score target ≥ 75 / 100.";
    }
}
