package com.hyraxlabs.ingest.partner;

import com.hyraxlabs.ingest.domain.SupplierRecord;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Legacy-style Java implementation of the Kotlin {@link PartnerApiClient}
 * interface for the synthetic partner "beta-materials".
 *
 * <p>This class demonstrates Java consuming Kotlin types directly: it implements
 * a Kotlin interface, reads a Kotlin enum / data class, and constructs the Kotlin
 * {@link SupplierRecord} data class via its generated Java constructor.
 *
 * <p>In production this would call the partner's REST endpoint and map the JSON
 * payload into {@link BetaFeedItem} DTOs; here it returns SYNTHETIC sample data.
 */
public final class LegacyBetaPartnerClient implements PartnerApiClient {

    public static final String SOURCE = "beta-materials";

    private final List<BetaFeedItem> sampleFeed;

    public LegacyBetaPartnerClient() {
        List<BetaFeedItem> items = new ArrayList<>();
        items.add(new BetaFeedItem(
                "BX-77", "Stainless Rod 304", "metal", "3.2", "metric_ton", "2026-05-31T07:50:00Z"));
        items.add(new BetaFeedItem(
                "BX-78", "Nylon 6 Granulate", "polymer", "900", "kg", "2026-05-31T07:55:00Z"));
        // Intentional duplicate of an alpha-supply item to exercise dedup:
        items.add(new BetaFeedItem(
                "BX-79", "Aluminum Sheet 6061", "metal", "1200", "kg", "2026-05-31T08:00:00Z"));
        // Malformed quantity to exercise normalizer robustness:
        items.add(new BetaFeedItem(
                "BX-80", "Polyester Fabric", "textile", "n/a", "kg", "2026-05-31T08:02:00Z"));
        this.sampleFeed = Collections.unmodifiableList(items);
    }

    /** Non-null accessor backing the Kotlin {@code val source} property. */
    @Override
    public String getSource() {
        return SOURCE;
    }

    @Override
    public List<SupplierRecord> fetchRecords() {
        List<SupplierRecord> records = new ArrayList<>(sampleFeed.size());
        for (BetaFeedItem item : sampleFeed) {
            records.add(new SupplierRecord(
                    item.getItemCode(),
                    SOURCE,
                    item.getDescription(),
                    item.getClassification(),
                    item.getAmount(),
                    item.getMeasure(),
                    item.getTimestamp()));
        }
        return Collections.unmodifiableList(records);
    }
}
