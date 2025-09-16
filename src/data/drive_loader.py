# src/data/drive_loader.py
# -*- coding: utf-8 -*-
"""
Cargador principal de datos desde Google Drive
"""
import os
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
import streamlit as st

from ..utils.google_drive import get_drive_client
from ..config import (
    GOOGLE_DRIVE_ROOT_FOLDER_ID, 
    DRIVE_CACHE_DIR, 
    CACHE_EXPIRY_HOURS,
    TEAM_SLUG,
    TEAM_NAME_DISPLAY,
    EXCEL_FILE
)


import requests  # <-- arriba (si no estaba)

@st.cache_data(show_spinner=False, ttl=3600)
def _probe_image_url(url: str) -> bool:
    try:
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        if not url.startswith("http"):
            return False

        headers = {
            "Range": "bytes=0-1023",
            "User-Agent": "Mozilla/5.0 Streamlit/1.0",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        }
        r = requests.get(url, headers=headers, timeout=4, stream=True)
        if r.status_code not in (200, 206):
            return False

        ctype = r.headers.get("Content-Type", "").lower()
        if not ctype.startswith("image/"):
            return False

        chunk = next(r.iter_content(1024), b"")
        if not chunk:
            return False

        is_png = chunk.startswith(b"\x89PNG\r\n\x1a\n")
        is_jpg = chunk.startswith(b"\xff\xd8\xff")
        is_webp = chunk[:4] == b"RIFF" and b"WEBP" in chunk[:12]
        return bool(is_png or is_jpg or is_webp)
    except Exception:
        return False


def _safe_image_url(url: str) -> str:
    """Devuelve la URL si es imagen real, si no devuelve ''."""
    return url if _probe_image_url(url) else ""


