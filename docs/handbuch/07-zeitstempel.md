# 7 — Zeitstempel

Die Kette aus Fingerabdrücken zeigt jede Veränderung, solange niemand das ganze
Archiv neu berechnet. Mit vollem Zugriff auf den Rechner wäre das möglich: alte
Fassungen ersetzen, alle Fingerabdrücke neu berechnen, fertig. Davor schützt
der **externe Zeitstempel**.

## Was ein Zeitstempel ist

Eine **Zeitstempelstelle** (englisch *Time Stamping Authority*, TSA) ist ein
unabhängiger Dienst. Tabularium schickt ihr den Fingerabdruck eines
Journaleintrags. Die Stelle antwortet mit einer digital unterschriebenen
Bestätigung: *„Dieser Fingerabdruck lag mir am 25.11.2026 um 21:32:50 vor.“* Das
Verfahren ist international genormt (RFC 3161).

Weil jeder Journaleintrag den Fingerabdruck seines Vorgängers enthält, belegt
ein Zeitstempel nicht nur die eine Fassung, sondern die **ganze Kette bis
dahin**. Wer später etwas ändert, kann zwar neue Fingerabdrücke berechnen, aber
keine passenden Unterschriften der Zeitstempelstelle erzeugen.

## Datenschutz

An die Zeitstempelstelle geht **nur der Fingerabdruck**, 64 Zeichen wie
`0bb0ee044be246ea…`. Aus ihm lässt sich weder der Inhalt der Tabelle noch ihr
Name noch irgendetwas sonst ablesen. Mandantendaten verlassen den Rechner
also nicht.

## Einschalten

1. **Einstellungen** öffnen.
2. **Jede Fassung mit externem Zeitstempel (RFC 3161) absichern** ankreuzen.
3. **Speichern** klicken.

Ab jetzt holt Tabularium bei jedem Sichern einen Zeitstempel. Das dauert etwa
eine Sekunde und braucht eine Internetverbindung. In der Versionsliste
erscheint unter der Fassung ⏱ mit dem bestätigten Zeitpunkt.

**Ohne Internet** sichert Tabularium die Fassung trotzdem und meldet
*„Zeitstempel fehlgeschlagen“*. Holen Sie ihn später über **Einstellungen →
Fehlende Zeitstempel nachholen** nach. Ein nachgeholter Stempel belegt
allerdings nur den Zeitpunkt des Nachholens, nicht den der Sicherung.

## Welche Zeitstempelstelle?

| Anbieter | Kosten | Beweiswert |
| --- | --- | --- |
| **FreeTSA** (voreingestellt, `https://freetsa.org/tsr`) | kostenlos | technisch einwandfrei, aber **kein** qualifizierter Vertrauensdienst. Für interne Nachvollziehbarkeit gut geeignet. |
| **Qualifizierter Vertrauensdiensteanbieter nach eIDAS**, z. B. D-Trust (Bundesdruckerei). Alle Anbieter stehen in der [EU-Vertrauensliste](https://eidas.ec.europa.eu/efda/tl-browser/) | je nach Vertrag | Für einen **qualifizierten elektronischen Zeitstempel** gilt nach Art. 41 Abs. 2 eIDAS-Verordnung EU-weit die Vermutung, dass Datum und Uhrzeit richtig sind und die Daten seitdem unverändert. |

Wollen Sie Zeitstempel als Beweismittel einsetzen, etwa im Prozess oder
gegenüber Behörden, nehmen Sie einen qualifizierten Anbieter. Viele verlangen
einen Vertrag und Zugangsdaten. Das Einrichten übernimmt in der Regel die IT:

```bash
./tabularium einstellungen \
  --tsa-url https://zeitstempel.anbieter.example/tsa \
  --tsa-ca /pfad/zur/ca-kette.pem \
  --tsa-zertifikat /pfad/zum/tsa-zertifikat.pem
```

Die Adresse lässt sich auch in den Einstellungen der Oberfläche ändern. Die
Zertifikate (Wurzel- und TSA-Zertifikat im PEM-Format) erhalten Sie vom
Anbieter. Für FreeTSA lädt Tabularium sie beim ersten Zeitstempel selbst
herunter und legt sie im Archiv unter `tsa/` ab.

> **Hinweis:** Anbieter mit Anmeldung per Benutzername und Kennwort oder
> Client-Zertifikat werden derzeit nicht direkt unterstützt. Fragen Sie den
> Anbieter nach einem Zugang ohne Anmeldung, etwa per IP-Freigabe.

## Prüfen

Bei **Archiv prüfen** kontrolliert Tabularium jeden Zeitstempel:

- Ist die Unterschrift der Zeitstempelstelle gültig?
- Gehört der Stempel genau zu diesem Journaleintrag?

Ein Stempel, der zu einem anderen Eintrag gehört oder beschädigt ist, ergibt
eine rote Meldung. Wie man Zeitstempel ganz ohne Tabularium prüft, steht in
[Kapitel 11](11-unabhaengig-pruefen.md).

---

← [6 — Prüfen und Prüfbericht](06-pruefen-und-pruefbericht.md) | [Inhalt](README.md) | [8 — Frühere Fassungen zurückholen](08-wiederherstellen.md) →
