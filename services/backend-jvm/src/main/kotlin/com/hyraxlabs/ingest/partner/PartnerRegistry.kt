package com.hyraxlabs.ingest.partner

/**
 * Holds the set of configured [PartnerApiClient]s, keyed by their source id.
 *
 * Immutable: registration returns a new registry rather than mutating in place,
 * keeping the wiring side-effect free and easy to reason about in tests.
 */
class PartnerRegistry private constructor(
    private val clients: Map<String, PartnerApiClient>,
) {
    val sources: Set<String> get() = clients.keys

    fun all(): List<PartnerApiClient> = clients.values.toList()

    fun get(source: String): PartnerApiClient? = clients[source]

    fun register(client: PartnerApiClient): PartnerRegistry =
        PartnerRegistry(clients + (client.source to client))

    companion object {
        fun empty(): PartnerRegistry = PartnerRegistry(emptyMap())

        fun of(vararg clients: PartnerApiClient): PartnerRegistry =
            PartnerRegistry(clients.associateBy { it.source })
    }
}
