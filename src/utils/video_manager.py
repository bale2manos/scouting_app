# src/utils/video_manager.py
# -*- coding: utf-8 -*-
"""
Gestor de videos de scouting desde Google Drive
"""
import streamlit as st
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

from ..utils.google_drive import GoogleDriveClient

logger = logging.getLogger(__name__)

# Extensiones de video soportadas
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']

class VideoManager:
    """Gestor de videos de scouting almacenados en Google Drive"""
    
    def __init__(self):
        self.drive_client = GoogleDriveClient()
    
    def _is_video_file(self, filename: str) -> bool:
        """Verifica si un archivo es un video basado en su extensión"""
        return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)
    
    def _get_folder_id(self, folder_name: str) -> Optional[str]:
        """Obtiene el ID de una carpeta en Google Drive"""
        try:
            if not self.drive_client.is_authenticated():
                return None
            
            service = self.drive_client.service
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo ID de carpeta {folder_name}: {e}")
            return None
    
    def _get_subfolder_id(self, parent_folder_id: str, subfolder_name: str) -> Optional[str]:
        """Obtiene el ID de una subcarpeta dentro de una carpeta padre"""
        try:
            if not self.drive_client.is_authenticated():
                return None
            
            service = self.drive_client.service
            query = f"'{parent_folder_id}' in parents and name='{subfolder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo ID de subcarpeta {subfolder_name}: {e}")
            return None
    
    def _list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """Lista todos los archivos en una carpeta de Google Drive"""
        try:
            if not self.drive_client.is_authenticated():
                return []
            
            service = self.drive_client.service
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query, 
                fields="files(id, name, size, createdTime, modifiedTime, mimeType)",
                orderBy="name"
            ).execute()
            
            files = results.get('files', [])
            return files
            
        except Exception as e:
            logger.error(f"Error listando archivos en carpeta {folder_id}: {e}")
            return []
    
    def get_team_videos(self, team_name: str) -> List[Dict]:
        """Obtiene videos del equipo desde la carpeta videos/"""
        try:
            # Obtener ID de la carpeta del equipo
            team_folder_id = self._get_folder_id(team_name)
            if not team_folder_id:
                return []
            
            # Obtener ID de la subcarpeta videos/
            videos_folder_id = self._get_subfolder_id(team_folder_id, 'videos')
            if not videos_folder_id:
                return []
            
            # Listar archivos de video
            files = self._list_files_in_folder(videos_folder_id)
            videos = [f for f in files if self._is_video_file(f['name'])]
            
            # Agregar información adicional
            for video in videos:
                video['type'] = 'team'
                video['team_name'] = team_name
                video['url'] = f"https://drive.google.com/file/d/{video['id']}/view"
                video['embed_url'] = f"https://drive.google.com/file/d/{video['id']}/preview"
            
            return videos
            
        except Exception as e:
            logger.error(f"Error obteniendo videos del equipo {team_name}: {e}")
            return []
    
    def get_team_player_videos(self, team_name: str, player_report_names: List[str] = None) -> List[Dict]:
        """Obtiene videos de jugadores del equipo desde la carpeta jugadores/"""
        try:
            # Obtener ID de la carpeta del equipo
            team_folder_id = self._get_folder_id(team_name)
            if not team_folder_id:
                logger.warning(f"No se encontró la carpeta del equipo: {team_name}")
                return []

            # Obtener ID de la subcarpeta jugadores/
            players_folder_id = self._get_subfolder_id(team_folder_id, 'jugadores')
            if not players_folder_id:
                logger.warning(f"No se encontró la subcarpeta 'jugadores' para el equipo: {team_name}")
                return []

            # Listar archivos de video
            files = self._list_files_in_folder(players_folder_id)
            # Depuración temporal eliminada: evitar prints en producción
            videos = [f for f in files if self._is_video_file(f['name'])]

            # Filtrar videos que coincidan con los nombres de los informes
            # Hacer la comparación siempre en MAYÚSCULAS para evitar problemas
            # de case-sensitivity en los nombres de los archivos.
            if player_report_names:
                report_basenames_upper = {Path(name).stem.upper() for name in player_report_names}
                videos = [v for v in videos if Path(v['name']).stem.upper() in report_basenames_upper]

            # Agregar información adicional
            for video in videos:
                video['url'] = f"https://drive.google.com/file/d/{video['id']}/view"
                video['embed_url'] = f"https://drive.google.com/file/d/{video['id']}/preview"

            return videos

        except Exception as e:
            logger.error(f"Error obteniendo videos de jugadores del equipo {team_name}: {e}")
            return []
    
    def get_player_video(self, team_name: str, player_report_name: str) -> Optional[Dict]:
        """Obtiene el video específico de un jugador del equipo rival"""
        try:
            # Buscar videos filtrando por el nombre del informe
            team_player_videos = self.get_team_player_videos(team_name, player_report_names=[player_report_name])
            if team_player_videos:
                return team_player_videos[0]
            return None
        except Exception as e:
            logger.error(f"Error obteniendo video del jugador {player_report_name} del equipo {team_name}: {e}")
            return None
    
    def get_user_videos(self, username: str) -> List[Dict]:
        """Obtiene videos del usuario desde la carpeta PINTOBASKET/"""
        try:
            # Obtener ID de la carpeta PINTOBASKET
            pintobasket_folder_id = self._get_folder_id('PINTOBASKET')
            if not pintobasket_folder_id:
                return []
            
            # Listar archivos de video
            files = self._list_files_in_folder(pintobasket_folder_id)
            
            # Filtrar videos que correspondan al usuario
            user_videos = []
            for file in files:
                if self._is_video_file(file['name']):
                    # Verificar si el nombre del archivo coincide con el username
                    file_name = Path(file['name']).stem.lower()
                    if username.lower() == file_name:
                        file['type'] = 'user'
                        file['username'] = username
                        file['url'] = f"https://drive.google.com/file/d/{file['id']}/view"
                        file['embed_url'] = f"https://drive.google.com/file/d/{file['id']}/preview"
                        user_videos.append(file)
            
            return user_videos
            
        except Exception as e:
            logger.error(f"Error obteniendo videos del usuario {username}: {e}")
            return []
    
    def get_all_teams_with_videos(self) -> List[str]:
        """Obtiene lista de equipos que tienen videos (excluyendo PINTOBASKET)"""
        try:
            if not self.drive_client.is_authenticated():
                return []
            
            service = self.drive_client.service
            
            # Buscar todas las carpetas en el drive (que no sean PINTOBASKET)
            query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            teams_with_videos = []
            for folder in folders:
                folder_name = folder['name']
                
                # Excluir PINTOBASKET
                if folder_name.upper() == 'PINTOBASKET':
                    continue
                
                # Verificar si tiene subcarpetas videos/ o jugadores/ con contenido
                videos_folder_id = self._get_subfolder_id(folder['id'], 'videos')
                players_folder_id = self._get_subfolder_id(folder['id'], 'jugadores')
                
                has_videos = False
                if videos_folder_id:
                    videos = self._list_files_in_folder(videos_folder_id)
                    if any(self._is_video_file(v['name']) for v in videos):
                        has_videos = True
                
                if players_folder_id and not has_videos:
                    player_videos = self._list_files_in_folder(players_folder_id)
                    if any(self._is_video_file(v['name']) for v in player_videos):
                        has_videos = True
                
                if has_videos:
                    teams_with_videos.append(folder_name)
            
            return sorted(teams_with_videos)
            
        except Exception as e:
            logger.error(f"Error obteniendo equipos con videos: {e}")
            return []
    
    def format_video_size(self, size_bytes: str) -> str:
        """Formatea el tamaño del video en formato legible"""
        try:
            size = int(size_bytes)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except (ValueError, TypeError):
            return "Tamaño desconocido"
    
    def format_video_date(self, date_string: str) -> str:
        """Formatea la fecha del video"""
        try:
            from datetime import datetime
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date.strftime('%d/%m/%Y %H:%M')
        except:
            return "Fecha desconocida"
    
    def mark_videos_as_unseen_if_changed(self, username: str):
        """Marca los videos como no vistos si se detectan cambios."""
        try:
            # Obtener videos actuales del usuario
            videos = self.get_user_videos(username)
            if not videos:
                return

            # Obtener estado actual de los videos desde la base de datos
            from ..auth.db_logger import DatabaseLogger
            logger = DatabaseLogger()
            current_video_names = {video['name'] for video in videos}
            logged_video_names = logger.get_logged_video_names(username)

            # Detectar cambios
            new_videos = current_video_names - logged_video_names
            if new_videos:
                logger.mark_videos_as_unseen(username, new_videos)

        except Exception as e:
            logger.error(f"Error marcando videos como no vistos para {username}: {e}")


# Instancia global para usar en toda la aplicación
video_manager = VideoManager()