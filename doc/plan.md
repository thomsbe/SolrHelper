# Plan für Slub SolrHelper

## Notes
- Das Tool dient Bibliothekaren & Entwicklern zum Betrachten und Editieren von Solr-Dokumenten.
- Es handelt sich um eine kleine Webanwendung auf Python-Basis.
- Webserver: Flask
- Projektverwaltung: 'uv', Veröffentlichung auf pypi, Start per 'uvx'.
- CLI-Parameter: click
- Logging: loguru
- Technische Details und Entscheidungen kommen in doc/technical.md (siehe globale Regeln).
- Für Tests wird ein Solr-Docker-Container verwendet.
- Solr-Docker-Container und Entwicklungsumgebung sind eingerichtet, Solr-Client wird vorbereitet
- Dokumentation für Anwender in README.md, technische Details in technical.md.
- Projekt ist bereits initialisiert, Abhängigkeiten sind installiert, neue Struktur mit src/solr_helper und CLI-Einstiegspunkt eingerichtet
- Das Build-System in pyproject.toml ist jetzt korrekt auf 'setuptools' eingestellt (nicht 'uv' oder 'hatchling').
- Für die Docker-Umgebung soll Solr 5.5.5 verwendet werden (altes Image prüfen).
- Solr-Client, Anbindung und Verbindungstest sind abgeschlossen. Docker-Umgebung läuft mit Solr 5.5.5.
- ACHTUNG: Solr 5.5.5 unterstützt kein /admin/ping. Die Verbindungsprüfung muss für alte Solr-Versionen angepasst werden.
- Solr 5.5.5 liefert auf /select standardmäßig XML zurück, nicht JSON! Die Verbindungsprüfung muss XML-Antworten auswerten und darf nicht response.json() verwenden.
- Zukünftig soll für die Solr-Anbindung `pysolr` statt `requests` verwendet werden (vereinfachte Handhabung, bessere Kompatibilität).
- Das Solr-Schema (Felder, Typen) soll abrufbar und auswertbar sein, damit die Feldstruktur dynamisch erkannt werden kann (z.B. für Editiermasken).
- Für das Testen und die Entwicklung sollen Beispiel-Felder (String, Number, Multivalue) im Schema vorhanden sein. Die Anpassung kann entweder per Schema-API (falls unterstützt) oder durch Einspielen einer angepassten schema.xml im Docker-Setup erfolgen.
- Das aktuelle Docker-Setup für die schema.xml führt zu Startproblemen (Berechtigungen/Kopierfehler). Troubleshooting und Anpassung des Docker-Starts notwendig.
- Achtung: Core wird offenbar nicht automatisch angelegt, und die Schema-API ist in Solr 5.5.5 nicht verfügbar (404-Fehler). Core-Management muss ggf. manuell oder über ein angepasstes Start-Skript erfolgen.
- Die aktuelle docker-compose-Strategie für die Core-Erstellung mit eigenem ConfigSet/Schemaverzeichnis funktioniert nicht zuverlässig (Fehler: configName nicht gefunden, Core bleibt im Status 'down'). Es ist ein robusteres Start-Skript oder ein manueller Workaround für die Core-Erstellung/ConfigSet-Zuweisung nötig.
- Solr läuft aktuell im SolrCloud-Modus, das ist aber nicht gewünscht! Ziel ist der Standalone-Modus (single core, kein ZooKeeper). Docker-Setup/Skript muss explizit den Standalone-Modus nutzen und darf nicht mit `-c` oder in Cloud-Variante gestartet werden.
- Fehler: Die Feldtypen IntPointField/LongPointField/... existieren in Solr 5.5.5 nicht! Die schema.xml muss auf klassische Typen (int, long, float, double) angepasst werden, sonst startet der Core nicht.
- Fehler: Der SynonymGraphFilterFactory existiert in Solr 5.5.5 nicht! Die schema.xml muss auf den klassischen SynonymFilter (SynonymFilterFactory) umgestellt werden, sonst startet der Core nicht.
- Erkenntnis: Die schema.xml wurde erfolgreich auf klassische Typen (int, long, float, double) und SynonymFilterFactory angepasst. Solr startet jetzt, der Core wird geladen. Nächster Schritt: Prüfung, ob die Beispiel-Felder wie gewünscht funktionieren und die Suche/Anzeige implementieren.

## Task List
- [x] Projektbeschreibung und Anforderungen lesen
- [x] Grundstruktur der Projektdateien anlegen (README.md, doc/technical.md, doc/plan.md)
- [x] Flask Webserver Grundgerüst erstellen
- [x] CLI-Interface mit click vorbereiten
- [x] Logging mit loguru integrieren
- [x] Solr-Docker-Container für lokale Entwicklung einrichten
- [x] README.md mit ersten Infos füllen
- [x] technical.md mit technischen Entscheidungen füllen
- [x] Solr-Client und Anbindung programmieren
- [x] Build-System in pyproject.toml auf 'hatchling' korrigieren
- [x] Docker-Image auf Solr 5.5.5 umstellen
- [x] Verbindungstest Solr-Client durchführen
- [ ] Verbindungstest für Solr 5.5.5 anpassen (kein /admin/ping, XML statt JSON verarbeiten)
- [ ] Suche und Anzeige von Solr-Dokumenten implementieren
- [x] Migration von requests auf pysolr für Solr-Client
- [ ] Solr-Schema (Felder & Typen) abrufen und auswerten
- [ ] Beispiel-Felder (String, Number, Multivalue) ins Schema einbauen (entweder per Schema-API oder durch Anpassen der schema.xml im Docker-Setup)
  - [ ] Docker-Compose/Start-Skript für eigenes Schema debuggen und lauffähig machen (Standalone-Modus sicherstellen, kein Cloud-Start)
  - [ ] Core-Erstellung und Core-Management für Solr 5.5.5 sicherstellen (ggf. manuell, via Skript oder nachträglicher Core-Upload, im Standalone-Modus per create_core)
  - [x] schema.xml für Solr 5.5.5-Kompatibilität anpassen (keine *PointField-Typen, nur klassische Typen, kein SynonymGraphFilter, sondern SynonymFilter)
  - [x] Anpassung auf SynonymFilter durchführen

## Current Goal
Solr-Dokumente suchen und anzeigen