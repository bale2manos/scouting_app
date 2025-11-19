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
            return None
        
        # Buscar archivo PDF del equipo
        files = self.drive_client.list_files_in_folder(team_folder_id, 'pdf')
        
        team_pdf = None
        for file in files:
            if file['name'].lower() == f"{TEAM_SLUG}.pdf":
                team_pdf = file
                break
        
        if not team_pdf:
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
            return downloaded_images
        
        # Listar imágenes en la carpeta de jugadores
        images = self.drive_client.list_files_in_folder(players_folder_id, 'png')
        
        for image in images:
            original_name = image['name']
            # Normalizar nombre del archivo a minúsculas para consistencia
            normalized_name = original_name.lower()
            cached_image = players_cache_dir / normalized_name
            
            # Verificar si usar cache
            if not force_refresh and self.is_cache_valid(cached_image):
                downloaded_images[normalized_name] = cached_image
                continue
            
            # Descargar imagen con nombre normalizado
            if self.drive_client.download_file(image['id'], cached_image):
                downloaded_images[normalized_name] = cached_image
            # Else: fallar silenciosamente
        
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
            team_report = self.download_team_report(force_refresh)
            result['team_report'] = team_report
            
            # Descargar imágenes de jugadores
            player_images = self.download_player_images(force_refresh)
            result['player_images'] = player_images
            
            result['success'] = bool(team_report or player_images)
                
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
        
        def _normalize_name(name: str) -> str:
            """Normaliza un nombre de fichero: minusculas, sin tildes en vocales, mantiene ñ"""
            # Mapeo SOLO de vocales con tilde (NO tocar Ñ ni Ç)
            mp = {
                'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ü': 'u',
                'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u'
            }
            # Separate name and extension
            if '.' in name:
                base, ext = name.rsplit('.', 1)
                ext = ext.lower()
            else:
                base, ext = name, ''

            # Replace accented vowels
            for k, v in mp.items():
                base = base.replace(k, v)

            # Convert to lowercase (esto mantiene ñ como ñ)
            base = base.lower()
            
            # Limpiar prefijos numéricos extraños al inicio (ej: 10221fespino → espino)
            # Solo si empieza con dígitos seguidos de una letra minúscula
            import re
            base = re.sub(r'^\d+[a-z](?=[a-z_])', '', base)
            
            # Replace spaces and multiple underscores
            base = base.replace(' ', '_').replace('-', '_')
            while '__' in base:
                base = base.replace('__', '_')

            return f"{base}.{ext}" if ext else base

        images: Dict[str, Path] = {}
        renamed_count = 0

        # Consider png, jpg, jpeg
        for pattern in ('*.png', '*.jpg', '*.jpeg'):
            for file_path in players_cache_dir.glob(pattern):
                filename = file_path.name
                normalized = _normalize_name(filename)

                # If normalized name differs, try to rename (safe)
                if normalized != filename:
                    target_path = players_cache_dir / normalized
                    try:
                        # If target exists, skip rename to avoid overwrite
                        if not target_path.exists():
                            file_path.rename(target_path)
                            file_path = target_path
                            renamed_count += 1
                        else:
                            # prefer existing normalized file
                            file_path.unlink()
                            file_path = target_path
                    except Exception as e:
                        # If rename fails, try to force rename
                        print(f"⚠️ Error renombrando {filename} → {normalized}: {e}")
                        # Try to create normalized version and delete original
                        try:
                            import shutil
                            shutil.copy2(file_path, target_path)
                            file_path.unlink()
                            file_path = target_path
                            renamed_count += 1
                        except Exception as e2:
                            print(f"⚠️ Error forzando renombrado: {e2}")
                            # Keep original if all fails
                            pass

                # Always use normalized name in dictionary
                final_name = _normalize_name(file_path.name)
                final_path = players_cache_dir / final_name
                if final_path.exists():
                    images[final_name] = final_path
                else:
                    images[file_path.name] = file_path

        if renamed_count > 0:
            st.info(f"🧹 {renamed_count} archivo(s) obsoleto(s) renombrado(s) en caché")

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
    """Sincronización automática silenciosa al cargar la aplicación"""
    if 'drive_synced' not in st.session_state:
        loader = get_drive_loader()
        
        # En producción (Streamlit Cloud), verificar si hay cache antes de sincronizar
        is_production = not Path("credentials/google_drive_credentials.json").exists()
        
        try:
            if is_production:
                # En producción, siempre sincronizar la primera vez
                result = loader.sync_team_data(force_refresh=True)
            else:
                # En desarrollo, usar cache si existe
                result = loader.sync_team_data(force_refresh=False)
            
            st.session_state['drive_synced'] = result['success']
            st.session_state['sync_timestamp'] = time.time()
        except:
            # Fallar silenciosamente
            st.session_state['drive_synced'] = False


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
                
                # Normalizar para comparación (mantener ñ, solo quitar tildes de vocales)
                surnames_normalized = surnames.upper().replace(' ', '_').replace(',', '')
                # Quitar tildes de vocales pero MANTENER Ñ
                for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                    surnames_normalized = surnames_normalized.replace(src, tgt)
                
                name_normalized = name.upper()
                for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                    name_normalized = name_normalized.replace(src, tgt)
                
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
        # Fallar silenciosamente
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
        downloaded_images = loader.download_player_images(force_refresh=True)
        
        if normalized_name in downloaded_images:
            return downloaded_images[normalized_name]
        
        # Si aún no se encuentra, retornar None silenciosamente
        return None
        
    except Exception as e:
        st.error(f"❌ Error obteniendo imagen del jugador {player_name}: {str(e)}")
        return None


