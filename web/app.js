"use strict";
/* Tabularium – Weboberfläche. Alle Inhalte werden als Text gesetzt, nie als HTML. */

const TOKEN = document.querySelector('meta[name="tabularium-token"]').content;
const $ = (s, el = document) => el.querySelector(s);

const zustand = {
  status: null,
  auswahl: [],        // {art: "pfad"|"upload", pfad?, datei?, name}
  dok: null,          // Daten des geöffneten Dokuments
  vergleich: null,
  gewaehlt: null,     // gewählte Version (Nummer)
};

/* ---------- Hilfen ---------- */

function h(tag, attrs, ...kinder) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "text") el.textContent = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kind of kinder.flat()) {
    if (kind === null || kind === undefined || kind === false) continue;
    el.append(kind instanceof Node ? kind : document.createTextNode(String(kind)));
  }
  return el;
}

async function api(pfad, { methode = "GET", daten, roh, kopf = {} } = {}) {
  const opt = { method: methode, headers: { "X-Tabularium-Token": TOKEN, ...kopf } };
  if (daten !== undefined) {
    opt.headers["Content-Type"] = "application/json";
    opt.body = JSON.stringify(daten);
  }
  if (roh) opt.body = roh;
  let r;
  try { r = await fetch(pfad, opt); }
  catch (e) { throw new Error("Keine Verbindung zu Tabularium – läuft das Programm noch?"); }
  let j = {};
  try { j = await r.json(); } catch (e) { /* leer */ }
  if (!r.ok) throw new Error(j.fehler || ("Fehler " + r.status));
  return j;
}

function datum(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }) +
    ", " + d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
}

function relativ(iso) {
  const d = new Date(iso);
  const s = (Date.now() - d.getTime()) / 1000;
  if (s < 60) return "gerade eben";
  if (s < 3600) return "vor " + Math.floor(s / 60) + " Min.";
  if (s < 86400) return "vor " + Math.floor(s / 3600) + " Std.";
  return datum(iso);
}

function aenderungstext(a, version) {
  if (!a) return "Zellinhalt nicht lesbar";
  if (version === 1) return "Erstfassung";
  const teile = [];
  if (a.geaendert) teile.push(a.geaendert + " geändert");
  if (a.neu) teile.push(a.neu + " neu");
  if (a.geloescht) teile.push(a.geloescht + " gelöscht");
  return teile.length ? teile.join(", ") : "keine Zelländerung";
}

let toastTimer;
function meldung(text, fehler = false) {
  const t = $("#toast");
  t.textContent = text;
  t.className = "sichtbar" + (fehler ? " fehler" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.className = fehler ? "fehler" : ""; }, fehler ? 6000 : 3500);
}

async function mitKnopf(knopf, fn) {
  knopf.disabled = true;
  try { return await fn(); }
  catch (e) { meldung(e.message, true); }
  finally { knopf.disabled = false; }
}

/* ---------- Status / Übersicht ---------- */

async function statusLaden() {
  try {
    zustand.status = await api("/api/status");
    zeichneKopf();
    zeichneDokumente();
    zeichneProtokoll();
    zeichnePruefung();
  } catch (e) {
    meldung(e.message, true);
  }
}

function zeichneKopf() {
  const s = zustand.status;
  $("#archivpfad").textContent = s.archiv_kurz || s.archiv;
  $("#archivpfad").title = s.archiv;
}

const STATUS = {
  aktuell: ["ok", "gesichert"],
  geaendert: ["warn", "geändert – nicht gesichert"],
  fehlt: ["", "Datei nicht am Ort"],
  hochgeladen: ["", "hochgeladen"],
};

