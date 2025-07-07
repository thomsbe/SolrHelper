# Plan für Slub SolrHelper

## Ziel
- Das Tool dient Bibliothekaren & Entwicklern zum Betrachten und Editieren von Solr-Dokumenten.
- Die Verbindung zu Solr ist flexibel über CLI, ENV oder config.toml konfigurierbar.

## Abgeschlossene Aufgaben (v1.0)
- [x] **Grundlagen:**
    - [x] Projektstruktur, CLI-Interface (click), Logging (loguru), Webserver (Flask) aufgesetzt.
    - [x] Docker-Setup für Solr 5.5.5 zur lokalen Entwicklung.
    - [x] Flexible Konfiguration für Solr-Verbindung (CLI, ENV, config.toml).
    - [x] Solr-Client zur Kommunikation mit dem Index implementiert.
- [x] **Web-Interface:**
    - [x] Suche und Anzeige von Solr-Dokumenten implementiert.
    - [x] Detailansicht für einzelne Dokumente mit allen Feldern.
    - [x] Solr-Schema wird ausgelesen und zur Darstellung der Felder genutzt.
- [x] **Bearbeitungsfunktion:**
    - [x] Feld-basiertes Editieren von Dokumenten über ein modales Formular.
    - [x] UI/UX mit HTMX für dynamische Formulare und Updates ohne Neuladen der Seite.
    - [x] Dynamische Update-Strategie: Automatische Erkennung, ob atomare Updates (`<updateLog/>`) vom Solr-Server unterstützt werden.
    - [x] Fallback-Strategie (Full Document Re-Index) für ältere oder anders konfigurierte Solr-Instanzen.
    - [x] Transparente Warnung an den Benutzer, wenn der Fallback-Modus aktiv ist.
    - [x] Robuste Fehlerbehandlung: Solr-Fehler werden abgefangen und direkt im UI angezeigt.

## Aktuelles Ziel
- [x] Dokumentation für v1.0 fertigstellen und für PyPI vorbereiten.
