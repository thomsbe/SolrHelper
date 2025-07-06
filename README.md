# Slub SolrHelper

Willkommen beim Slub SolrHelper!

Dieses Tool hilft Bibliothekaren und Softwareentwicklern dabei, Dokumente in einem Solr-Index einfach anzusehen und zu bearbeiten.

Es handelt sich um eine kleine Webanwendung, die lokal gestartet werden kann.

## Features

- Verbindung zu einem beliebigen Solr-Core
- Suche nach Dokumenten
- Anzeige von Dokumenten
- Bearbeiten von Dokumenten

## Entwicklung

Um die Anwendung lokal zu entwickeln, benötigst du Docker und Docker Compose.

1.  **Starte die Solr-Instanz:**
    ```bash
    docker-compose up -d
    ```
2.  **Installiere die Projektabhängigkeiten im editierbaren Modus:**
    ```bash
    uv pip install -e .
    ```
3.  **Starte die Webanwendung:**
    ```bash
    solr-helper run
    ```
