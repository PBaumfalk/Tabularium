# 13 — Grenzen und rechtliche Einordnung

Dieses Kapitel sagt offen, was Tabularium leistet und was nicht. Es ist keine
Rechts- oder Steuerberatung.

## Was Tabularium technisch leistet

- **Unveränderbarkeit nachweisen:** Jede nachträgliche Änderung, Löschung oder
  Einfügung im Archiv wird bei der Prüfung erkannt.
- **Vollständigkeit des Verlaufs:** Jede gesicherte Fassung bleibt erhalten.
  Nichts wird überschrieben.
- **Nachvollziehbarkeit:** Zu jeder Fassung gibt es Zeitpunkt, Person, Notiz und
  die genauen Zelländerungen.
- **Zeitpunkt beweisen:** Mit externem Zeitstempel ist belegt, dass eine
  Fassung spätestens zu diesem Zeitpunkt existierte.
- **Unabhängige Prüfbarkeit:** offenes Format, prüfbar mit Standardwerkzeugen
  ([Kapitel 11](11-unabhaengig-pruefen.md)).

## Grenzen

| Grenze | Was das heißt | Abhilfe |
| --- | --- | --- |
| **Nur was gesichert wird, ist geschützt** | Änderungen zwischen zwei Sicherungen sind nicht einzeln erfasst. | Ordnerüberwachung ([Kapitel 5](05-ordner-ueberwachen.md)), feste Regeln, wann gesichert wird |
| **Wer geändert hat** | Erfasst werden Benutzerkonto, Rechnername und die freie Angabe „Bearbeitet von“. Teilen sich mehrere Personen ein Konto, ist die Person nicht eindeutig. | Eigene Benutzerkonten je Person |
| **Uhrzeit des Rechners** | Das Feld „gesichert am“ stammt von der Uhr des Rechners, und die lässt sich verstellen. | Zeitstempel einschalten. Verlässlich ist die Zeit der Zeitstempelstelle. |
| **Löschen des ganzen Archivs** | Wer Vollzugriff hat, kann das Archiv samt Sicherungen löschen. Tabularium erkennt Veränderungen, verhindert aber kein Löschen. | Kopie auf WORM-Speicher ([Kapitel 10](10-archiv-und-sicherung.md)) |
| **Entfernen der letzten Einträge** | Ohne Mac-Dateisperre fällt das Kürzen am Ende der Kette nur auf, wenn man den früheren Kopf-Hash kennt. | Kopf-Hash festhalten (Prüfbericht), Archiv auf APFS-Laufwerk |
| **Was verglichen wird** | Werte und Formeln. Nicht verglichen werden Formatierung, Kommentare, Datenüberprüfung, Diagramme, Pivot-Tabellen, Makros. Diese Teile sind aber in der gesicherten Originaldatei enthalten. | Originaldatei herunterladen und vergleichen |
| **Eingefügte Zeilen** | Der Vergleich arbeitet nach Zelladresse. Eine eingefügte Zeile erscheint als Änderung aller darunter liegenden Zellen. | Suchfeld nutzen ([Kapitel 4](04-verlauf-und-vergleich.md)) |
| **Verschlüsselte Dateien** | werden gesichert, aber nicht ausgelesen | Kennwortschutz zum Öffnen vermeiden, Zugriffsschutz über Ordnerrechte |
| **FreeTSA** | technisch einwandfrei, aber kein qualifizierter Vertrauensdienst | qualifizierten Anbieter wählen ([Kapitel 7](07-zeitstempel.md)) |
| **Betriebssysteme** | macOS mit Dateisperren. Windows ohne Dateisperren (nur Schreibschutz-Attribut). Unter Windows prüft Tabularium die Signatur der Zeitstempel nur, wenn OpenSSL installiert ist. Linux aus dem Quelltext | Zeitstempel vollständig auf einem Mac oder mit OpenSSL prüfen ([Kapitel 11](11-unabhaengig-pruefen.md)) |
| **Mehrere gleichzeitig angemeldete Benutzer** | Die Oberfläche ist nur auf diesem Rechner erreichbar, dort aber für jedes angemeldete Benutzerkonto, das die Adresse kennt. Auf Terminalservern oder bei schneller Benutzerumschaltung können andere Benutzer eine laufende Sitzung erreichen. | Tabularium auf Einzelplatzrechnern betreiben oder beenden, wenn andere angemeldet sind |

## Rechtliche Einordnung

### „Revisionssicher“

