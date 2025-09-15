# src/data/__init__.py
"""
Módulo de datos para la aplicación Scouting Hub
"""

from .loader import (
    load_players_dynamically,
    get_team_players,
    find_player_by_slug
)

# Importaciones de Google Drive (solo)
from .drive_loader import (
    load_players,
    get_team_report_path,
    get_player_image_path,
    force_sync,
    get_sync_status
)

__all__ = [
    # Funciones originales (solo local - mantenidas para compatibilidad)
    'load_players_dynamically',
    'get_team_players',
    'find_player_by_slug',
    
    # Funciones de Google Drive
    'load_players',
    'get_team_report_path',
    'get_player_image_path',
    'force_sync',
    'get_sync_status'
]