def get_player_image_path_by_drive_id(player_name: str, team_name: str, team_slug: str, drive_id: str) -> Optional[Path]:
    """
    Obtiene la ruta de la imagen de un jugador desde un equipo específico por drive_id
    
    Args:
        player_name: Nombre del archivo de imagen (ej: "jugador_1.png")
        team_name: Nombre del equipo
        team_slug: Slug del equipo (para cache)
        drive_id: ID de la carpeta del equipo en Google Drive
    
    Returns:
        Path a la imagen o None si no está disponible
    """
    try:
        drive_client = get_drive_client()
        if not drive_client or not drive_client.is_authenticated():
            return None
        
        # Buscar carpeta de jugadores dentro de la carpeta del equipo
        folders = drive_client.list_folders_in_folder(drive_id)
        jugadores_folder_id = None
        
        for folder in folders:
            if folder['name'].lower() in ['jugadores', 'players']:
                jugadores_folder_id = folder['id']
                break
        
        if not jugadores_folder_id:
            return None
        
        # Crear carpeta de cache para imágenes de este equipo
        team_images_cache_dir = DRIVE_CACHE_DIR / team_slug / "jugadores"
        team_images_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Normalizar nombre del archivo
        normalized_name = player_name.lower()
        
        # Buscar en cache primero
        cached_image_path = team_images_cache_dir / player_name
        if cached_image_path.exists():
            file_age_hours = (time.time() - cached_image_path.stat().st_mtime) / 3600
            if file_age_hours < CACHE_EXPIRY_HOURS:
                return cached_image_path
        
        # Si no está en cache, buscar en Google Drive
        image_files = drive_client.list_files_in_folder(jugadores_folder_id, 'png')
        image_files.extend(drive_client.list_files_in_folder(jugadores_folder_id, 'jpg'))
        image_files.extend(drive_client.list_files_in_folder(jugadores_folder_id, 'jpeg'))
        
        # Buscar el archivo específico
        target_file = None
        for image_file in image_files:
            if image_file['name'].lower() == normalized_name:
                target_file = image_file
                break
        
        if not target_file:
            return None
        
        # Descargar la imagen
        image_path = team_images_cache_dir / target_file['name']
        success = drive_client.download_file(target_file['id'], image_path)
        
        if success and image_path.exists():
            return image_path
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error obteniendo imagen del jugador {player_name} del equipo {team_name}: {str(e)}")
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


