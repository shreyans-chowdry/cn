package com.scamshield.app.detector

import org.json.JSONObject
import java.net.Inet4Address
import java.net.Inet6Address
import java.net.InetAddress
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Port of scamshield.net.urlintel: lexical link checks plus (optionally) a real DNS lookup of
 * each host, with every resolved address classified against the special-purpose CIDR registry.
 */
class LinkIntel(cfg: JSONObject) {
    data class Link(val url: String, val host: String, val risk: Double, val reasons: List<String>,
                    val addresses: List<String> = emptyList(), val dnsMs: Double? = null)

    private val shorteners = cfg.getJSONArray("shorteners").toStringList().toHashSet()
    private val riskyTlds = cfg.getJSONArray("risky_tlds").toStringList().toHashSet()
    private val official: Map<String, Set<String>> = cfg.getJSONObject("official").let { o ->
        o.keys().asSequence().associateWith { o.getJSONArray(it).toStringList().toSet() }
    }

    companion object {
        private val URL_RE = Regex(
            "(?:(?:https?://)|(?:www\\.))?(?:\\[[0-9a-fA-F:]+\\]|(?:\\d{1,3}\\.){3}\\d{1,3}|(?:[\\w\\-]+\\.)+[A-Za-z\\u00a1-\\uffff]{2,}|xn--[\\w\\-]+(?:\\.[\\w\\-]+)+)(?::\\d{2,5})?(?:/\\S*)?"
        )
        private val IPV4 = Regex("^(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})$")

        /** Special-purpose IPv4 ranges (RFC 6890) as (network, prefix, description). */
        private val SPECIAL4 = listOf(
            Triple("0.0.0.0", 8, "this network"), Triple("10.0.0.0", 8, "private (RFC 1918)"),
            Triple("100.64.0.0", 10, "carrier-grade NAT"), Triple("127.0.0.0", 8, "loopback"),
            Triple("169.254.0.0", 16, "link-local"), Triple("172.16.0.0", 12, "private (RFC 1918)"),
            Triple("192.0.2.0", 24, "documentation"), Triple("192.168.0.0", 16, "private (RFC 1918)"),
            Triple("198.18.0.0", 15, "benchmarking"), Triple("198.51.100.0", 24, "documentation"),
            Triple("203.0.113.0", 24, "documentation"), Triple("224.0.0.0", 4, "multicast"),
            Triple("240.0.0.0", 4, "reserved"),
        )
        private val RISKY = listOf("private", "loopback", "link-local", "carrier-grade", "this network",
            "reserved", "multicast", "unique local")

        fun ipv4ToLong(ip: String): Long? {
            val m = IPV4.matchEntire(ip) ?: return null
            var n = 0L
            for (g in m.groupValues.drop(1)) {
                val o = g.toInt(); if (o > 255) return null
                n = (n shl 8) or o.toLong()
            }
            return n
        }

        /** Longest-prefix match of an IPv4 address against the special ranges (CIDR, Module 4). */
        fun classifyIp(ip: String): String? {
            if (ip.contains(':')) {
                val l = ip.lowercase()
                return when {
                    l == "::1" -> "loopback"
                    l.startsWith("fe8") || l.startsWith("fe9") || l.startsWith("fea") || l.startsWith("feb") -> "link-local"
                    l.startsWith("fc") || l.startsWith("fd") -> "unique local (private)"
                    l.startsWith("2001:db8") -> "documentation"
                    else -> null
                }
            }
            val n = ipv4ToLong(ip) ?: return null
            var best: Pair<Int, String>? = null
            for ((net, prefix, why) in SPECIAL4) {
                val mask = if (prefix == 0) 0L else (0xFFFFFFFFL shl (32 - prefix)) and 0xFFFFFFFFL
                if ((n and mask) == (ipv4ToLong(net)!! and mask) && (best == null || prefix > best.first)) best = prefix to why
            }
            return best?.second
        }

        private val pool = Executors.newCachedThreadPool()
    }

    fun extract(text: String): List<Pair<String, String>> {
        val out = ArrayList<Pair<String, String>>()
        for (m in URL_RE.findAll(text)) {
            var u = m.value.replace(Regex("-[\\u0B80-\\u0BFF]+$"), "").trimEnd('.', ',', ';', ':', '!', '?', ')', '\'', '"')
            if (m.range.first > 0 && text[m.range.first - 1] == '@') continue
            val host = u.replace(Regex("^https?://", RegexOption.IGNORE_CASE), "").substringBefore('/')
                .substringBefore(':').trim('[', ']').lowercase()
            if (ipv4ToLong(host) != null) { out.add(u to host); continue }
            if (!host.contains('.') || host.replace(".", "").all { it.isDigit() }) continue
            val tld = host.substringAfterLast('.')
            if (tld.length < 2 || tld.all { it.isDigit() }) continue
            if (host.substringBefore('.') in setOf("rs", "inr", "a/c", "no", "ref", "avl", "bal")) continue
            out.add(u to host)
        }
        return out
    }

