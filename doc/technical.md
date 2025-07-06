# Technische Dokumentation: Slub SolrHelper

Dieses Dokument enthält technische Details und Entscheidungen für das SolrHelper-Projekt.

## Abhängigkeiten und Tools

- **Paketmanagement:** `uv` wird für die Verwaltung der Python-Abhängigkeiten verwendet.
- **CLI:** `click` wird für die Erstellung der Kommandozeilenschnittstelle genutzt.
- **Logging:** `loguru` wird für das Logging verwendet.
- **Web Framework:** `Flask` dient als Grundlage für die Webanwendung.

## Entwicklungsumgebung

- **Solr:** Für lokale Tests wird eine Solr-Instanz über einen Docker-Container bereitgestellt. Eine `docker-compose.yml` wird im Hauptverzeichnis des Projekts erstellt, um den Start zu vereinfachen.
