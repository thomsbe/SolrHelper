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

## Refactoring 2025-07-08: Modulare Architektur

### Motivation

Die ursprüngliche `app.py` war mit 826 Zeilen viel zu groß und unübersichtlich. Dies führte zu:
- Schwieriger Wartbarkeit
- Schlechter LLM-Kompatibilität (LLMs haben Probleme mit großen Dateien)
- Vermischung von Verantwortlichkeiten
- Doppelte Route-Definitionen

### Lösung: Blueprint-basierte Architektur

**Neue Struktur (alle Dateien < 300 Zeilen):**
```
src/solr_helper/web/
├── app.py                 # App-Factory (84 Zeilen)
├── routes/
│   ├── connection.py      # Verbindungsmanagement (90 Zeilen)
│   ├── search.py          # Such-Funktionalität (89 Zeilen)
│   ├── record.py          # Dokumentenbearbeitung (180 Zeilen)
│   └── api.py             # HTMX-API-Endpoints (105 Zeilen)
├── utils/
│   ├── auth.py            # Authentifizierung/Autorisierung (32 Zeilen)
│   └── helpers.py         # Helper-Funktionen (85 Zeilen)
└── templates/             # Unverändert
```

### Kritische Erkenntnisse für Entwickler

#### 1. **DocValues-Duplikate bei Full-Updates**

**Problem**: `DocValuesField "title_fullStr" appears more than once in this document`
**Ursache**: Copy-Fields werden bei Full-Document-Updates dupliziert
**Lösung**: Copy-Fields vor Update identifizieren und entfernen

```python
# Copy-Fields identifizieren und entfernen
copy_field_targets = {cf['dest'] for cf in copy_fields if cf['source'] == field_name}
for target in copy_field_targets:
    if target in doc:
        del doc[target]
        logger.debug(f"Copy-Field-Ziel '{target}' entfernt")
```

#### 2. **HTMX Modal-Schließung nach Updates**

**Problem**: Modal schließt nicht nach erfolgreichem Speichern
**Ursache**: HTMX-Events werden nicht korrekt abgefangen
**Lösung**: Mehrere Event-Handler für verschiedene Szenarien

```javascript
// Primärer Handler: afterRequest
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (isModalContent && isSuccessful && isPostRequest) {
        closeModal();
    }
});

// Fallback: afterSwap für Tabellenzeilen-Updates
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id && event.detail.target.id.startsWith('row-')) {
        closeModal();
    }
});
```

#### 3. **Blueprint URL-Namespacing**

**Problem**: `url_for('edit_form')` funktioniert nicht nach Blueprint-Refactoring
**Ursache**: Routes sind jetzt in Blueprints organisiert
**Lösung**: Blueprint-Präfix in Templates verwenden

```html
<!-- Vorher (fehlerhaft): -->
{{ url_for('edit_form', doc_id=doc_id, field_name=field_name) }}

<!-- Nachher (korrekt): -->
{{ url_for('record.edit_form', doc_id=doc_id, field_name=field_name) }}
```

#### 4. **Template-Route-Parameter-Mismatch**

**Problem**: "Feld hinzufügen" funktioniert nicht
**Ursache**: Template sendet `new_field_name`, Route erwartet `field_name`
**Lösung**: Konsistente Parameternamen verwenden

```html
<!-- Vorher (fehlerhaft): -->
<input name="new_field_name" ...>
<input name="new_field_value" ...>

<!-- Nachher (korrekt): -->
<input name="field_name" ...>
<input name="field_value" ...>
```

### Dynamisches Verbindungsmanagement

#### Innovation: Verbindungswechsel zur Laufzeit

**Traditionell**: App-Neustart für neue Verbindung erforderlich
**SolrHelper**: Dynamischer Wechsel ohne Neustart

**Implementierung**:
```python
# Verbindungswechsel zur Laufzeit
current_app.config['CURRENT_CONNECTION'] = new_connection
current_app.config['CURRENT_CLIENT'] = new_client
current_app.config['CURRENT_SCHEMA'] = new_schema
```

**Browser-Integration**:
- localStorage für Verbindungsspeicher
- Alpine.js für reaktive UI
- Import/Export-Funktionalität

### Debug-Modus-Implementierung

**CLI-Integration**:
```bash
# Debug-Modus
solr-helper --debug start-web

# Produktions-Modus
solr-helper start-web
```

**Logging-Konfiguration**:
```python
def create_app(debug=False):
    logger.remove()
    log_level = "DEBUG" if debug else "INFO"
    log_format = ("{time} | {level} | {name}:{function}:{line} - {message}"
                 if debug else "{time} | {level} | {message}")
    logger.add(sys.stderr, level=log_level, format=log_format)
```

### Performance-Optimierungen

1. **Lazy Schema Loading**: Schema nur bei Bedarf laden
2. **Client-seitige Feldfilterung**: Alpine.js für Suggest-Funktionalität
3. **HTMX für partielle Updates**: Reduzierte Seitenlasten
4. **Effiziente Feldauflösung**: Dreistufige Fallback-Strategie

### Sicherheitsaspekte

1. **Input-Validierung**: Feldnamen und -werte werden validiert
2. **XSS-Schutz**: Jinja2-Escaping für alle Ausgaben
3. **Datenverlust-Prävention**: Warnsystem für Full-Updates
4. **Verbindungssicherheit**: Tests vor Verwendung
