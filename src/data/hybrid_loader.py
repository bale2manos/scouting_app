# src/data/hybrid_loader.py
# -*- coding: utf-8 -*-
"""
Cargador híbrido que combina Google Drive y archivos locales
"""
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
from pathlib import Path

from ..config import (
    EXCEL_FILE, 
    TEAM_NAME_DISPLAY, 
    PLAYER_PHOTOS_DIR, 
    PLAYER_NAME_MAPPING,
    FALLBACK_PLAYERS,
    USE_DRIVE_FIRST,
    TEAM_REPORT
)
from .drive_loader import get_drive_loader
from .loader import load_players_dynamically as load_players_local


def _get_image_path_hybrid(player_slug: str) -> Optional[Path]:
    """
    Busca imagen de jugador primero en Drive cache, luego local
    
    Args:
        player_slug: Slug del jugador (ej: "ALMENARA_SANABRIAS_ALVARO")
    
    Returns:
        Path a la imagen o None si no se encuentra
    """
    drive_loader = get_drive_loader()
    
    # Método 1: Buscar en cache de Google Drive
    if USE_DRIVE_FIRST:
        cached_images = drive_loader.get_cached_player_images()
        for image_name, image_path in cached_images.items():
            if player_slug.upper() in image_name.upper():
                return image_path
    
    # Método 2: Buscar en archivos locales
    if PLAYER_PHOTOS_DIR.exists():
        for ext in ['.png', '.jpg', '.jpeg']:
            local_path = PLAYER_PHOTOS_DIR / f"{player_slug}{ext}"
            if local_path.exists():
                return local_path
    
    # Método 3: Si no se encontró y no priorizamos Drive, buscar en cache
    if not USE_DRIVE_FIRST:
        cached_images = drive_loader.get_cached_player_images()
        for image_name, image_path in cached_images.items():
            if player_slug.upper() in image_name.upper():
                return image_path
    
    return None


def get_team_report_path_hybrid() -> Optional[Path]:
    """
    Obtiene la ruta al informe del equipo (Drive o local)
    
    Returns:
        Path al informe del equipo o None si no se encuentra
    """
    drive_loader = get_drive_loader()
    
    # Método 1: Google Drive (si se prioriza)
    if USE_DRIVE_FIRST:
        cached_report = drive_loader.get_cached_team_report()
        if cached_report and cached_report.exists():
            return cached_report
    
    # Método 2: Archivo local
    if TEAM_REPORT.exists():
        return TEAM_REPORT
    
    # Método 3: Google Drive cache (si no se priorizó antes)
    if not USE_DRIVE_FIRST:
        cached_report = drive_loader.get_cached_team_report()
        if cached_report and cached_report.exists():
            return cached_report
    
    return None


@st.cache_data
def load_players_hybrid() -> List[Dict[str, Any]]:
    """
    Carga jugadores combinando Google Drive y archivos locales
    
    Returns:
        Lista de jugadores con imágenes de Drive o locales
    """
    # Primero intentar sincronizar desde Google Drive (sin forzar)
    drive_loader = get_drive_loader()
    
    # Sincronización silenciosa (sin mostrar spinners)
    if drive_loader.drive_client and drive_loader.drive_client.is_authenticated():
        try:
            # Descargar imágenes si no están en cache
            drive_loader.download_player_images(force_refresh=False)
        except Exception:
            pass  # Fallar silenciosamente y continuar con archivos locales
    
    # Cargar jugadores usando el método local existente
    players = load_players_local()
    
    # Actualizar rutas de imágenes con versiones híbridas
    for player in players:
        player_slug = player.get('slug', '')
        if player_slug:
            hybrid_image_path = _get_image_path_hybrid(player_slug)
            if hybrid_image_path:
                player['image_path'] = str(hybrid_image_path)
                player['image_source'] = 'drive' if 'cache' in str(hybrid_image_path) else 'local'
            else:
                player['image_source'] = 'none'
    
    return players


def sync_from_drive(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Sincroniza datos desde Google Drive manualmente
    
    Args:
        force_refresh: Forzar descarga completa
    
    Returns:
        Resultado de la sincronización
    """
    drive_loader = get_drive_loader()
    
    if not drive_loader.drive_client or not drive_loader.drive_client.is_authenticated():
        return {
            'success': False,
            'errors': ['Google Drive no está disponible o no está autenticado']
        }
    
    # Limpiar cache de Streamlit para forzar recarga
    if force_refresh:
        st.cache_data.clear()
    
    return drive_loader.sync_team_data(force_refresh)


def get_drive_status() -> Dict[str, Any]:
    """
    Obtiene el estado de la conexión con Google Drive
    
    Returns:
        Diccionario con información del estado
    """
    drive_loader = get_drive_loader()
    
    status = {
        'authenticated': False,
        'team_report_cached': False,
        'player_images_cached': 0,
        'cache_dir': str(drive_loader.cache_dir),
        'errors': []
    }
    
    try:
        if drive_loader.drive_client:
            status['authenticated'] = drive_loader.drive_client.is_authenticated()
        
        # Verificar archivos en cache
        cached_report = drive_loader.get_cached_team_report()
        status['team_report_cached'] = bool(cached_report and cached_report.exists())
        
        cached_images = drive_loader.get_cached_player_images()
        status['player_images_cached'] = len(cached_images)
        
    except Exception as e:
        status['errors'].append(str(e))
    
    return status


def clear_drive_cache() -> bool:
    """Limpia el cache de Google Drive"""
    drive_loader = get_drive_loader()
    success = drive_loader.clear_cache()
    
    # Limpiar cache de Streamlit también
    if success:
        st.cache_data.clear()
    
    return success