function zeichneDokumente() {
  const docs = zustand.status.dokumente;
  const filter = $("#dok-filter").value.trim().toLowerCase();
  const tbody = $("#dok-tabelle tbody");
  tbody.replaceChildren();
  $("#dok-leer").hidden = docs.length > 0;
  $("#dok-tabelle").hidden = docs.length === 0;
  for (const d of docs) {
    if (filter && !(d.name.toLowerCase().includes(filter) ||
                    (d.quelle || "").toLowerCase().includes(filter))) continue;
    const [klasse, text] = STATUS[d.status] || ["", d.status];
    const aktion = d.status === "geaendert"
      ? h("button", { class: "knopf klein", text: "Jetzt sichern",
          onclick: (ev) => { ev.stopPropagation(); mitKnopf(ev.currentTarget, () => sichernPfade([d.quelle], $("#f-notiz").value.trim(), $("#f-bearbeiter").value.trim())); } })
      : null;
    const zeile = h("tr", { tabindex: "0", onclick: () => { location.hash = "#/dok/" + encodeURIComponent(d.name); },
                            onkeydown: (ev) => { if (ev.key === "Enter") location.hash = "#/dok/" + encodeURIComponent(d.name); } },
      h("td", {}, h("div", { class: "dok-name", text: d.name }),
        d.quelle && d.status !== "hochgeladen" ? h("div", { class: "dok-quelle", text: d.quelle_kurz || d.quelle }) : null),
      h("td", { class: "zahl", text: d.versionen }),
      h("td", { title: datum(d.zuletzt), text: relativ(d.zuletzt) }),
      h("td", {}, h("span", { class: "chip " + klasse, text: text })),
      h("td", { class: "zahl" }, aktion));
    tbody.append(zeile);
  }
}

function zeichneProtokoll() {
  const ul = $("#protokoll");
  ul.replaceChildren();
  const liste = zustand.status.protokoll;
  if (!liste.length) {
    ul.append(h("li", { class: "klein", text: "Noch keine Aktivität in dieser Sitzung." }));
    return;
  }
  for (const p of liste) {
    ul.append(h("li", {}, h("span", { class: "zeit", text: p.zeit }),
      h("span", { class: p.art, text: p.text })));
  }
}

function zeichnePruefung() {
  const p = zustand.status.pruefung;
  const b = $("#pruefbanner");
  if (!p) { b.hidden = true; return; }
  b.hidden = false;
  b.className = "banner " + (p.ok ? "ok" : "fehler");
  b.replaceChildren();
  const inhalt = h("div", {});
  if (p.ok) {
    inhalt.append(h("div", { class: "titel", text: "✔ Archiv unversehrt" }),
      h("div", { class: "klein", text:
        `${p.anzahl} Einträge geprüft · Hash-Kette lückenlos · alle Dateien unverändert · ` +
        `${p.zeitstempel} gültige Zeitstempel · geprüft ${datum(p.zeit)}` }));
  } else {
    inhalt.append(h("div", { class: "titel", text: `✘ Prüfung fehlgeschlagen – ${p.fehler.length} Problem(e)` }),
      h("ul", {}, p.fehler.map((f) => h("li", { text: f }))));
  }
  for (const hw of p.hinweise || []) inhalt.append(h("div", { class: "klein", text: "Hinweis: " + hw }));
  b.append(inhalt, h("button", { class: "knopf leise klein", text: "Ausblenden",
    onclick: () => { b.hidden = true; } }));
}

/* ---------- Sichern ---------- */

function zeichneAuswahl() {
  const ul = $("#auswahl");
  ul.replaceChildren();
  zustand.auswahl.forEach((a, i) => {
    ul.append(h("li", {},
      h("div", { style: null },
        h("div", { class: "name", text: a.name, title: a.pfad || a.name }),
        h("div", { class: "art", text: a.art === "pfad" ? "vom Speicherort" : "hochladen" })),
      h("button", { class: "knopf leise klein", "aria-label": "Entfernen", text: "✕",
        onclick: () => { zustand.auswahl.splice(i, 1); zeichneAuswahl(); } })));
  });
  $("#sichern-form").hidden = zustand.auswahl.length === 0;
}