    private fun registered(host: String): String {
        val p = host.split('.')
        return if (p.size >= 3 && p[p.size - 2] in setOf("co", "org", "net", "gov", "ac") && p.last().length == 2)
            p.takeLast(3).joinToString(".") else p.takeLast(2).joinToString(".")
    }

    fun lexical(url: String, host: String): Pair<Double, List<String>> {
        val reasons = ArrayList<String>()
        var s = 0.0
        val reg = registered(host)
        val tld = host.substringAfterLast('.')
        val isIp = ipv4ToLong(host) != null
        if (isIp) {
            reasons += "Link uses a raw IP address instead of a domain name"; s += 0.45
            classifyIp(host)?.let { why -> if (RISKY.any { why.contains(it) }) { reasons += "IP is in a $why range"; s += 0.3 } }
        }
        if (reg in shorteners) { reasons += "URL shortener ($reg) hides the real destination"; s += 0.25 }
        if (host.startsWith("xn--") || host.contains(".xn--") || host.any { it.code > 127 }) {
            reasons += "Internationalised (punycode) domain, possible look-alike letters"; s += 0.35
        }
        if (tld in riskyTlds) { reasons += ".$tld is a domain ending heavily used for throwaway scam sites"; s += 0.3 }
        val compact = host.filter { it in 'a'..'z' }
        for ((brand, offi) in official) {
            if (compact.contains(brand) && reg !in offi && host !in offi) {
                reasons += "Mentions '$brand' but is not an official $brand domain"; s += 0.45; break
            }
        }
        if (host.count { it == '-' } >= 2 || reg.count { it.isDigit() } >= 3) { reasons += "Many hyphens or digits in the domain"; s += 0.1 }
        if (host.count { it == '.' } >= 3 && !isIp) { reasons += "Deeply nested subdomain"; s += 0.1 }
        if (url.lowercase().startsWith("http://")) { reasons += "Plain http (no TLS)"; s += 0.05 }
        return minOf(s, 1.0) to reasons
    }

    /** System DNS lookup with a timeout; every address is checked against the CIDR registry. */
    private fun dns(host: String): Triple<Double, List<String>, Pair<List<String>, Double>?> {
        if (ipv4ToLong(host) != null) return Triple(0.0, emptyList(), null)
        val t0 = System.nanoTime()
        return try {
            val f = pool.submit<Array<InetAddress>> { InetAddress.getAllByName(host) }
            val addrs = f.get(2500, TimeUnit.MILLISECONDS)
            val ms = (System.nanoTime() - t0) / 1e6
            val ips = addrs.map { it.hostAddress ?: "" }
            val reasons = ArrayList<String>()
            var s = 0.0
            for (a in addrs) {
                val why = classifyIp(a.hostAddress ?: continue)
                if (why != null && RISKY.any { why.contains(it) }) {
                    reasons += "Resolves to ${a.hostAddress}, a $why address"; s += 0.4; break
                }
            }
            val v6 = addrs.count { it is Inet6Address }
            val v4 = addrs.count { it is Inet4Address }
            Triple(s, reasons, (ips + listOf("($v4 IPv4, $v6 IPv6)")) to ms)
        } catch (e: java.util.concurrent.ExecutionException) {
            if (e.cause is java.net.UnknownHostException)
                Triple(0.35, listOf("Domain does not exist in DNS (NXDOMAIN)"), emptyList<String>() to (System.nanoTime() - t0) / 1e6)
            else Triple(0.0, emptyList(), null)
        } catch (e: Exception) {
            Triple(0.0, emptyList(), null)
        }
    }

    fun analyse(text: String, resolveDns: Boolean): List<Link> = extract(text).map { (url, host) ->
        val (sl, rl) = lexical(url, host)
        if (resolveDns) {
            val (sd, rd, info) = dns(host)
            Link(url, host, minOf(1.0, sl + sd), rl + rd, info?.first ?: emptyList(), info?.second)
        } else Link(url, host, sl, rl)
    }
}
