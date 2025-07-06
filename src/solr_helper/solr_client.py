# Importiert die notwendigen Bibliotheken
import pysolr  # Python-Bibliothek für die Interaktion mit Solr
from loguru import logger  # Für das Logging
from typing import Optional, Dict, Any, List, Union
import requests  # Für direkte HTTP-Anfragen an die Solr-API


class SolrClient:
    """Ein Client für die Kommunikation mit einem Solr-Server."""

    def __init__(self, solr_url: str = "http://localhost:8983/solr", core: str = "testing"):
        """
        Initialisiert den Solr-Client mit pysolr.

        Args:
            solr_url (str): Die Basis-URL des Solr-Servers.
            core (str): Der Name des Solr-Cores, mit dem kommuniziert werden soll.
        """
        # Konstruiert die vollständige URL zum Solr-Core
        self.core_url = f"{solr_url}/{core}"
        # Initialisiert die pysolr-Instanz
        self.solr = pysolr.Solr(self.core_url, timeout=10)
        logger.info(f"Solr-Client für Core-URL '{self.core_url}' initialisiert.")

    def check_connection(self) -> bool:
        """
        Überprüft, ob eine Verbindung zum Solr-Core hergestellt werden kann.
        Verwendet die search-Methode von pysolr, die mit allen Solr-Versionen kompatibel ist.

        Returns:
            bool: True, wenn die Verbindung erfolgreich ist, sonst False.
        """
        logger.info(f"Überprüfe Solr-Verbindung an: {self.core_url}")

        try:
            # Führt eine einfache Suche ohne Ergebnisse durch
            # Die search-Methode wirft eine Ausnahme, wenn die Verbindung fehlschlägt
            self.solr.search('*:*', rows=0)
            logger.success("Verbindung zum Solr-Core erfolgreich hergestellt.")
            return True
            
        except pysolr.SolrError as e:
            # Fängt Solr-spezifische Fehler ab
            logger.error(f"Fehler bei der Verbindung zum Solr-Core: {e}")
            return False
        except Exception as e:
            # Fängt alle anderen Fehler ab (z.B. Netzwerkprobleme)
            logger.error(f"Unbekannter Fehler bei der Verbindung zum Solr-Core: {e}")
            return False
            
    def get_schema(self) -> Dict[str, Any]:
        """
        Ruft das Schema des Solr-Cores ab und gibt Informationen über die Felder zurück.
        
        Returns:
            Dict[str, Any]: Ein Dictionary mit Informationen zum Schema, einschließlich der Felder
                           und ihrer Eigenschaften.
        """
        try:
            # Erstelle die URL für den Schema-Endpunkt
            schema_url = f"{self.core_url}/schema"
            
            # Führe die Anfrage an die Schema-API durch
            response = requests.get(schema_url, params={'wt': 'json'})
            response.raise_for_status()
            
            # Extrahiere die relevanten Informationen aus der Antwort
            schema_data = response.json()
            
            # Erstelle ein aufgeräumtes Ergebnis-Dictionary
            result = {
                'core': self.core_url.split('/')[-1],
                'fields': [],
                'field_types': {},
                'unique_key': schema_data.get('uniqueKey', 'id')
            }
            
            # Verarbeite die Felder
            for field in schema_data.get('fields', []):
                field_info = {
                    'name': field.get('name'),
                    'type': field.get('type'),
                    'required': field.get('required', False),
                    'indexed': field.get('indexed', False),
                    'stored': field.get('stored', False),
                    'multi_valued': field.get('multiValued', False),
                    'default_value': field.get('default', None)
                }
                result['fields'].append(field_info)
            
            # Verarbeite die Feldtypen
            for field_type in schema_data.get('fieldTypes', []):
                result['field_types'][field_type.get('name')] = {
                    'class': field_type.get('class', '').split('.')[-1],
                    'analyzer': field_type.get('analyzer', {}).get('class', '').split('.')[-1]
                }
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Abrufen des Schemas: {e}")
            raise
        except Exception as e:
            logger.error(f"Unbekannter Fehler beim Verarbeiten des Schemas: {e}")
            raise
