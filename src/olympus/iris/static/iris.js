// Iris — vanilla JS rendering.
// Reads window.OLYMPUS_DATA (a JSON object embedded by the build step)
// and writes to the predeclared mount nodes in the template.
//
// No framework, no fetch, no eval. Strict mode. CSP-clean.

"use strict";

(function () {
    var data = window.OLYMPUS_DATA || {};

    // ── helpers ───────────────────────────────────────────────
    function el(tag, attrs, kids) {
        var node = document.createElement(tag);
        if (attrs) {
            for (var k in attrs) {
                if (k === "class") { node.className = attrs[k]; }
                else if (k === "text") { node.textContent = attrs[k]; }
                else { node.setAttribute(k, attrs[k]); }
            }
        }
        if (kids) {
            for (var i = 0; i < kids.length; i++) {
                var c = kids[i];
                if (c == null) continue;
                node.appendChild(typeof c === "string"
                    ? document.createTextNode(c) : c);
            }
        }
        return node;
    }

    function tshort(ts) {
        if (!ts) return "—";
        var s = String(ts);
        // Trim to YYYY-MM-DD HH:MM
        return s.length >= 16 ? s.substring(0, 10) + " " + s.substring(11, 16) : s;
    }

    function mountTable(parent, headers, rows) {
        if (!rows || !rows.length) {
            parent.appendChild(el("div", {"class": "empty",
                text: "no records yet"}));
            return;
        }
        var thead = el("thead", null,
            [el("tr", null, headers.map(function (h) {
                return el("th", {text: h});
            }))]);
        var tbody = el("tbody", null, rows.map(function (row) {
            return el("tr", null, row.map(function (cell) {
                if (cell && cell.html === true) {
                    var td = el("td");
                    td.appendChild(cell.node);
                    return td;
                }
                return el("td", cell && cell.cls
                    ? {"class": cell.cls, text: String(cell.text)}
                    : {text: String(cell == null ? "" : cell)});
            }));
        }));
        parent.appendChild(el("table", {"class": "iris"}, [thead, tbody]));
    }

    function badge(kind, label) {
        return {html: true, node: el("span", {"class": "badge " + kind, text: label})};
    }

    // ── counts strip ──────────────────────────────────────────
    var countsHost = document.getElementById("counts");
    var c = data.counts || {};
    var countTiles = [
        ["Sessions",    c.sessions || 0],
        ["Prophecies",  c.prophecies || 0],
        ["Proposals",   c.proposals || 0],
        ["Improvements", c.prometheus_passes || 0],
        ["Slices",      c.slices || 0],
        ["Styx oaths",  c.oaths || 0],
    ];
    for (var i = 0; i < countTiles.length; i++) {
        var tile = el("div", {"class": "count-card"}, [
            el("div", {"class": "label", text: countTiles[i][0]}),
            el("div", {"class": "value", text: String(countTiles[i][1])}),
        ]);
        countsHost.appendChild(tile);
    }

    // ── session timeline ──────────────────────────────────────
    var tl = document.getElementById("timeline");
    var sessions = (data.sessions || []).slice().reverse();
    if (!sessions.length) {
        tl.appendChild(el("div", {"class": "empty",
            text: "no sessions in Mnemosyne yet"}));
    } else {
        var box = el("div", {"class": "timeline"});
        for (var s = 0; s < Math.min(15, sessions.length); s++) {
            var ses = sessions[s];
            var stats = el("div", {"class": "stats"}, [
                el("span", {"class": "stat",
                    text: "hydra " + (ses.hydra_findings || 0)}),
                el("span", {"class": "stat",
                    text: "argos " + (ses.argos_pheromones || 0)}),
                el("span", {"class": "stat",
                    text: "proposals " + (ses.proposals || 0)}),
                ses.prophecies_verified > 0
                    ? el("span", {"class": "stat",
                        text: "prophecies " + ses.prophecies_verified})
                    : null,
                (ses.fury_alerts && ses.fury_alerts.length)
                    ? el("span", {"class": "stat",
                        text: "furies " + ses.fury_alerts.length})
                    : null,
            ]);
            var dur = el("span", {"class": "stat",
                text: (ses.duration_ms || 0).toFixed
                    ? (ses.duration_ms || 0) + "ms"
                    : (ses.duration_ms + "ms")});
            box.appendChild(el("div", {"class": "row"}, [
                el("div", {"class": "ts", text: tshort(ses.ts)}),
                stats,
                dur,
            ]));
        }
        tl.appendChild(box);
    }

    // ── slice heatmap ─────────────────────────────────────────
    var hm = document.getElementById("heatmap");
    var slices = data.slice_heatmap || [];
    if (!slices.length) {
        hm.appendChild(el("div", {"class": "empty",
            text: "no findings recorded yet"}));
    } else {
        var grid = el("div", {"class": "heatmap"});
        // header row
        grid.appendChild(el("div", {"class": "heat-row"}, [
            el("div", {"class": "slice-name",
                text: "Slice (top " + slices.length + ")"}),
            el("div", {"class": "heat-cell zero", text: "ALERT"}),
            el("div", {"class": "heat-cell zero", text: "INFO"}),
        ]));
        for (var hi = 0; hi < slices.length; hi++) {
            var sl = slices[hi];
            grid.appendChild(el("div", {"class": "heat-row"}, [
                el("div", {"class": "slice-name", text: sl.slice || "—"}),
                el("div", {"class": "heat-cell "
                    + (sl.alert > 0 ? "alert-cell" : "zero"),
                    text: String(sl.alert || 0)}),
                el("div", {"class": "heat-cell "
                    + (sl.info > 0 ? "info-cell" : "zero"),
                    text: String(sl.info || 0)}),
            ]));
        }
        hm.appendChild(grid);
    }

    // ── prophecies ────────────────────────────────────────────
    var proHost = document.getElementById("prophecies");
    var prophs = (data.prophecies || []).slice().reverse();
    mountTable(proHost,
        ["When", "Prediction", "Outcome", "Horizon"],
        prophs.slice(0, 20).map(function (p) {
            var outcomeBadge;
            if (p.accepted === true) outcomeBadge = badge("accepted", "accepted");
            else if (p.accepted === false) outcomeBadge = badge("rejected", "rejected");
            else outcomeBadge = badge("pending", "pending");
            return [tshort(p.ts), p.name || "—", outcomeBadge, p.horizon || "—"];
        }));
    // acceptance %
    if (prophs.length) {
        var seen = 0, accepted = 0;
        for (var ai = 0; ai < prophs.length; ai++) {
            if (prophs[ai].accepted === true || prophs[ai].accepted === false) {
                seen++;
                if (prophs[ai].accepted === true) accepted++;
            }
        }
        if (seen > 0) {
            var rate = (accepted / seen * 100).toFixed(1);
            document.getElementById("prophecies-rate").textContent =
                " · " + rate + "% accepted (" + accepted + "/" + seen + ")";
        }
    }

    // ── proposals (Hephaestus) ────────────────────────────────
    var pHost = document.getElementById("proposals");
    var props = data.proposals || [];
    mountTable(pHost,
        ["When", "Outcome", "Drift", "Summary"],
        props.slice(0, 20).map(function (pr) {
            var b = pr.outcome === "ratified"
                ? badge("ratified", "ratified")
                : badge("rejected", "rejected");
            return [tshort(pr.ts), b, pr.drift || "—", pr.summary || ""];
        }));

    // ── prometheus passes ─────────────────────────────────────
    var prHost = document.getElementById("prometheus");
    var passes = (data.prometheus_passes || []).slice().reverse();
    mountTable(prHost,
        ["When", "Succeeded", "Invoked", "Summary"],
        passes.slice(0, 15).map(function (p) {
            return [
                tshort(p.ts),
                String(p.succeeded || 0),
                String(p.invoked || 0),
                p.summary || "",
            ];
        }));

    // ── prometheus handlers (per-call) ────────────────────────
    var prhHost = document.getElementById("prometheus-handlers");
    var handlers = (data.prometheus_handlers || []).slice().reverse();
    mountTable(prhHost,
        ["When", "Handler", "Result", "Detail"],
        handlers.slice(0, 25).map(function (h) {
            var b = h.succeeded === false
                ? badge("fail", "fail")
                : badge("ok", "ok");
            return [tshort(h.ts), h.handler || "", b, h.summary || ""];
        }));

    // ── styx panel ────────────────────────────────────────────
    var st = data.styx || {};
    var styxHost = document.getElementById("styx");
    if (!st.total_oaths) {
        styxHost.appendChild(el("div", {"class": "empty",
            text: "no oaths sworn yet"}));
    } else {
        var rows = [
            ["Total oaths", String(st.total_oaths)],
            ["Last seq", String(st.last_seq)],
            ["Last hash", {cls: "mono", text: st.last_hash || "—"}],
            ["Last sworn", tshort(st.last_ts)],
        ];
        var tbody = el("tbody", null, rows.map(function (r) {
            return el("tr", null, [
                el("td", {"class": "mono", text: r[0]}),
                (r[1] && r[1].cls)
                    ? el("td", {"class": r[1].cls, text: r[1].text})
                    : el("td", {text: r[1]}),
            ]);
        }));
        styxHost.appendChild(el("table", {"class": "iris"}, [tbody]));
    }
})();