function ergebnisMelden(ergebnisse) {
  const texte = ergebnisse.map((e) => {
    if (!e.ok) return `${e.datei}: ${e.meldung}`;
    if (e.unveraendert) return `${e.datei}: ${e.meldung}`;
    let t = `${e.datei}: Version ${e.version} gesichert (${aenderungstext(e.aenderungen, e.version)})`;
    if (e.zeitstempel_fehler) t += " – Zeitstempel fehlgeschlagen";
    return t;
  });
  meldung(texte.join(" · "), ergebnisse.some((e) => !e.ok));
}

async function sichernPfade(pfade, notiz, bearbeiter) {
  const r = await api("/api/einchecken", { methode: "POST", daten: {
    pfade, notiz: notiz || "", bearbeiter: bearbeiter || localStorage.getItem("bearbeiter") || "" } });
  ergebnisMelden(r.ergebnisse);
  await statusLaden();
}

async function sichernAuswahl() {
  const notiz = $("#f-notiz").value.trim();
  const bearbeiter = $("#f-bearbeiter").value.trim();
  localStorage.setItem("bearbeiter", bearbeiter);
  const ergebnisse = [];
  const pfade = zustand.auswahl.filter((a) => a.art === "pfad").map((a) => a.pfad);
  if (pfade.length) {
    const r = await api("/api/einchecken", { methode: "POST", daten: { pfade, notiz, bearbeiter } });
    ergebnisse.push(...r.ergebnisse);
  }
  for (const a of zustand.auswahl.filter((x) => x.art === "upload")) {
    try {
      const r = await api("/api/hochladen", { methode: "POST", roh: a.datei, kopf: {
        "Content-Type": "application/octet-stream",
        "X-Dateiname": encodeURIComponent(a.name),
        "X-Notiz": encodeURIComponent(notiz),
        "X-Bearbeiter": encodeURIComponent(bearbeiter) } });
      ergebnisse.push(...r.ergebnisse);
    } catch (e) {
      ergebnisse.push({ datei: a.name, ok: false, meldung: e.message });
    }
  }
  ergebnisMelden(ergebnisse);
  zustand.auswahl = [];
  $("#f-notiz").value = "";
  zeichneAuswahl();
  await statusLaden();
}

const ENDUNGEN = [".xlsx", ".xlsm", ".xltx", ".xltm", ".ods", ".ots", ".fods", ".xls", ".xlsb", ".xlt"];

function dateienAblegen(liste) {
  let abgelehnt = 0;
  for (const f of liste) {
    const ok = ENDUNGEN.some((e) => f.name.toLowerCase().endsWith(e));
    if (!ok) { abgelehnt++; continue; }
    zustand.auswahl.push({ art: "upload", datei: f, name: f.name });
  }
  if (abgelehnt) meldung(`${abgelehnt} Datei(en) übersprungen – kein Tabellenformat.`, true);
  zeichneAuswahl();
  if (zustand.auswahl.length) $("#f-notiz").focus();
}

/* ---------- Dokumentansicht ---------- */

async function dokumentOeffnen(name, version) {
  $("#ansicht-liste").hidden = true;
  $("#ansicht-dokument").hidden = false;
  window.scrollTo(0, 0);
  try {
    zustand.dok = await api("/api/dokument?name=" + encodeURIComponent(name));
  } catch (e) {
    meldung(e.message, true);
    location.hash = "#/";
    return;
  }
  const d = zustand.dok;
  document.title = d.name + " – Tabularium";
  $("#d-name").textContent = d.name;
  const q = $("#d-quelle");
  q.replaceChildren();
  if (d.quelle && d.quelle_existiert) {
    const manager = (zustand.status && zustand.status.dateimanager) || "Finder";
    q.append(d.quelle_kurz || d.quelle, h("button", { class: "knopf leise klein", text: "Im " + manager + " zeigen",
      onclick: (ev) => mitKnopf(ev.currentTarget, () => api("/api/finder", { methode: "POST", daten: { pfad: d.quelle } })) }));
  } else if (d.quelle) {
    q.textContent = (d.quelle_kurz || d.quelle) + (d.quelle.startsWith("/") ? " (nicht mehr vorhanden)" : "");
  }
  $("#d-aktuell").hidden = !d.quelle_existiert;

  const ol = $("#d-versionen");
  ol.replaceChildren();
  for (const v of [...d.versionen].reverse()) {
    const wer = v.bearbeiter ? `${v.bearbeiter}` : v.nutzer;
    ol.append(h("li", {}, h("button", { "data-v": v.version, onclick: () => versionWaehlen(v.version) },
      h("div", { class: "v-kopf" }, h("span", { class: "v-nr", text: "Version " + v.version }),
        h("span", { class: "v-zeit", text: datum(v.zeit) })),
      h("div", { class: "v-info", text: `${wer} · ${aenderungstext(v.aenderungen, v.version)}` }),
      v.notiz ? h("div", { class: "v-notiz", text: v.notiz }) : null,
      v.zeitstempel ? h("div", { class: "v-zs", text: "⏱ Zeitstempel " + v.zeitstempel }) : null)));
  }
  const optionen = (sel, mitLeer) => {
    sel.replaceChildren();
    if (mitLeer) sel.append(h("option", { value: "", text: "–" }));
    for (const v of d.versionen) sel.append(h("option", { value: v.version, text: "Version " + v.version }));
  };
  optionen($("#d-von"), true);
  optionen($("#d-bis"), false);
  const letzte = d.versionen[d.versionen.length - 1].version;
  await versionWaehlen(version && version <= letzte ? version : letzte);
}

