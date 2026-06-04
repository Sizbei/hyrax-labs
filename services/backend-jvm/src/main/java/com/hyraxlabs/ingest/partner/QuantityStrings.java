package com.hyraxlabs.ingest.partner;

/**
 * Small Java utility for cleaning the free-form quantity strings that partner
 * feeds emit (thousands separators, surrounding whitespace, stray symbols).
 *
 * <p>Kept in Java to demonstrate Kotlin/Java interop: it is consumed from the
 * Kotlin normalizer in the pipeline layer.
 */
public final class QuantityStrings {

    private QuantityStrings() {
        // utility class — no instances
    }

    /**
     * Strips grouping separators and whitespace from a raw quantity token.
     *
     * @param raw the partner-supplied value, may be {@code null}
     * @return a parse-ready numeric string, or an empty string if {@code raw} is null/blank
     */
    public static String clean(String raw) {
        if (raw == null) {
            return "";
        }
        String trimmed = raw.trim();
        if (trimmed.isEmpty()) {
            return "";
        }
        // Remove thousands separators and any non numeric/decimal/sign characters.
        return trimmed.replace(",", "").replaceAll("[^0-9.\\-]", "");
    }
}