def get_team_report_path_by_drive_id(team_name: str, team_slug: str, drive_id: str) -> Optional[Path]:
    """
    Obtiene la ruta del informe de cualquier equipo desde Google Drive basándose en su drive_id
    
    Args:
        team_name: Nombre del equipo 
        team_slug: Slug del equipo (para cache)
        drive_id: ID de la carpeta del equipo en Google Drive
    
    Returns:
        Path al archivo del informe o None si no está disponible
    """
    try:
        drive_client = get_drive_client()
        if not drive_client or not drive_client.is_authenticated():
            return None
        
        # Crear carpeta de cache para este equipo específico
        team_cache_dir = DRIVE_CACHE_DIR / team_slug
        team_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Ruta del archivo en cache
        cached_file = team_cache_dir / f"{team_slug}.pdf"
        
        # Verificar si el archivo en cache es válido (menos de CACHE_EXPIRY_HOURS horas)
        if cached_file.exists():
            file_age_hours = (time.time() - cached_file.stat().st_mtime) / 3600
            if file_age_hours < CACHE_EXPIRY_HOURS:
                return cached_file
        
        # Buscar archivo PDF del equipo en Google Drive
        files = drive_client.list_files_in_folder(drive_id, 'pdf')
        
        team_pdf = None
        for file in files:
            file_name_lower = file['name'].lower()
            # Buscar archivos PDF que puedan ser el informe del equipo
            if (team_slug.lower() in file_name_lower or 
                'informe' in file_name_lower or 
                'report' in file_name_lower or
                file_name_lower.endswith('.pdf')):
                team_pdf = file
                break
        
        if not team_pdf:
            return None
        
        # Descargar el archivo directamente a la ruta de cache
        success = drive_client.download_file(team_pdf['id'], cached_file)
        if not success:
            return None
        
        return cached_file
        
    except Exception as e:
        st.error(f"❌ Error cargando informe de {team_name}: {str(e)}")
        return None


