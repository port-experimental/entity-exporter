#!/usr/bin/env python3
"""
Port Entity Exporter

A comprehensive script to extract entities from Port with configurable options for:
- Exporting entities from all blueprints
- Exporting entities from specific blueprints
- Exporting specific entities by identifier
- Excluding specific entities from export

Dependencies:
    pip install requests click python-dotenv PyYAML

Usage:
    # Export all entities from all blueprints
    python port_entity_exporter.py --all

    # Export entities from specific blueprints
    python port_entity_exporter.py --blueprints service,deployment

    # Export specific entities by identifier
    python port_entity_exporter.py --entities service-1,deployment-prod

    # Export all but exclude specific entities
    python port_entity_exporter.py --all --exclude service-1,old-deployment

    # Export to specific file format
    python port_entity_exporter.py --all --format yaml --output entities.yaml

Configuration:
    Set up your Port credentials in a .env file:
    PORT_CLIENT_ID=your_client_id
    PORT_CLIENT_SECRET=your_client_secret
    PORT_BASE_URL=https://api.getport.io/v1  # Optional, defaults to this
"""

import os
import sys
import json
import yaml
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from pathlib import Path

import requests
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('port_exporter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PortEntityExporter:
    """
    Main class for exporting entities from Port with various configuration options.
    """
    
    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://api.getport.io/v1"):
        """
        Initialize the Port Entity Exporter.
        
        Args:
            client_id: Port application client ID
            client_secret: Port application client secret
            base_url: Base URL for Port API (default: https://api.getport.io/v1)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.session = requests.Session()
        
        # Set up session with default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PortEntityExporter/1.0'
        })
    
    def authenticate(self) -> bool:
        """
        Authenticate with Port API and obtain access token.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            auth_url = "https://api.getport.io/v1/auth/access_token"
            
            payload = {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            }
            
            logger.info("Authenticating with Port API...")
            response = requests.post(auth_url, json=payload)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('accessToken')
            
            if not self.access_token:
                logger.error("No access token received from authentication")
                return False
            
            # Update session with authorization header
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            logger.info("Authentication successful")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return False
    
    def get_blueprints(self) -> List[Dict[str, Any]]:
        """
        Retrieve all blueprints from Port.
        
        Returns:
            List[Dict]: List of blueprint objects
        """
        try:
            url = f"{self.base_url}/blueprints"
            logger.info("Fetching blueprints...")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            blueprints = data.get('blueprints', [])
            
            logger.info(f"Retrieved {len(blueprints)} blueprints")
            return blueprints
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch blueprints: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching blueprints: {e}")
            return []
    
    def get_entities_for_blueprint(self, blueprint_id: str, include_calculated: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve all entities for a specific blueprint.
        
        Args:
            blueprint_id: The blueprint identifier
            include_calculated: Whether to include calculated properties
            
        Returns:
            List[Dict]: List of entity objects
        """
        try:
            url = f"{self.base_url}/blueprints/{blueprint_id}/entities"
            params = {}
            
            if not include_calculated:
                params['exclude_calculated_properties'] = 'true'
            
            logger.info(f"Fetching entities for blueprint: {blueprint_id}")
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            entities = data.get('entities', [])
            
            logger.info(f"Retrieved {len(entities)} entities for blueprint {blueprint_id}")
            return entities
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch entities for blueprint {blueprint_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching entities for blueprint {blueprint_id}: {e}")
            return []
    
    def get_entity(self, blueprint_id: str, entity_id: str, include_calculated: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific entity by blueprint and entity identifiers.
        
        Args:
            blueprint_id: The blueprint identifier
            entity_id: The entity identifier
            include_calculated: Whether to include calculated properties
            
        Returns:
            Optional[Dict]: Entity object if found, None otherwise
        """
        try:
            url = f"{self.base_url}/blueprints/{blueprint_id}/entities/{entity_id}"
            params = {}
            
            if not include_calculated:
                params['exclude_calculated_properties'] = 'true'
            
            logger.info(f"Fetching entity: {entity_id} from blueprint: {blueprint_id}")
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            entity = data.get('entity')
            
            if entity:
                logger.info(f"Retrieved entity {entity_id}")
                return entity
            else:
                logger.warning(f"Entity {entity_id} not found in response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch entity {entity_id} from blueprint {blueprint_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching entity {entity_id}: {e}")
            return None
    
    def export_all_entities(self, exclude_entities: Optional[Set[str]] = None, 
                          include_calculated: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export all entities from all blueprints.
        
        Args:
            exclude_entities: Set of entity identifiers to exclude
            include_calculated: Whether to include calculated properties
            
        Returns:
            Dict: Dictionary with blueprint_id as key and list of entities as value
        """
        exclude_entities = exclude_entities or set()
        all_entities = {}
        
        blueprints = self.get_blueprints()
        if not blueprints:
            logger.error("No blueprints found or failed to fetch blueprints")
            return all_entities
        
        for blueprint in blueprints:
            blueprint_id = blueprint.get('identifier')
            if not blueprint_id:
                continue
                
            entities = self.get_entities_for_blueprint(blueprint_id, include_calculated)
            
            # Filter out excluded entities
            filtered_entities = []
            for entity in entities:
                entity_id = entity.get('identifier')
                if entity_id and entity_id not in exclude_entities:
                    filtered_entities.append(entity)
                elif entity_id in exclude_entities:
                    logger.info(f"Excluding entity: {entity_id}")
            
            if filtered_entities:
                all_entities[blueprint_id] = filtered_entities
        
        total_entities = sum(len(entities) for entities in all_entities.values())
        logger.info(f"Exported {total_entities} entities from {len(all_entities)} blueprints")
        
        return all_entities
    
    def export_blueprint_entities(self, blueprint_ids: List[str], exclude_entities: Optional[Set[str]] = None,
                                include_calculated: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export entities from specific blueprints.
        
        Args:
            blueprint_ids: List of blueprint identifiers
            exclude_entities: Set of entity identifiers to exclude
            include_calculated: Whether to include calculated properties
            
        Returns:
            Dict: Dictionary with blueprint_id as key and list of entities as value
        """
        exclude_entities = exclude_entities or set()
        selected_entities = {}
        
        for blueprint_id in blueprint_ids:
            entities = self.get_entities_for_blueprint(blueprint_id, include_calculated)
            
            # Filter out excluded entities
            filtered_entities = []
            for entity in entities:
                entity_id = entity.get('identifier')
                if entity_id and entity_id not in exclude_entities:
                    filtered_entities.append(entity)
                elif entity_id in exclude_entities:
                    logger.info(f"Excluding entity: {entity_id}")
            
            if filtered_entities:
                selected_entities[blueprint_id] = filtered_entities
            else:
                logger.warning(f"No entities found for blueprint: {blueprint_id}")
        
        total_entities = sum(len(entities) for entities in selected_entities.values())
        logger.info(f"Exported {total_entities} entities from {len(selected_entities)} specified blueprints")
        
        return selected_entities
    
    def export_specific_entities(self, entity_specs: List[str], include_calculated: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export specific entities by their identifiers.
        
        Args:
            entity_specs: List of entity identifiers (format: "blueprint_id:entity_id" or just "entity_id")
            include_calculated: Whether to include calculated properties
            
        Returns:
            Dict: Dictionary with blueprint_id as key and list of entities as value
        """
        specific_entities = {}
        
        # If entity specs don't include blueprint, we need to search all blueprints
        entities_without_blueprint = []
        entities_with_blueprint = []
        
        for spec in entity_specs:
            if ':' in spec:
                entities_with_blueprint.append(spec)
            else:
                entities_without_blueprint.append(spec)
        
        # Handle entities with explicit blueprint specification
        for spec in entities_with_blueprint:
            blueprint_id, entity_id = spec.split(':', 1)
            entity = self.get_entity(blueprint_id, entity_id, include_calculated)
            
            if entity:
                if blueprint_id not in specific_entities:
                    specific_entities[blueprint_id] = []
                specific_entities[blueprint_id].append(entity)
        
        # Handle entities without blueprint specification - search all blueprints
        if entities_without_blueprint:
            blueprints = self.get_blueprints()
            
            for blueprint in blueprints:
                blueprint_id = blueprint.get('identifier')
                if not blueprint_id:
                    continue
                
                for entity_id in entities_without_blueprint:
                    entity = self.get_entity(blueprint_id, entity_id, include_calculated)
                    
                    if entity:
                        if blueprint_id not in specific_entities:
                            specific_entities[blueprint_id] = []
                        specific_entities[blueprint_id].append(entity)
                        logger.info(f"Found entity {entity_id} in blueprint {blueprint_id}")
        
        total_entities = sum(len(entities) for entities in specific_entities.values())
        logger.info(f"Exported {total_entities} specific entities")
        
        return specific_entities
    
    def save_entities(self, entities: Dict[str, List[Dict[str, Any]]], output_file: str, format: str = 'json'):
        """
        Save entities to file in specified format.
        
        Args:
            entities: Dictionary of entities to save
            output_file: Output file path
            format: Output format ('json', 'yaml', 'csv')
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(entities, f, indent=2, ensure_ascii=False, default=str)
                    
            elif format.lower() == 'yaml':
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(entities, f, default_flow_style=False, allow_unicode=True)
                    
            elif format.lower() == 'csv':
                # Flatten entities for CSV format
                flattened_data = []
                for blueprint_id, blueprint_entities in entities.items():
                    for entity in blueprint_entities:
                        row = {
                            'blueprint_id': blueprint_id,
                            'entity_id': entity.get('identifier', ''),
                            'title': entity.get('title', ''),
                            'created_at': entity.get('createdAt', ''),
                            'updated_at': entity.get('updatedAt', ''),
                            'created_by': entity.get('createdBy', ''),
                            'updated_by': entity.get('updatedBy', ''),
                        }
                        
                        # Add properties as separate columns
                        properties = entity.get('properties', {})
                        for prop_key, prop_value in properties.items():
                            row[f'prop_{prop_key}'] = str(prop_value) if prop_value is not None else ''
                        
                        # Add relations as separate columns
                        relations = entity.get('relations', {})
                        for rel_key, rel_value in relations.items():
                            row[f'rel_{rel_key}'] = str(rel_value) if rel_value is not None else ''
                        
                        flattened_data.append(row)
                
                if flattened_data:
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        fieldnames = set()
                        for row in flattened_data:
                            fieldnames.update(row.keys())
                        
                        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                        writer.writeheader()
                        writer.writerows(flattened_data)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Entities saved to {output_path} in {format.upper()} format")
            
            # Print summary
            total_entities = sum(len(blueprint_entities) for blueprint_entities in entities.values())
            print(f"\n✅ Export completed successfully!")
            print(f"📊 Total entities exported: {total_entities}")
            print(f"📁 Blueprints included: {len(entities)}")
            print(f"💾 Output file: {output_path}")
            print(f"📄 Format: {format.upper()}")
            
        except Exception as e:
            logger.error(f"Failed to save entities to {output_file}: {e}")
            raise


@click.command()
@click.option('--all', 'export_all', is_flag=True, help='Export all entities from all blueprints')
@click.option('--blueprints', help='Comma-separated list of blueprint identifiers to export')
@click.option('--entities', help='Comma-separated list of entity identifiers to export (format: blueprint:entity or just entity)')
@click.option('--exclude', help='Comma-separated list of entity identifiers to exclude from export')
@click.option('--output', '-o', default='port_entities', help='Output file name (default: port_entities)')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'csv']), default='json', help='Output format (default: json)')
@click.option('--include-calculated/--exclude-calculated', default=True, help='Include calculated properties (default: True)')
@click.option('--client-id', envvar='PORT_CLIENT_ID', help='Port client ID (can be set via PORT_CLIENT_ID env var)')
@click.option('--client-secret', envvar='PORT_CLIENT_SECRET', help='Port client secret (can be set via PORT_CLIENT_SECRET env var)')
@click.option('--base-url', envvar='PORT_BASE_URL', default='https://api.getport.io/v1', help='Port API base URL')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(export_all, blueprints, entities, exclude, output, format, include_calculated, 
         client_id, client_secret, base_url, verbose):
    """
    Port Entity Exporter - Extract entities from Port with configurable options.
    
    Examples:
        # Export all entities from all blueprints
        python port_entity_exporter.py --all
        
        # Export entities from specific blueprints
        python port_entity_exporter.py --blueprints service,deployment
        
        # Export specific entities by identifier
        python port_entity_exporter.py --entities service-1,deployment-prod
        
        # Export all but exclude specific entities
        python port_entity_exporter.py --all --exclude service-1,old-deployment
        
        # Export to YAML format
        python port_entity_exporter.py --all --format yaml --output entities.yaml
    """
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate required parameters
    if not client_id or not client_secret:
        click.echo("❌ Error: PORT_CLIENT_ID and PORT_CLIENT_SECRET must be provided", err=True)
        click.echo("Set them as environment variables or use --client-id and --client-secret options", err=True)
        sys.exit(1)
    
    # Validate export options
    export_options = [export_all, blueprints, entities]
    if sum(bool(option) for option in export_options) != 1:
        click.echo("❌ Error: You must specify exactly one export option: --all, --blueprints, or --entities", err=True)
        sys.exit(1)
    
    # Initialize exporter
    exporter = PortEntityExporter(client_id, client_secret, base_url)
    
    # Authenticate
    if not exporter.authenticate():
        click.echo("❌ Authentication failed. Please check your credentials.", err=True)
        sys.exit(1)
    
    # Parse exclude list
    exclude_set = set()
    if exclude:
        exclude_set = set(item.strip() for item in exclude.split(',') if item.strip())
    
    # Export entities based on selected option
    try:
        if export_all:
            click.echo("🚀 Exporting all entities from all blueprints...")
            exported_entities = exporter.export_all_entities(exclude_set, include_calculated)
            
        elif blueprints:
            blueprint_list = [item.strip() for item in blueprints.split(',') if item.strip()]
            click.echo(f"🚀 Exporting entities from blueprints: {', '.join(blueprint_list)}")
            exported_entities = exporter.export_blueprint_entities(blueprint_list, exclude_set, include_calculated)
            
        elif entities:
            entity_list = [item.strip() for item in entities.split(',') if item.strip()]
            click.echo(f"🚀 Exporting specific entities: {', '.join(entity_list)}")
            exported_entities = exporter.export_specific_entities(entity_list, include_calculated)
        
        # Add file extension if not provided
        output_file = output
        if not output_file.endswith(f'.{format}'):
            output_file = f"{output_file}.{format}"
        
        # Save entities
        exporter.save_entities(exported_entities, output_file, format)
        
    except KeyboardInterrupt:
        click.echo("\n❌ Export cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 