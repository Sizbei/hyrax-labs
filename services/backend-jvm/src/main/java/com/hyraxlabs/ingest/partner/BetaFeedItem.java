package com.hyraxlabs.ingest.partner;

/**
 * Legacy-style Java DTO mirroring the wire shape of the synthetic "beta-materials"
 * partner feed. Modeled as an immutable value object with explicit getters, which
 * is how the original (pre-Kotlin) integration was written.
 *
 * <p>All field values used in this project are SYNTHETIC sample data.
 */
public final class BetaFeedItem {

    private final String itemCode;
    private final String description;
    private final String classification;
    private final String amount;
    private final String measure;
    private final String timestamp;

    public BetaFeedItem(
            String itemCode,
            String description,
            String classification,
            String amount,
            String measure,
            String timestamp) {
        this.itemCode = itemCode;
        this.description = description;
        this.classification = classification;
        this.amount = amount;
        this.measure = measure;
        this.timestamp = timestamp;
    }

    public String getItemCode() {
        return itemCode;
    }

    public String getDescription() {
        return description;
    }

    public String getClassification() {
        return classification;
    }

    public String getAmount() {
        return amount;
    }

    public String getMeasure() {
        return measure;
    }

    public String getTimestamp() {
        return timestamp;
    }
}