def load_players_by_drive_id(team_name: str, team_slug: str, drive_id: str) -> List[Dict[str, Any]]:
    """
    Carga la lista de jugadores de cualquier equipo desde Google Drive basándose en su drive_id
    
    Args:
        team_name: Nombre del equipo
        team_slug: Slug del equipo (para cache)
        drive_id: ID de la carpeta del equipo en Google Drive
    
    Returns:
        Lista de diccionarios con datos de jugadores
    """
    try:
        drive_client = get_drive_client()
        if not drive_client or not drive_client.is_authenticated():
            return []
        
        # Buscar carpeta de jugadores dentro de la carpeta del equipo
        folders = drive_client.list_folders_in_folder(drive_id)
        jugadores_folder_id = None
        
        for folder in folders:
            if folder['name'].lower() in ['jugadores', 'players']:
                jugadores_folder_id = folder['id']
                break
        
        if not jugadores_folder_id:
            return []
        
        # Crear carpeta de cache para imágenes de este equipo
        team_images_cache_dir = DRIVE_CACHE_DIR / team_slug / "jugadores"
        team_images_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Obtener lista de archivos de imagen en la carpeta de jugadores desde Drive
        image_files = drive_client.list_files_in_folder(jugadores_folder_id, 'png')
        image_files.extend(drive_client.list_files_in_folder(jugadores_folder_id, 'jpg'))
        image_files.extend(drive_client.list_files_in_folder(jugadores_folder_id, 'jpeg'))
        
        # IMPORTANTE: Si no hay archivos en Drive, intentar usar el caché local
        if not image_files:
            # Buscar imágenes en caché local
            cached_images = []
            if team_images_cache_dir.exists():
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    cached_images.extend(list(team_images_cache_dir.glob(ext)))
            
            if not cached_images:
                return []
            
            # Usar solo imágenes del caché local
            available_images = {}
            for cached_path in cached_images:
                # Verificar que el archivo no esté muy antiguo
                file_age_hours = (time.time() - cached_path.stat().st_mtime) / 3600
                if file_age_hours < CACHE_EXPIRY_HOURS * 7:  # Cache más largo para equipos externos
                    available_images[cached_path.name] = cached_path
        else:
            # Descargar imágenes que no estén en cache
            available_images = {}
            for image_file in image_files:
                image_filename = image_file['name']
                cached_image_path = team_images_cache_dir / image_filename
                
                # Verificar si la imagen está en cache y es válida
                if cached_image_path.exists():
                    file_age_hours = (time.time() - cached_image_path.stat().st_mtime) / 3600
                    if file_age_hours < CACHE_EXPIRY_HOURS:
                        available_images[image_filename] = cached_image_path
                        continue
                
                # Descargar imagen
                success = drive_client.download_file(image_file['id'], cached_image_path)
                if success:
                    available_images[image_filename] = cached_image_path
        
        if not available_images:
            return []
        
        # Cargar datos del Excel
        if not EXCEL_FILE.exists():
            # Si no hay Excel, crear jugadores basados solo en los nombres de archivo
            players_data = []
            for image_filename in available_images.keys():
                image_base = image_filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
                
                # Intentar extraer nombre del archivo
                if '_' in image_base:
                    parts = image_base.split('_')
                    surnames = parts[0].replace('_', ' ')
                    name = parts[1] if len(parts) > 1 else 'N'
                else:
                    surnames = image_base
                    name = 'N'
                
                players_data.append({
                    'name': name,
                    'surnames': surnames,
                    'full_name': f"{name} {surnames}",
                    'position': '',
                    'height': '',
                    'age': '',
                    'team': team_name,
                    'image_path': str(available_images[image_filename]),
                    'image_filename': image_filename
                })
            
            return players_data
        
        # Cargar Excel y buscar coincidencias
        df = pd.read_excel(EXCEL_FILE)
        df = df.fillna("")
        
        # INVERTIR LA LÓGICA: partir de las imágenes en Drive y buscar en Excel
        players_data = []
        used_players = set()
        
        for image_filename, image_path in available_images.items():
            # Extraer información del nombre del archivo y normalizar (quitar tildes)
            image_base = image_filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
            
            # Quitar tildes antes de convertir a mayúsculas para matching
            tilde_map = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
                        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ü': 'U'}
            for src, tgt in tilde_map.items():
                image_base = image_base.replace(src, tgt)
            
            image_base = image_base.upper()
            
            # Buscar coincidencia en el Excel (buscar en cualquier equipo, no solo el actual)
            matching_player = None
            matching_index = None
            
            for idx, row in df.iterrows():
                if idx in used_players:
                    continue
                    
                full_name = row.get('JUGADOR', '')
                if not full_name:
                    continue
                
                # Extraer apellidos y nombre del Excel
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
                
                # Normalizar para comparación (mantener ñ, solo quitar tildes de vocales)
                surnames_normalized = surnames.upper().replace(' ', '_').replace(',', '')
                # Quitar tildes de vocales pero MANTENER Ñ
                for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                    surnames_normalized = surnames_normalized.replace(src, tgt)
                
                name_normalized = name.upper()
                for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                    name_normalized = name_normalized.replace(src, tgt)
                
                # Verificar coincidencias
                expected_pattern = f"{surnames_normalized}_{name_normalized}"
                expected_pattern_initial = f"{surnames_normalized}_{name_normalized[0]}" if len(name_normalized) > 1 else expected_pattern
                
                if (image_base == expected_pattern or 
                    image_base == expected_pattern_initial or
                    image_base.startswith(surnames_normalized + '_')):
                    matching_player = row
                    matching_index = idx
                    break
            
            if matching_player is not None and matching_index is not None:
                used_players.add(matching_index)
                
                # Extraer datos del Excel
                full_name = matching_player['JUGADOR']
                
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
                
                # Extraer dorsal y otros datos del Excel
                dorsal = int(matching_player['DORSAL']) if pd.notna(matching_player['DORSAL']) else 0
                imagen_url = matching_player.get('IMAGEN', '')
                
                # Crear slug único usando nombre del archivo
                slug = image_filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').lower()
                
                players_data.append({
                    'number': dorsal,
                    'name': name,
                    'surnames': surnames,
                    'slug': slug,
                    'full_name': full_name,
                    'team': team_name,  # Usar el nombre del equipo actual, no del Excel
                    'image_url': imagen_url,  # URL del Excel
                    'image_filename': image_filename,
                    'image_path': str(image_path),  # Ruta local de la imagen
                    'position': matching_player.get('POSICION', ''),
                    'height': matching_player.get('ALTURA', ''),
                    'age': matching_player.get('EDAD', ''),
                    'points': int(matching_player['PUNTOS']) if pd.notna(matching_player['PUNTOS']) else 0,
                    'minutes': float(matching_player['MINUTOS JUGADOS']) if pd.notna(matching_player['MINUTOS JUGADOS']) else 0.0,
                    'games_played': int(matching_player['PJ']) if pd.notna(matching_player['PJ']) else 0,
                    'bio_url': matching_player.get('BIO_URL', ''),
                    'photo_url': matching_player.get('FOTO_URL', '')
                })
            else:
                # No se encontró en Excel, crear entrada básica
                print(f"\n❌ NO MATCH para archivo: {image_filename}")
                print(f"   📄 Nombre archivo original: {image_filename}")
                print(f"   🔤 Image base (uppercase): '{image_base}'")
                print(f"   🔍 Buscando coincidencias en Excel para equipo: {team_name}")
                
                # Buscar jugadores similares en el Excel del equipo actual
                team_players_in_excel = df[df['EQUIPO'].str.contains(team_name, na=False, case=False)]
                print(f"   👥 Jugadores encontrados en Excel para '{team_name}': {len(team_players_in_excel)}")
                
                if len(team_players_in_excel) > 0:
                    print(f"   📋 TODOS los jugadores del equipo en Excel:")
                    for idx, row in team_players_in_excel.iterrows():
                        jugador_name = row.get('JUGADOR', 'N/A')
                        # Mostrar cómo se normalizaría
                        if ',' in jugador_name:
                            parts = jugador_name.split(',', 1)
                            surnames = parts[0].strip()
                            name = parts[1].strip() if len(parts) > 1 else ""
                            name_full = name  # Guardar nombre completo
                            name = name.split()[0] if name else "N"
                            surnames_norm = surnames.upper().replace(' ', '_')
                            for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                                surnames_norm = surnames_norm.replace(src, tgt)
                            name_norm = name.upper()
                            for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                                name_norm = name_norm.replace(src, tgt)
                            # También mostrar pattern con nombre completo
                            name_full_norm = name_full.upper().replace(' ', '_')
                            for src, tgt in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U')]:
                                name_full_norm = name_full_norm.replace(src, tgt)
                            pattern = f"{surnames_norm}_{name_norm}"
                            pattern_full = f"{surnames_norm}_{name_full_norm}"
                            print(f"      - {jugador_name}")
                            print(f"        → Pattern inicial: '{pattern}'")
                            print(f"        → Pattern completo: '{pattern_full}'")
                
                image_base_clean = image_filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
                
                if '_' in image_base_clean:
                    parts = image_base_clean.split('_')
                    surnames = parts[0].replace('_', ' ')
                    name = parts[1] if len(parts) > 1 else 'N'
                else:
                    surnames = image_base_clean
                    name = 'N'
                
                # Crear slug único
                slug = image_base_clean.lower()
                
                players_data.append({
                    'number': 0,  # Sin dorsal
                    'name': name,
                    'surnames': surnames,
                    'slug': slug,
                    'full_name': f"{name} {surnames}",
                    'team': team_name,
                    'image_url': '',  # Vacío para usar imagen local
                    'image_filename': image_filename,
                    'image_path': str(image_path),  # Ruta local de la imagen
                    'position': '',
                    'height': '',
                    'age': '',
                    'points': 0,
                    'minutes': 0.0,
                    'games_played': 0,
                    'bio_url': '',
                    'photo_url': ''
                })
        
        return players_data
        
    except Exception as e:
        st.error(f"❌ Error cargando jugadores de {team_name}: {str(e)}")
        return []