async function versionWaehlen(nr) {
  zustand.gewaehlt = nr;
  const von = nr > 1 ? nr - 1 : "";
  $("#d-von").value = von;
  $("#d-bis").value = nr;
  document.querySelectorAll("#d-versionen button").forEach((b) =>
    b.classList.toggle("gewaehlt", Number(b.dataset.v) === nr));
  await vergleichLaden({ von, bis: nr });
}

async function vergleichLaden({ von, bis, aktuell }) {
  const d = zustand.dok;
  let url = "/api/vergleich?name=" + encodeURIComponent(d.name);
  if (aktuell) url += "&aktuell=1";
  else {
    if (von) url += "&von=" + von;
    url += "&bis=" + bis;
  }
  const hinweis = $("#d-hinweis");
  hinweis.hidden = true;
  try {
    zustand.vergleich = await api(url);
  } catch (e) {
    zustand.vergleich = null;
    hinweis.hidden = false;
    hinweis.textContent = e.message;
    $("#d-tabelle tbody").replaceChildren();
    $("#d-summe").textContent = "";
    $("#d-meta").textContent = "";
    fussZeichnen(bis);
    return;
  }
  const v = zustand.vergleich;
  if (aktuell) {
    $("#d-titel").textContent = `Version ${v.von} → aktuelle Datei (nicht gesichert)`;
  } else if (v.von) {
    $("#d-titel").textContent = `Änderungen Version ${v.von} → ${v.bis}`;
  } else {
    $("#d-titel").textContent = `Inhalt der Erstfassung (Version ${v.bis})`;
  }
  const meta = [];
  if (!aktuell) {
    const ver = d.versionen.find((x) => x.version === v.bis);
    if (ver) {
      meta.push("gesichert " + datum(ver.zeit), "von " + (ver.bearbeiter ? `${ver.bearbeiter} (${ver.nutzer})` : ver.nutzer));
      if (ver.notiz) meta.push("„" + ver.notiz + "“");
    }
  }
  if (v.blaetter_neu.length) meta.push("Blatt neu: " + v.blaetter_neu.join(", "));
  if (v.blaetter_entfernt.length) meta.push("Blatt entfernt: " + v.blaetter_entfernt.join(", "));
  $("#d-meta").textContent = meta.join(" · ");
  if (v.gekuerzt) {
    hinweis.hidden = false;
    hinweis.textContent = `Es gibt ${v.gesamt} Änderungen – angezeigt werden die ersten 5000. Der Prüfbericht enthält mehr.`;
  }
  const blaetter = [...new Set(v.aenderungen.map((a) => a.zelle.slice(0, a.zelle.lastIndexOf("!"))))];
  const sel = $("#d-blatt");
  sel.replaceChildren(h("option", { value: "", text: "Alle Blätter" }),
    ...blaetter.map((b) => h("option", { value: b, text: b })));
  sel.hidden = blaetter.length < 2;
  zeichneAenderungen();
  fussZeichnen(aktuell ? null : v.bis);
}

