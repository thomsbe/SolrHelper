# Importiert die notwendigen Bibliotheken
import click  # Für die Erstellung von Kommandozeilen-Interfaces
from flask import Flask  # Das Web-Framework für unsere Anwendung
import json  # Für die Formatierung der JSON-Ausgabe
from loguru import logger  # Für einfaches und effektives Logging

# Importiert unseren neuen SolrClient und die zentrale Konfigurationsfunktion
from .solr_client import SolrClient
from .web.app import create_app, create_app_for_connection_management
from .config import load_solr_config

import functools

def pass_solr_config(f):
    @click.pass_context
    @functools.wraps(f)
    def new_func(ctx, *args, **kwargs):
        solr_url, core = load_solr_config(ctx.obj.get('solr_url'), ctx.obj.get('core'))
        return f(solr_url, core, *args, **kwargs)
    return new_func

# Erstellt die Flask-Anwendung
app = Flask(__name__)

@app.route('/')
def home():
    """Zeigt die Startseite an."""
    logger.info("Startseite wurde aufgerufen.")
    return "<h1>Hallo vom SolrHelper!</h1>"

# Globale Optionen für alle Kommandos (werden an alle weitergereicht)
@click.group()
@click.option('--solr-url', default=None, help='Basis-URL des Solr-Servers, z.B. http://localhost:8983')
@click.option('--core', default=None, help='Name des Solr-Cores, z.B. testing')
@click.pass_context
def cli(ctx, solr_url, core):
    """Ein Helfer-Tool für die Interaktion mit Solr."""
    logger.remove()
    logger.add(lambda msg: click.echo(msg, err=True), colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.info("SolrHelper wird gestartet...")
    # Speichere die Konfigurationsparameter im Context-Objekt
    ctx.ensure_object(dict)
    ctx.obj['solr_url'] = solr_url
    ctx.obj['core'] = core

@cli.command()
@click.option('--host', default='127.0.0.1', help='Der Host, auf dem der Server laufen soll.')
@click.option('--port', default=5000, help='Der Port, auf dem der Server lauschen soll.')
@click.option('--debug', is_flag=True, help='Aktiviert den Debug-Modus.')
@click.pass_context
def run(ctx, host, port, debug):
    """Startet den Flask-Entwicklungsserver."""
    logger.info(f"Starte den Server auf http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

@cli.command(name="test-connection")
@pass_solr_config
def test_connection(solr_url, core):
    """Prüft die Verbindung zum Solr-Core."""
    try:
        client = SolrClient(solr_url=solr_url, core=core)
        if client.check_connection():
            logger.success(f"Verbindung zu Solr-Core '{core}' unter '{solr_url}' erfolgreich.")
        else:
            logger.error("Verbindung fehlgeschlagen.")
            raise click.ClickException("Verbindung konnte nicht hergestellt werden.")
    except Exception as e:
        logger.error(f"Fehler beim Verbindungs-Test: {e}")
        raise click.ClickException("Ein unerwarteter Fehler ist aufgetreten.")

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host für den Webserver.')
@click.option('--port', default=5000, help='Port für den Webserver.')
@click.option('--no-connection-check', is_flag=True, help='Startet ohne Verbindungstest (für Connection Management).')
@click.option('--debug', '-d', is_flag=True, help='Startet im Debug-Modus (Flask Debug + DEBUG Logging).')
@pass_solr_config
def start_web(solr_url, core, host, port, no_connection_check, debug):
    """Startet den Flask-Webserver für die UI."""

    # Prüfe ob Solr-Parameter über CLI gegeben wurden
    ctx = click.get_current_context()
    solr_params_from_cli = any(param in ctx.params for param in ['solr_url', 'core'])

    if not solr_params_from_cli and not no_connection_check:
        # Keine CLI-Parameter -> Connection Management Mode
        logger.info("Keine Solr-Parameter angegeben. Starte im Connection Management Modus.")
        logger.info("Verwende --no-connection-check um ohne Verbindungstest zu starten.")

        # Erstelle App ohne Schema für Connection Management
        app = create_app_for_connection_management(debug=debug)
        logger.info(f"Starte Webserver auf http://{host}:{port}")
        logger.info("Gehe zu /connections um Verbindungen zu verwalten.")
        if debug:
            logger.debug("Debug-Modus aktiviert")
        app.run(host=host, port=port, debug=debug)
        return

    if no_connection_check:
        # Starte ohne Verbindungstest (für Connection Management)
        logger.info("Starte ohne Verbindungstest...")
        app = create_app_for_connection_management(debug=debug)
        logger.info(f"Starte Webserver auf http://{host}:{port}")
        if debug:
            logger.debug("Debug-Modus aktiviert")
        app.run(host=host, port=port, debug=debug)
        return

    # Normale Startup-Logik mit Verbindungstest
    try:
        logger.info("Rufe aktuelles Schema vom Solr-Server ab...")
        client = SolrClient(solr_url=solr_url, core=core)
        schema = client.get_schema()
        logger.success("Schema erfolgreich vom Solr-Server abgerufen.")
    except Exception as e:
        logger.error(f"Konnte Schema nicht abrufen: {e}")
        raise click.ClickException("Der Webserver konnte nicht gestartet werden, da das Schema nicht abrufbar war.")

    app = create_app(solr_url=solr_url, core=core, schema=schema, debug=debug)
    logger.info(f"Starte Webserver auf http://{host}:{port}")
    if debug:
        logger.debug("Debug-Modus aktiviert")
    app.run(host=host, port=port, debug=debug)

@cli.command()
@click.option('--format', type=click.Choice(['json', 'table'], case_sensitive=False), 
              default='table', help='Ausgabeformat (json oder table)')
@pass_solr_config
def show_schema(solr_url, core, format):
    """Zeigt das Schema des aktuellen Solr-Cores an."""
    try:
        client = SolrClient(solr_url=solr_url, core=core)
        schema = client.get_schema()
        if format == 'json':
            print(json.dumps(schema, indent=2, ensure_ascii=False))
        else:
            print(f"\nSchema für Core: {schema.get('core', '-')}")
            print("-" * 80)
            print("Felder:")
            print("-" * 80)
            fields = schema.get('fields', [])
            field_names = set()
            for field in fields:
                field_names.update(field.keys())
            field_names = sorted(list(field_names))
            print(f"{'Name':<30} | " + " | ".join(f"{name:<20}" for name in field_names))
            print("-" * (30 + len(field_names) * 20))
            for field in fields:
                print(f"{field.get('name', '-'): <30} | " + " | ".join(f"{field.get(name, '-'): <20}" for name in field_names))
            print("\nFeldtypen:")
            print("-" * 80)
            for name, ftype in schema.get('fieldTypes', {}).items():
                print(f"- {name}: {ftype.get('class', '-')}")
            print(f"\nPrimärschlüssel: {schema.get('uniqueKey', '-')}")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Schemas: {e}")
        raise click.ClickException("Konnte das Schema nicht abrufen. Bitte überprüfen Sie die Verbindungseinstellungen.")

if __name__ == '__main__':
    cli()
