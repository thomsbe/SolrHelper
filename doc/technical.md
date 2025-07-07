# Technische Dokumentation: Slub SolrHelper

Dieses Dokument enthält technische Details und Entscheidungen für das SolrHelper-Projekt.

## Abhängigkeiten und Tools

- **Paketmanagement:** `uv` wird für die Verwaltung der Python-Abhängigkeiten verwendet.
- **CLI:** `click` wird für die Erstellung der Kommandozeilenschnittstelle genutzt.
- **Logging:** `loguru` wird für das Logging verwendet.
- **Web Framework:** `Flask` dient als Grundlage für die Webanwendung.
- **Konfiguration:**
  - Die Solr-Verbindung kann über CLI-Parameter, Umgebungsvariablen oder eine `config.toml` (im Projekt oder `~/.solrhelper/`) gesteuert werden. Priorität: CLI > ENV > config.toml > Default.
  - Beispiel für `config.toml`:
    ```toml
    solr_url = "http://localhost:8983"
    core = "testing"
    ```
- **Schema-Ausgabe:**
  - `solr-helper show-schema --format json` zeigt das Schema als JSON
  - `solr-helper show-schema --format table` zeigt eine tabellarische Übersicht

## Entwicklungsumgebung

- **Solr:** Für lokale Tests wird eine Solr-Instanz empfohlen, kann aber auch extern angebunden werden.

## Web-Interface und Frontend

- **Templating:** Die Web-Oberfläche wird mit Flask und Jinja2-Templates gerendert.
- **HTMX:** Für eine moderne und reaktionsschnelle Benutzererfahrung wird [HTMX](https://htmx.org/) eingesetzt. Dies ermöglicht dynamische Interaktionen ohne komplexe JavaScript-Frameworks:
  - Das Bearbeitungsformular (`_edit_form.html`) wird per HTMX-Request in ein modales Fenster geladen.
  - Nach dem Absenden des Formulars wird nur die betroffene Tabellenzeile (`_record_row.html`) neu gerendert und ausgetauscht (`hx-swap="outerHTML"`).
  - Fehler oder Erfolgsmeldungen werden so direkt und ohne Neuladen der gesamten Seite angezeigt.
  - HTMX wird einfach über ein CDN im Haupt-Template (`record.html`) eingebunden.

## Details zur Solr-Integration

### Dynamische Update-Strategie

Eine der Kernkomponenten ist die Fähigkeit, sich an unterschiedliche Solr-Konfigurationen anzupassen. Dies wird durch die Methode `check_update_log_status` im `SolrClient` erreicht.

1.  **Erkennung:** Die Methode fragt die `/config`-API des Solr-Cores ab.
2.  **Prüfung:** Sie prüft, ob die Konfiguration einen Hinweis auf ein aktiviertes `<updateLog/>` enthält. Dies ist die Voraussetzung für atomare Updates.
3.  **Kompatibilität:** Es wurde eine spezielle Logik implementiert, um auch ältere Solr-Versionen (wie 5.5.5) zu unterstützen. Diese melden die Konfiguration mit einem flachen, zusammengesetzten Schlüssel (`updateHandlerupdateLog`) anstatt einer modernen, verschachtelten JSON-Struktur. Die Prüfroutine beherrscht beide Varianten.

Basierend auf dem Ergebnis wählt die `update_document_field`-Methode eine von zwei Strategien:

- **Atomares Update (`_update_atomic`):** Die bevorzugte, sichere und performante Methode. Sendet einen Befehl an Solr, nur das spezifische Feld zu ändern (`{'set': ...}`).
- **Full Document Re-Index (`_update_full_document`):** Die Fallback-Methode. Liest das gesamte Dokument, ändert den Feldwert im Python-Code, entfernt alle Felder, die als Ziel eines `copyField` definiert sind (um Solr-Fehler zu vermeiden), und sendet das komplette, modifizierte Dokument zur Neu-Indizierung an Solr.