function fussZeichnen(version) {
  const d = zustand.dok;
  const ver = version ? d.versionen.find((x) => x.version === version) : null;
  $("#d-download").hidden = !ver;
  $("#d-hash").textContent = ver ? "SHA-256 " + ver.datei_sha256 : "";
  $("#d-hash").title = ver ? ver.datei_sha256 : "";
}

/* Anzeige im deutschen Format; gespeichert bleibt der Rohwert (Tooltip). */
function anzeigeWert(w) {
  const s = String(w);
  if (/^-?(0|[1-9]\d{0,14})\.\d+$/.test(s)) return s.replace(".", ",");   // nur Dezimalkomma
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return `${m[3]}.${m[2]}.${m[1]}`;
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2}(:\d{2})?)/);
  if (m) return `${m[3]}.${m[2]}.${m[1]} ${m[4]}`;
  return s;
}

function wertKnoten(inhalt, klasse) {
  if (!inhalt) return h("span", { class: "leerwert", text: "–" });
  const [wert, formel] = inhalt;
  const anzeige = wert === "" ? null : anzeigeWert(wert);
  return h("div", { class: klasse || null, title: anzeige !== null && anzeige !== String(wert) ? "gespeichert: " + wert : null },
    wert === "" ? h("span", { class: "leerwert", text: "(leer)" }) : anzeige,
    formel ? h("span", { class: "formel", text: formel }) : null);
}

const ARTEN = { neu: "neu", geaendert: "geändert", geloescht: "gelöscht" };

function zeichneAenderungen() {
  const v = zustand.vergleich;
  const tbody = $("#d-tabelle tbody");
  tbody.replaceChildren();
  if (!v) return;
  const blatt = $("#d-blatt").value;
  const suche = $("#d-suche").value.trim().toLowerCase();
  let n = 0;
  const frag = document.createDocumentFragment();
  for (const a of v.aenderungen) {
    if (blatt && !a.zelle.startsWith(blatt + "!")) continue;
    if (suche) {
      const text = [a.zelle, ...(a.alt || []), ...(a.neu || [])].join(" ").toLowerCase();
      if (!text.includes(suche)) continue;
    }
    n++;
    frag.append(h("tr", { class: a.art },
      h("td", { class: "zelle", text: a.zelle }),
      h("td", {}, h("span", { class: "chip " + a.art, text: ARTEN[a.art] })),
      h("td", {}, wertKnoten(a.alt, "alt")),
      h("td", {}, wertKnoten(a.neu))));
  }
  if (!v.aenderungen.length) {
    frag.append(h("tr", {}, h("td", { colspan: "4", class: "leer",
      text: "Keine Änderungen an Werten oder Formeln (evtl. nur Formatierung)." })));
  }
  tbody.append(frag);
  const z = v.zaehlung;
  $("#d-summe").textContent = v.von
    ? `${z.geaendert} geändert · ${z.neu} neu · ${z.geloescht} gelöscht` + (n !== v.aenderungen.length ? ` · ${n} angezeigt` : "")
    : `${v.gesamt} Zellen` + (n !== v.aenderungen.length ? ` · ${n} angezeigt` : "");
}

/* ---------- Einstellungen ---------- */

