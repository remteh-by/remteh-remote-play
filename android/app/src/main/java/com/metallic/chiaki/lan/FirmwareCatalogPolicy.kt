package com.metallic.chiaki.lan

/** Version metadata only. Queries selecting firmware files never leave the app. */
object FirmwareCatalogPolicy {
    fun permits(query: String?, fragment: String?) = query == null && fragment == null
    fun versions(values: Map<String, String>) = values.filter { (family, version) ->
        family in setOf("0004", "000B", "000E", "0044") && version.matches(Regex("0x[0-9a-fA-F]{4}"))
    }
}