Der Begriff ist nicht gesetzlich definiert. Üblicherweise meint er eine
Ablage, die **vollständig, unveränderbar, nachvollziehbar, wiederauffindbar und
fristgerecht** ist. Tabularium deckt die technischen Anforderungen
Unveränderbarkeit, Nachvollziehbarkeit und Wiederauffindbarkeit ab. Wie lange
aufbewahrt wird, wer zugreifen darf und dass tatsächlich gesichert wird, regeln
Sie organisatorisch.

### Steuerlich relevante Unterlagen (AO, GoBD)

Nach § 146 Abs. 4 AO darf eine Aufzeichnung nicht so verändert werden, dass
der ursprüngliche Inhalt nicht mehr feststellbar ist. Die **GoBD** (BMF-Schreiben
zu den Grundsätzen ordnungsmäßiger Buchführung in elektronischer Form) verlangen
außerdem unter anderem:

- **Unveränderbarkeit** und Protokollierung von Änderungen. Tabularium leistet
  das für die gesicherten Fassungen.
- eine **Verfahrensdokumentation**: Wer sichert wann was, wo liegt das Archiv,
  wie wird geprüft und gesichert. Diese Beschreibung schreiben Sie selbst. Die
  Kapitel 3 bis 10 dieses Handbuchs liefern dafür Bausteine.
- **Datenzugriff** für die Finanzverwaltung. Die Originaldateien lassen sich
  jederzeit herausgeben ([Kapitel 8](08-wiederherstellen.md)).
- **Aufbewahrung** über die gesetzlichen Fristen (§ 147 AO, § 257 HGB).

Tabelle als Hauptbuch? Die GoBD sehen Tabellenkalkulationen kritisch, wenn sie
Bücher ersetzen. Tabularium macht aus Excel keine Buchhaltungssoftware. Es
sichert Tabellen, die neben der Buchhaltung geführt werden (Nebenrechnungen,
Übersichten, Kalkulationen), nachvollziehbar ab. Ob das im Einzelfall genügt,
klären Sie mit Ihrer Steuerberatung.

### Beweiswert im Zivilprozess

Elektronische Dokumente unterliegen der **freien Beweiswürdigung** des Gerichts
(§ 286 ZPO, Augenscheinsbeweis nach § 371 ZPO). Fingerabdrücke, eine lückenlose
Kette und Zeitstempel erleichtern es, die Echtheit und den Zeitpunkt einer
Fassung darzulegen und durch Sachverständige prüfen zu lassen
([Kapitel 11](11-unabhaengig-pruefen.md)).

Für **qualifizierte elektronische Zeitstempel** gilt EU-weit die Vermutung,
dass Datum und Uhrzeit richtig sind und die Daten seitdem unverändert
(Art. 41 Abs. 2 eIDAS-Verordnung). Ein Zeitstempel von FreeTSA hat diese
Vermutung nicht, bleibt aber ein starkes Indiz.

Tabularium belegt, dass eine Fassung **so vorlag**, nicht dass ihr Inhalt
**richtig** ist.

### Kanzleien

Für Handakten gilt eine Aufbewahrungsfrist von sechs Jahren (§ 50 Abs. 1 BRAO).
Tabularium arbeitet vollständig lokal. Mandantendaten gehen an keinen Dritten,
auch nicht an die Zeitstempelstelle, denn die erhält nur einen Fingerabdruck.
Das erleichtert die Wahrung der Verschwiegenheit (§ 43a Abs. 2 BRAO, § 203
StGB). Liegt das Archiv auf einem NAS oder in einer Datensicherung bei einem
Dienstleister, gelten dafür die üblichen Anforderungen (§ 43e BRAO).

### Datenschutz

Tabularium verarbeitet personenbezogene Daten nur, soweit sie in Ihren Tabellen
stehen, sowie Benutzerkonto und Namen der Bearbeitenden im Journal. Weil
Fassungen bewusst nicht gelöscht werden können, bedenken Sie das bei
Löschpflichten nach Art. 17 DSGVO: Nach Ablauf der Aufbewahrungsfrist
löschen Sie das **ganze Archiv** ([Kapitel 10](10-archiv-und-sicherung.md#archiv-löschen)).
Planen Sie Archive deshalb nach Zweck und Frist getrennt, etwa ein Archiv je
Geschäftsjahr.

---

← [12 — Technik](12-technik.md) | [Inhalt](README.md) | [14 — Häufige Fragen](14-haeufige-fragen.md) →