function zeichneEinstellungen() {
  const s = zustand.status;
  $("#e-version").textContent = `Tabularium ${s.version}` + (s.app ? " · installierte App" : "");
  $("#e-autostart-zeile").hidden = s.autostart === null || s.autostart === undefined;
  $("#e-autostart").checked = !!s.autostart;
  $("#e-zs").checked = !!s.einstellungen.zeitstempel;
  $("#e-tsa").value = s.einstellungen.tsa_url || "";
  $("#e-archiv").textContent = s.archiv_kurz || s.archiv;
  const ul = $("#e-ordner");
  ul.replaceChildren();
  if (!s.ueberwachung.length) ul.append(h("li", { class: "leer klein", text: "Kein Ordner überwacht." }));
  for (const o of s.ueberwachung) {
    ul.append(h("li", {}, h("span", { title: o.pfad, text: (o.kurz || o.pfad) + (o.rekursiv ? "  (mit Unterordnern)" : "") }),
      h("button", { type: "button", class: "knopf leise klein", text: "Entfernen",
        onclick: (ev) => mitKnopf(ev.currentTarget, async () => {
          await api("/api/ueberwachung", { methode: "POST", daten: { aktion: "entfernen", pfad: o.pfad } });
          await statusLaden(); zeichneEinstellungen();
        }) })));
  }
}

/* ---------- Routing ---------- */