class DriveDataLoader:
    """Cargador de datos desde Google Drive con cache local"""
    
    def __init__(self):
        self.drive_client = get_drive_client()
        self.cache_dir = DRIVE_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache de IDs de carpetas para evitar búsquedas repetidas
        self._folder_cache = {}
    
    def is_cache_valid(self, file_path: Path) -> bool:
        """Verifica si el archivo en cache es válido (no expirado)"""
        if not file_path.exists():
            return False
        
        # Verificar tiempo de modificación
        file_time = file_path.stat().st_mtime
        current_time = time.time()
        age_hours = (current_time - file_time) / 3600
        
        return age_hours < CACHE_EXPIRY_HOURS
    
    def get_team_folder_id(self, team_name: str = None) -> Optional[str]:
        """
        Obtiene el ID de la carpeta del equipo
        
        Args:
            team_name: Nombre del equipo (por defecto usa TEAM_NAME_DISPLAY)
        
        Returns:
            ID de la carpeta del equipo o None si no se encuentra
        """
        if not self.drive_client:
            return None
        
        team_name = team_name or TEAM_NAME_DISPLAY
        cache_key = f"team_folder_{team_name}"
        
        # Verificar cache de carpetas
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        
        # Buscar carpeta del equipo
        folder_id = self.drive_client.find_team_folder(GOOGLE_DRIVE_ROOT_FOLDER_ID, team_name)
        
        if folder_id:
            self._folder_cache[cache_key] = folder_id
        
        return folder_id
    
    def get_players_folder_id(self, team_folder_id: str) -> Optional[str]:
        """
        Obtiene el ID de la carpeta de jugadores
        
        Args:
            team_folder_id: ID de la carpeta del equipo
        
        Returns:
            ID de la carpeta de jugadores o None si no se encuentra
        """
        if not self.drive_client:
            return None
        
        cache_key = f"players_folder_{team_folder_id}"
        
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        
        # Buscar carpeta de jugadores
        folders = self.drive_client.list_folders_in_folder(team_folder_id)
        
        for folder in folders:
            if folder['name'].lower() == 'jugadores':
                self._folder_cache[cache_key] = folder['id']
                return folder['id']
        
        return None
    
    def download_team_report(self, force_refresh: bool = False) -> Optional[Path]:
        """
        Descarga el informe del equipo desde Google Drive
        
        Args:
            force_refresh: Forzar descarga aunque exista en cache
        
        Returns:
            Path al archivo local del informe o None si falla
        """
        # Crear carpeta de cache para el equipo
        team_cache_dir = self.cache_dir / TEAM_SLUG
        team_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Ruta del archivo en cache
        cached_file = team_cache_dir / f"{TEAM_SLUG}.pdf"
        
        # Verificar si usar cache
        if not force_refresh and self.is_cache_valid(cached_file):
            return cached_file
        
        # Descargar desde Google Drive
        if not self.drive_client:
            return None
        
        team_folder_id = self.get_team_folder_id()
        if not team_folder_id:
            st.warning(f"📁 No se encontró la carpeta del equipo: {TEAM_NAME_DISPLAY}")
            return None
        
        # Buscar archivo PDF del equipo
        files = self.drive_client.list_files_in_folder(team_folder_id, 'pdf')
        
        team_pdf = None
        for file in files:
            if file['name'].lower() == f"{TEAM_SLUG}.pdf":
                team_pdf = file
                break
        
        if not team_pdf:
            st.warning(f"📄 No se encontró el archivo: {TEAM_SLUG}.pdf")
            return None
        
        # Descargar archivo
        if self.drive_client.download_file(team_pdf['id'], cached_file):
            return cached_file
        else:
            return None
    
    def download_player_images(self, force_refresh: bool = False) -> Dict[str, Path]:
        """
        Descarga todas las imágenes de jugadores desde Google Drive
        
        Args:
            force_refresh: Forzar descarga aunque existan en cache
        
        Returns:
            Diccionario con {nombre_archivo: path_local}
        """
        # Crear carpeta de cache para jugadores
        players_cache_dir = self.cache_dir / TEAM_SLUG / "jugadores"
        players_cache_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_images = {}
        
        if not self.drive_client:
            return downloaded_images
        
        # Obtener carpeta de jugadores
        team_folder_id = self.get_team_folder_id()
        if not team_folder_id:
            return downloaded_images
        
        players_folder_id = self.get_players_folder_id(team_folder_id)
        if not players_folder_id:
            st.warning("📁 No se encontró la carpeta de jugadores")
            return downloaded_images
        
        # Listar imágenes en la carpeta de jugadores
        images = self.drive_client.list_files_in_folder(players_folder_id, 'png')
        
        for image in images:
            original_name = image['name']
            # Normalizar nombre del archivo a minúsculas para consistencia
            normalized_name = original_name.lower()
            cached_image = players_cache_dir / normalized_name
            
            # Debug info para desarrollo
            if 'ALMENARA' in original_name.upper():
                st.info(f"🔍 Procesando: {original_name} → {normalized_name}")
            
            # Verificar si usar cache
            if not force_refresh and self.is_cache_valid(cached_image):
                downloaded_images[normalized_name] = cached_image
                continue
            
            # Descargar imagen con nombre normalizado
            if self.drive_client.download_file(image['id'], cached_image):
                downloaded_images[normalized_name] = cached_image
                if 'ALMENARA' in original_name.upper():
                    st.success(f"✅ Descargado: {normalized_name}")
            else:
                if 'ALMENARA' in original_name.upper():
                    st.error(f"❌ Error descargando: {original_name}")
        
        return downloaded_images
    
    def sync_team_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Sincroniza todos los datos del equipo desde Google Drive
        
        Args:
            force_refresh: Forzar descarga completa
        
        Returns:
            Diccionario con rutas a archivos descargados
        """
        result = {
            'team_report': None,
            'player_images': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Descargar informe del equipo
            with st.spinner("📄 Sincronizando informe del equipo..."):
                team_report = self.download_team_report(force_refresh)
                result['team_report'] = team_report
            
            # Descargar imágenes de jugadores
            with st.spinner("🖼️ Sincronizando imágenes de jugadores..."):
                player_images = self.download_player_images(force_refresh)
                result['player_images'] = player_images
            
            result['success'] = bool(team_report or player_images)
            
            if not result['success']:
                st.warning("⚠️ No se pudieron descargar datos desde Google Drive")
                
        except Exception as e:
            error_msg = f"Error durante la sincronización: {str(e)}"
            result['errors'].append(error_msg)
            st.error(f"❌ {error_msg}")
        
        return result
    
    def get_cached_team_report(self) -> Optional[Path]:
        """Obtiene el informe del equipo desde cache (sin descargar)"""
        cached_file = self.cache_dir / TEAM_SLUG / f"{TEAM_SLUG}.pdf"
        return cached_file if cached_file.exists() else None
    
    def get_cached_player_images(self) -> Dict[str, Path]:
        """Obtiene las imágenes de jugadores desde cache (sin descargar)"""
        players_cache_dir = self.cache_dir / TEAM_SLUG / "jugadores"
        
        if not players_cache_dir.exists():
            return {}
        
        images = {}
        needs_cleanup = False
        
        for file_path in players_cache_dir.glob("*.png"):
            filename = file_path.name
            # Verificar si hay archivos con nombres en mayúsculas (cache obsoleto)
            if filename != filename.lower():
                needs_cleanup = True
                st.warning(f"⚠️ Archivo obsoleto detectado: {filename}")
            else:
                images[filename] = file_path
        
        # Si detectamos archivos obsoletos, limpiar cache
        if needs_cleanup:
            st.info("🧹 Limpiando cache obsoleto...")
            try:
                import shutil
                shutil.rmtree(players_cache_dir)
                players_cache_dir.mkdir(parents=True, exist_ok=True)
                return {}  # Forzar descarga
            except Exception as e:
                st.error(f"❌ Error limpiando cache: {str(e)}")
        
        return images
    
    def clear_cache(self) -> bool:
        """Limpia el cache del equipo actual"""
        try:
            team_cache_dir = self.cache_dir / TEAM_SLUG
            if team_cache_dir.exists():
                import shutil
                shutil.rmtree(team_cache_dir)
                return True
        except Exception as e:
            st.error(f"❌ Error al limpiar cache: {str(e)}")
        
        return False


# Instancia global del cargador
_drive_loader = None

def get_drive_loader() -> DriveDataLoader:
    """Obtiene la instancia global del cargador de Drive"""
    global _drive_loader
    
    if _drive_loader is None:
        _drive_loader = DriveDataLoader()
    
    return _drive_loader


def auto_sync_on_load():
    """Sincronización automática al cargar la aplicación"""
    if 'drive_synced' not in st.session_state:
        loader = get_drive_loader()
        
        # En producción (Streamlit Cloud), verificar si hay cache antes de sincronizar
        is_production = not Path("credentials/google_drive_credentials.json").exists()
        
        if is_production:
            # En producción, siempre sincronizar la primera vez
            st.info("☁️ Sincronizando datos desde Google Drive...")
            with st.spinner("🔄 Descargando archivos..."):
                result = loader.sync_team_data(force_refresh=True)
        else:
            # En desarrollo, usar cache si existe
            with st.spinner("🔄 Sincronizando con Google Drive..."):
                result = loader.sync_team_data(force_refresh=False)
        
        st.session_state['drive_synced'] = result['success']
        st.session_state['sync_timestamp'] = time.time()
        
        if result['success']:
            # Mostrar información de sincronización
            team_report = result.get('team_report')
            player_images = result.get('player_images', {})
            
            if team_report:
                st.success(f"✅ Informe del equipo sincronizado")
            
            if player_images:
                st.success(f"✅ {len(player_images)} imágenes de jugadores sincronizadas")
        else:
            st.error("❌ Error en la sincronización inicial")


def load_players() -> List[Dict[str, Any]]:
    """
    Carga la lista de jugadores basándose ÚNICAMENTE en las imágenes disponibles en Google Drive.
    Invierte la lógica: parte de las imágenes en Drive y busca su información en el Excel.
    
    Returns:
        Lista de diccionarios con datos de jugadores que tienen imagen PNG en Google Drive
    """
    try:
        # Sincronizar automáticamente si es necesario
        auto_sync_on_load()
        
        # Obtener lista de imágenes disponibles en Google Drive
        loader = get_drive_loader()
        available_images = loader.get_cached_player_images()
        
        if not available_images:
            # Si no hay imágenes en cache, intentar descargar
            available_images = loader.download_player_images(force_refresh=False)
        
        if not available_images:
            st.warning("⚠️ No hay imágenes disponibles en Google Drive")
            return []
        
        # Cargar datos del Excel
        if not EXCEL_FILE.exists():
            st.error(f"❌ No se encuentra el archivo Excel: {EXCEL_FILE}")
            return []
        
        df = pd.read_excel(EXCEL_FILE)
        
        # Filtrar solo jugadores del equipo actual
        team_players = df[df['EQUIPO'] == TEAM_NAME_DISPLAY].copy()
        
        if len(team_players) == 0:
            st.warning(f"⚠️ No se encontraron jugadores para el equipo: {TEAM_NAME_DISPLAY}")
            return []
        
        # Rellenar valores NaN
        team_players = team_players.fillna("")
        
        # INVERTIR LA LÓGICA: partir de las imágenes en Drive y buscar en Excel
        players_data = []
        used_players = set()  # Para evitar que un jugador del Excel se use múltiples veces
        
        for image_filename in available_images.keys():
            # Extraer información del nombre del archivo
            # Formato: APELLIDOS_NOMBRE.png o APELLIDOS_INICIAL.png
            image_base = image_filename.replace('.png', '').upper()
            
            # Buscar coincidencia en el Excel
            matching_player = None
            matching_index = None
            
            for idx, row in team_players.iterrows():
                # Saltar si este jugador ya fue usado
                if idx in used_players:
                    continue
                    
                full_name = row['JUGADOR']
                
                # Extraer apellidos y nombre del Excel
                if ',' in full_name:
                    # Formato: "APELLIDOS, NOMBRE"
                    parts = full_name.split(',', 1)
                    surnames = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else ""
                    name = name.split()[0] if name else "N"
                    name = name[0] if name else "N"
                else:
                    # Formato: "INICIAL. APELLIDOS"
                    name_parts = full_name.split(' ', 1) if full_name else ['', '']
                    if len(name_parts) >= 2:
                        first_part = name_parts[0].replace('.', '').strip()
                        surnames = name_parts[1]
                        name = first_part
                    else:
                        name = full_name[:1] if full_name else "N"
                        surnames = full_name[2:] if len(full_name) > 2 else "APELLIDOS"
                
                # Normalizar para comparación
                surnames_normalized = surnames.upper().replace(' ', '_').replace('Ñ', 'N').replace(',', '')
                name_normalized = name.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U').replace('Ü', 'U')
                
                # Verificar si coincide con el archivo
                expected_pattern = f"{surnames_normalized}_{name_normalized}"
                expected_pattern_initial = f"{surnames_normalized}_{name_normalized[0]}" if len(name_normalized) > 1 else expected_pattern
                
                if (image_base == expected_pattern or 
                    image_base == expected_pattern_initial or
                    image_base.startswith(surnames_normalized + '_')):
                    matching_player = row
                    matching_index = idx
                    break
            
            if matching_player is not None and matching_index is not None:
                # Marcar este jugador como usado
                used_players.add(matching_index)
                
                # Extraer datos del jugador desde Excel
                full_name = matching_player['JUGADOR']
                
                # Re-extraer nombre y apellidos para estructura final
                if ',' in full_name:
                    parts = full_name.split(',', 1)
                    surnames = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else ""
                    name = name.split()[0] if name else "N"
                    name = name[0] if name else "N"
                else:
                    name_parts = full_name.split(' ', 1) if full_name else ['', '']
                    if len(name_parts) >= 2:
                        first_part = name_parts[0].replace('.', '').strip()
                        surnames = name_parts[1]
                        name = first_part
                    else:
                        name = full_name[:1] if full_name else "N"
                        surnames = full_name[2:] if len(full_name) > 2 else "APELLIDOS"
                
                dorsal = int(matching_player['DORSAL']) if pd.notna(matching_player['DORSAL']) else 0
                
                # Crear slug único usando nombre del archivo para evitar duplicados
                slug = image_filename.replace('.png', '').lower()
                
                player_data = {
                    'number': dorsal,
                    'name': name,
                    'surnames': surnames,
                    'slug': slug,
                    'full_name': full_name,
                    'team': matching_player['EQUIPO'],
                    'image_url': _safe_image_url(str(matching_player.get('IMAGEN', ''))),
                    'image_filename': image_filename,
                    'points': int(matching_player['PUNTOS']) if pd.notna(matching_player['PUNTOS']) else 0,
                    'minutes': float(matching_player['MINUTOS JUGADOS']) if pd.notna(matching_player['MINUTOS JUGADOS']) else 0.0,
                    'games_played': int(matching_player['PJ']) if pd.notna(matching_player['PJ']) else 0
                }
                players_data.append(player_data)
            else:
                # Crear jugador genérico para imágenes sin coincidencia en Excel
                # Extraer nombre del archivo para mostrar
                name_from_file = image_filename.replace('.png', '').replace('_', ' ').title()
                
                # Crear slug único usando nombre del archivo
                slug = image_filename.replace('.png', '').lower()
                
                player_data = {
                    'number': 0,
                    'name': name_from_file.split()[-1] if name_from_file else "Jugador",
                    'surnames': ' '.join(name_from_file.split()[:-1]) if len(name_from_file.split()) > 1 else "Sin Datos",
                    'slug': slug,
                    'full_name': name_from_file,
                    'team': TEAM_NAME_DISPLAY,
                    'image_url': '',  # Sin URL, usará imagen genérica
                    'image_filename': image_filename,
                    'points': 0,
                    'minutes': 0.0,
                    'games_played': 0
                }
                players_data.append(player_data)
        
        # Ordenar por dorsal
        players_data.sort(key=lambda x: x['number'])
        
        return players_data
            
    except Exception as e:
        st.error(f"❌ Error cargando jugadores: {str(e)}")
        import traceback
        st.error(f"📋 Traceback: {traceback.format_exc()}")
        return []


def get_team_report_path() -> Optional[Path]:
    """
    Obtiene la ruta del informe del equipo desde Google Drive
    
    Returns:
        Path al archivo del informe o None si no está disponible
    """
    try:
        # Sincronizar automáticamente si es necesario  
        auto_sync_on_load()
        
        loader = get_drive_loader()
        
        # Intentar obtener desde cache primero
        cached_report = loader.get_cached_team_report()
        if cached_report and cached_report.exists():
            return cached_report
        
        # Si no está en cache, intentar descargar
        return loader.download_team_report(force_refresh=False)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo informe del equipo: {str(e)}")
        return None


def get_player_image_path(player_name: str) -> Optional[Path]:
    """
    Obtiene la ruta de la imagen de un jugador desde Google Drive
    
    Args:
        player_name: Nombre del archivo de imagen (ej: "jugador_1.png")
    
    Returns:
        Path a la imagen o None si no está disponible
    """
    try:
        # Sincronizar automáticamente si es necesario
        auto_sync_on_load()
        
        loader = get_drive_loader()
        
        # Normalizar nombre del archivo
        normalized_name = player_name.lower()
        
        # Obtener imágenes desde cache
        cached_images = loader.get_cached_player_images()
        
        if normalized_name in cached_images:
            return cached_images[normalized_name]
        
        # Si no está en cache, intentar descargar TODAS las imágenes
        st.info(f"🔄 Descargando imagen: {player_name}")
        downloaded_images = loader.download_player_images(force_refresh=True)
        
        if normalized_name in downloaded_images:
            return downloaded_images[normalized_name]
        
        # Si aún no se encuentra, mostrar información de debugging
        st.warning(f"❌ No se encontró la imagen: {normalized_name}")
        st.info("📋 Imágenes disponibles:")
        for available_name in downloaded_images.keys():
            st.write(f"• {available_name}")
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error obteniendo imagen del jugador {player_name}: {str(e)}")
        return None


def force_sync():
    """Fuerza una sincronización completa con Google Drive"""
    try:
        loader = get_drive_loader()
        
        # Limpiar cache antes de sincronizar
        st.info("🧹 Limpiando cache antes de sincronización...")
        loader.clear_cache()
        
        result = loader.sync_team_data(force_refresh=True)
        
        # Actualizar estado de sesión
        st.session_state['drive_synced'] = result['success']
        st.session_state['sync_timestamp'] = time.time()
        
        return result
        
    except Exception as e:
        st.error(f"❌ Error en sincronización forzada: {str(e)}")
        return {'success': False, 'errors': [str(e)]}


def debug_player_files():
    """Función de debugging para verificar archivos de jugadores"""
    try:
        loader = get_drive_loader()
        
        # Mostrar archivos en cache local
        cached_images = loader.get_cached_player_images()
        st.subheader("📁 Archivos en Cache Local:")
        for filename, path in cached_images.items():
            st.write(f"• {filename} → {path}")
        
        # Mostrar archivos en Google Drive
        team_folder_id = loader.get_team_folder_id()
        if team_folder_id:
            players_folder_id = loader.get_players_folder_id(team_folder_id)
            if players_folder_id and loader.drive_client:
                images = loader.drive_client.list_files_in_folder(players_folder_id, 'png')
                st.subheader("☁️ Archivos en Google Drive:")
                for image in images:
                    st.write(f"• {image['name']} → {image['name'].lower()}")
        
    except Exception as e:
        st.error(f"❌ Error en debugging: {str(e)}")


def get_sync_status() -> Dict[str, Any]:
    """Obtiene el estado actual de sincronización"""
    return {
        'is_synced': st.session_state.get('drive_synced', False),
        'last_sync': st.session_state.get('sync_timestamp', 0),
        'drive_available': get_drive_client() is not None
    }