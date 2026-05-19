// Agora — shared client-side JS.
// Pages use these helpers to fetch from the read-only HTTP API.
// Vanilla. No framework. No build step.

"use strict";

(function () {
    // Note: API_BASE and INTERVAL_MS are substituted at build time
    var API_BASE = "__API_BASE__";
    var INTERVAL_MS = __INTERVAL_MS__;

    window.AGORA = {
        API_BASE: API_BASE,
        INTERVAL_MS: INTERVAL_MS,

        // Fetch JSON from the HTTP API with timeout + error capture.
        get: function (path, cb) {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", API_BASE + path, true);
            xhr.timeout = 6000;
            xhr.onload = function () {
                if (xhr.status === 200) {
                    try { cb(null, JSON.parse(xhr.responseText)); }
                    catch (e) { cb(e, null); }
                } else { cb(new Error("HTTP " + xhr.status), null); }
            };
            xhr.onerror = function () { cb(new Error("network"), null); };
            xhr.ontimeout = function () { cb(new Error("timeout"), null); };
            xhr.send();
        },

        post: function (path, body, cb) {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", API_BASE + path, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.timeout = 30000;
            xhr.onload = function () {
                var ok = (xhr.status >= 200 && xhr.status < 300);
                try {
                    var parsed = JSON.parse(xhr.responseText);
                    cb(ok ? null : new Error("HTTP " + xhr.status), parsed);
                } catch (e) { cb(e, null); }
            };
            xhr.onerror = function () { cb(new Error("network"), null); };
            xhr.ontimeout = function () { cb(new Error("timeout"), null); };
            xhr.send(JSON.stringify(body || {}));
        },

        setStatus: function (ok, text) {
            var dot = document.getElementById("status-dot");
            var lbl = document.getElementById("status-text");
            if (dot) dot.className = "status-dot" + (ok ? "" : " bad");
            if (lbl) lbl.textContent = text;
        },

        // Simple element builder
        el: function (tag, attrs, kids) {
            var node = document.createElement(tag);
            if (attrs) {
                for (var k in attrs) {
                    if (k === "class") node.className = attrs[k];
                    else if (k === "text") node.textContent = attrs[k];
                    else if (k === "html") node.innerHTML = attrs[k];
                    else node.setAttribute(k, attrs[k]);
                }
            }
            if (kids) for (var i = 0; i < kids.length; i++) {
                var c = kids[i];
                if (c == null) continue;
                node.appendChild(typeof c === "string"
                    ? document.createTextNode(c) : c);
            }
            return node;
        },
    };
})();