function route() {
  const m = location.hash.match(/^#\/dok\/([^/]+)(?:\/(\d+))?$/);
  if (m) {
    dokumentOeffnen(decodeURIComponent(m[1]), m[2] ? Number(m[2]) : null);
  } else {
    document.title = "Tabularium";
    $("#ansicht-dokument").hidden = true;
    $("#ansicht-liste").hidden = false;
    zustand.dok = null;
    statusLaden().then(() => {
      if (location.hash === "#/einstellungen" && !$("#dlg-einst").open) {
        zeichneEinstellungen();
        $("#dlg-einst").showModal();
      }
    });
  }
}

/* ---------- Ereignisse ---------- */

function einrichten() {
  $("#f-bearbeiter").value = localStorage.getItem("bearbeiter") || "";

  $("#btn-datei").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    const r = await api("/api/datei-waehlen", { methode: "POST", daten: {} });
    for (const p of r.pfade) {
      if (!zustand.auswahl.some((a) => a.pfad === p))
        zustand.auswahl.push({ art: "pfad", pfad: p, name: p.split("/").pop() });
    }
    if (r.abgelehnt.length) meldung("Übersprungen (kein Tabellenformat): " + r.abgelehnt.join(", "), true);
    zeichneAuswahl();
    if (zustand.auswahl.length) $("#f-notiz").focus();
  }));
  $("#btn-sichern").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, sichernAuswahl));
  $("#btn-verwerfen").addEventListener("click", () => { zustand.auswahl = []; zeichneAuswahl(); });
  $("#f-notiz").addEventListener("keydown", (ev) => { if (ev.key === "Enter") $("#btn-sichern").click(); });

  const ablage = $("#ablage");
  ["dragenter", "dragover"].forEach((t) => ablage.addEventListener(t, (ev) => {
    ev.preventDefault(); ablage.classList.add("aktiv");
  }));
  ["dragleave", "drop"].forEach((t) => ablage.addEventListener(t, () => ablage.classList.remove("aktiv")));
  ablage.addEventListener("drop", (ev) => { ev.preventDefault(); dateienAblegen([...ev.dataTransfer.files]); });
  // Dateien außerhalb der Ablage nicht im Browser öffnen
  window.addEventListener("dragover", (ev) => ev.preventDefault());
  window.addEventListener("drop", (ev) => {
    ev.preventDefault();
    if (!$("#ansicht-liste").hidden && ev.dataTransfer.files.length) dateienAblegen([...ev.dataTransfer.files]);
  });

  $("#dok-filter").addEventListener("input", zeichneDokumente);

  $("#btn-pruefen").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    await api("/api/pruefen", { methode: "POST", daten: {} });
    await statusLaden();
    window.scrollTo(0, 0);
  }));

  const dlg = $("#dlg-einst");
  dlg.addEventListener("close", () => {
    if (location.hash === "#/einstellungen") history.replaceState(null, "", "#/");
  });
  const einstOeffnen = async () => { await statusLaden(); zeichneEinstellungen(); dlg.showModal(); };
  $("#btn-einst").addEventListener("click", einstOeffnen);
  $("#archivpfad").addEventListener("click", einstOeffnen);
  $("#e-zs-speichern").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    await api("/api/einstellungen", { methode: "POST", daten: {
      zeitstempel: $("#e-zs").checked, tsa_url: $("#e-tsa").value } });
    meldung("Einstellungen gespeichert.");
    await statusLaden();
  }));
  $("#e-zs-nachholen").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    const r = await api("/api/zeitstempel", { methode: "POST", daten: {} });
    meldung(r.nachgeholt ? `${r.nachgeholt} Zeitstempel nachgeholt.` : "Alle Fassungen haben bereits einen Zeitstempel.");
    await statusLaden();
  }));
  $("#e-ordner-neu").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    const r = await api("/api/ordner-waehlen", { methode: "POST", daten: { titel: "Ordner zur Überwachung wählen" } });
    if (!r.pfad) return;
    await api("/api/ueberwachung", { methode: "POST", daten: {
      aktion: "hinzufuegen", pfad: r.pfad, rekursiv: $("#e-rekursiv").checked } });
    await statusLaden(); zeichneEinstellungen();
  }));
  $("#e-archiv-wechseln").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    const r = await api("/api/ordner-waehlen", { methode: "POST", daten: {
      titel: "Ordner für das Archiv wählen (vorhandenes Archiv oder neuer Ordner)" } });
    if (!r.pfad) return;
    await api("/api/archiv", { methode: "POST", daten: { pfad: r.pfad } });
    meldung("Archiv gewechselt.");
    await statusLaden(); zeichneEinstellungen();
  }));

  $("#d-von").addEventListener("change", () => vergleichLaden({ von: $("#d-von").value, bis: Number($("#d-bis").value) }));
  $("#d-bis").addEventListener("change", () => vergleichLaden({ von: $("#d-von").value, bis: Number($("#d-bis").value) }));
  $("#d-blatt").addEventListener("change", zeichneAenderungen);
  $("#d-suche").addEventListener("input", zeichneAenderungen);
  $("#d-aktuell").addEventListener("click", () => {
    document.querySelectorAll("#d-versionen button").forEach((b) => b.classList.remove("gewaehlt"));
    vergleichLaden({ aktuell: true });
  });
  $("#d-bericht").addEventListener("click", () => {
    window.open("/api/bericht?name=" + encodeURIComponent(zustand.dok.name) + "&token=" + encodeURIComponent(TOKEN), "_blank", "noopener");
  });
  $("#d-download").addEventListener("click", () => {
    const v = Number($("#d-bis").value);
    location.href = "/api/datei?name=" + encodeURIComponent(zustand.dok.name) + "&version=" + v + "&token=" + encodeURIComponent(TOKEN);
  });

  $("#e-autostart").addEventListener("change", (ev) => mitKnopf(ev.currentTarget, async () => {
    const r = await api("/api/autostart", { methode: "POST", daten: { aktiv: ev.currentTarget.checked } });
    ev.currentTarget.checked = !!r.aktiv;
    meldung(r.aktiv ? "Tabularium startet ab jetzt bei der Anmeldung." : "Autostart ausgeschaltet.");
  }));

  $("#btn-beenden").addEventListener("click", (ev) => mitKnopf(ev.currentTarget, async () => {
    await api("/api/beenden", { methode: "POST", daten: {} });
    clearInterval(zustand.takt);
    document.body.replaceChildren(h("main", { class: "beendet" },
      h("h1", { text: "Tabularium wurde beendet" }),
      h("p", { text: "Ihre Daten sind gesichert. Überwachte Ordner werden erst nach dem nächsten Start wieder gesichert." }),
      h("p", { class: "hinweis", text: "Zum Neustart Tabularium wieder öffnen. Dieses Fenster können Sie schließen." })));
  }));

  window.addEventListener("hashchange", route);
  if (location.hash.startsWith("#/dok/")) statusLaden();   // Kopfzeile auch in der Dokumentansicht
  // Übersicht aktuell halten (Ordnerüberwachung, geänderte Dateien)
  zustand.takt = setInterval(() => {
    if (document.visibilityState === "visible" && !$("#ansicht-liste").hidden && !$("#dlg-einst").open) statusLaden();
  }, 5000);
  route();
}

einrichten();
