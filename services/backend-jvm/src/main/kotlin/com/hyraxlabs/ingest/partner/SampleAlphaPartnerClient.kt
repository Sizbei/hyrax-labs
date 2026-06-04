package com.hyraxlabs.ingest.partner

import com.hyraxlabs.ingest.domain.SupplierRecord

/**
 * Kotlin reference implementation of [PartnerApiClient] for the synthetic partner
 * "alpha-supply".
 *
 * Returns a deterministic batch of SYNTHETIC sample records. In a real deployment
 * this would issue an authenticated HTTP request to the partner endpoint and
 * deserialize the JSON payload.
 */
class SampleAlphaPartnerClient : PartnerApiClient {

    override val source: String = SOURCE

    override fun fetchRecords(): List<SupplierRecord> = listOf(
        SupplierRecord(
            partnerId = "AL-1001",
            partnerSource = SOURCE,
            name = "Aluminum Sheet 6061",
            rawCategory = "metal",
            rawQuantity = "1,200",
            rawUnit = "kg",
            reportedAt = "2026-05-31T08:00:00Z",
        ),
        SupplierRecord(
            partnerId = "AL-1002",
            partnerSource = SOURCE,
            name = "ABS Pellets",
            rawCategory = "polymer",
            rawQuantity = "550.5",
            rawUnit = "lbs",
            reportedAt = "2026-05-31T08:05:00Z",
        ),
        SupplierRecord(
            partnerId = "AL-1003",
            partnerSource = SOURCE,
            name = "Carbon Fiber Weave",
            rawCategory = "composite",
            rawQuantity = "0.75",
            rawUnit = "tonne",
            reportedAt = "2026-05-31T08:10:00Z",
        ),
    )

    companion object {
        const val SOURCE = "alpha-supply"
    }
}
