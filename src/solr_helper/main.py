# Importiert die notwendigen Bibliotheken
import click  # Für die Erstellung von Kommandozeilen-Interfaces
from flask import Flask  # Das Web-Framework für unsere Anwendung
import json  # Für die Formatierung der JSON-Ausgabe
from loguru import logger  # Für einfaches und effektives Logging

# Importiert unseren neuen SolrClient
from .solr_client import SolrClient


# Erstellt die Flask-Anwendung
# Dies ist das Herzstück unserer Web-App.
app = Flask(__name__)


# Definiert eine einfache Route für die Startseite
# Eine Route verbindet eine URL mit einer Python-Funktion.
@app.route('/')
def home():
    """Zeigt die Startseite an."""
    logger.info("Startseite wurde aufgerufen.")  # Loggt, wenn jemand die Seite besucht
    return "<h1>Hallo vom SolrHelper!</h1>"  # Gibt den HTML-Inhalt für die Seite zurück


# Definiert die Haupt-Kommandozeilengruppe mit click
# 'cli' wird der Einstiegspunkt für alle unsere Befehle sein.
@click.group()
def cli():
    """Ein Helfer-Tool für die Interaktion mit Solr."""
    # Konfiguriert das Logging
    # Wir entfernen den Standard-Handler und fügen einen neuen hinzu,
    # der die Logs farbig und mit Zeitstempel ausgibt.
    logger.remove()
    logger.add(lambda msg: click.echo(msg, err=True), colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.info("SolrHelper wird gestartet...")


# Fügt einen Befehl zur 'cli'-Gruppe hinzu, um den Webserver zu starten
@cli.command()
@click.option('--host', default='127.0.0.1', help='Der Host, auf dem der Server laufen soll.')
@click.option('--port', default=5000, help='Der Port, auf dem der Server lauschen soll.')
@click.option('--debug', is_flag=True, help='Aktiviert den Debug-Modus.')
def run(host, port, debug):
    """Startet den Flask-Entwicklungsserver."""
    logger.info(f"Starte den Server auf http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


# Dieser Block wird nur ausgeführt, wenn das Skript direkt gestartet wird
# Fügt einen Befehl hinzu, um die Verbindung zu Solr zu testen
@cli.command(name="test-connection")
def test_connection():
    """Überprüft die Verbindung zum Solr-Server."""
    logger.info("Führe Solr-Verbindungstest durch...")
    # Erstellt eine Instanz unseres Solr-Clients
    client = SolrClient()
    # Ruft die Methode zur Überprüfung der Verbindung auf
    if client.check_connection():
        click.secho("\nVerbindungstest erfolgreich! Der Solr-Core ist erreichbar.", fg="green")
    else:
        click.secho("\nVerbindungstest fehlgeschlagen. Überprüfe, ob der Docker-Container läuft.", fg="red")


# Fügt einen neuen Befehl 'show-schema' hinzu, um das Solr-Schema anzuzeigen
@cli.command()
@click.option('--format', type=click.Choice(['json', 'table'], case_sensitive=False), 
              default='table', help='Ausgabeformat (json oder table)')
def show_schema(format):
    """Zeigt das Schema des aktuellen Solr-Cores an."""
    try:
        client = SolrClient()
        schema = client.get_schema()
        
        if format == 'json':
            # Ausgabe als formatiertes JSON
            print(json.dumps(schema, indent=2, ensure_ascii=False))
        else:
            # Tabellarische Ausgabe
            print(f"\nSchema für Core: {schema['core']}")
            print("-" * 80)
            print("Felder:")
            print("-" * 80)
            print(f"{'Name':<30} | {'Typ':<20} | {'Indiziert':<8} | {'Gespeichert':<10} | {'Mehrfach'} | {'Erforderlich'}")
            print("-" * 85)
            
            for field in schema['fields']:
                print(f"{field['name']:<30} | {field['type']:<20} | "
                      f"{'Ja' if field['indexed'] else 'Nein':<8} | "
                      f"{'Ja' if field['stored'] else 'Nein':<10} | "
                      f"{'Ja' if field['multi_valued'] else 'Nein':<6} | "
                      f"{'Ja' if field['required'] else 'Nein'}")
            
            print("\nFeldtypen:")
            print("-" * 80)
            for name, ftype in schema['field_types'].items():
                print(f"- {name}: {ftype['class']} (Analyzer: {ftype.get('analyzer', 'Keiner')})")
            
            print(f"\nPrimärschlüssel: {schema.get('unique_key', 'id')}")
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Schemas: {e}")
        raise click.ClickException("Konnte das Schema nicht abrufen. Bitte überprüfen Sie die Verbindungseinstellungen.")


# Dieser Block wird nur ausgeführt, wenn das Skript direkt gestartet wird
if __name__ == '__main__':
    cli()  # Startet die click-Kommandozeilenschnittstelle
