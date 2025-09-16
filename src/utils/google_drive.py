# src/utils/google_drive.py
# -*- coding: utf-8 -*-
"""
Cliente de Google Drive para descargar archivos de scouting
"""
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import streamlit as st

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False


class GoogleDriveClient:
    """Cliente para interactuar con Google Drive API"""
    
    def __init__(self, credentials_path: str = "credentials/google_drive_credentials.json"):
        self.credentials_path = Path(credentials_path)
        self.service = None
        self._authenticated = False
        
        if not GOOGLE_DRIVE_AVAILABLE:
            return
            
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google Drive usando credenciales de cuenta de servicio"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
            credentials = None
            
            # Intentar Streamlit Secrets primero (para producción)
            try:
                if hasattr(st, 'secrets') and "google_credentials" in st.secrets:
                    credentials_info = dict(st.secrets["google_credentials"])
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_info, 
                        scopes=SCOPES
                    )
            except Exception:
                # Si falla secrets, continuar con archivo local
                pass
            
            # Si no hay secrets, usar archivo local (para desarrollo)
            if credentials is None and self.credentials_path.exists():
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        str(self.credentials_path), 
                        scopes=SCOPES
                    )
                except Exception as e:
                    return
            
            # Si no se encontraron credenciales
            if credentials is None:
                return
            
            # Construir el servicio
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Verificar que funciona
            about = self.service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Usuario')
            
            self._authenticated = True
            
        except Exception as e:
            self._authenticated = False
    
    def is_authenticated(self) -> bool:
        """Verifica si el cliente está autenticado"""
        return self._authenticated and self.service is not None
    
    def list_files_in_folder(self, folder_id: str, file_type: str = None) -> List[Dict[str, Any]]:
        """
        Lista archivos en una carpeta específica
        
        Args:
            folder_id: ID de la carpeta en Google Drive
            file_type: Tipo de archivo a filtrar ('pdf', 'png', etc.)
        
        Returns:
            Lista de diccionarios con información de archivos
        """
        if not self.is_authenticated():
            return []
        
        try:
            # Construir query de búsqueda
            query = f"'{folder_id}' in parents and trashed=false"
            if file_type:
                if file_type.lower() == 'pdf':
                    query += " and mimeType='application/pdf'"
                elif file_type.lower() in ['png', 'jpg', 'jpeg']:
                    query += " and (mimeType='image/png' or mimeType='image/jpeg')"
            
            # Obtener lista de archivos
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            return []
    
    def list_folders_in_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Lista carpetas dentro de una carpeta específica
        
        Args:
            folder_id: ID de la carpeta padre
        
        Returns:
            Lista de diccionarios con información de carpetas
        """
        if not self.is_authenticated():
            return []
        
        try:
            # Buscar solo carpetas
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            return []
    
    def download_file(self, file_id: str, destination_path: Path) -> bool:
        """
        Descarga un archivo de Google Drive
        
        Args:
            file_id: ID del archivo en Google Drive
            destination_path: Ruta local donde guardar el archivo
        
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        if not self.is_authenticated():
            return False
        
        try:
            # Crear directorio si no existe
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Descargar archivo
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Escribir archivo a disco
            with open(destination_path, 'wb') as f:
                f.write(fh.getvalue())
            
            return True
            
        except Exception as e:
            return False
    
    def find_team_folder(self, root_folder_id: str, team_name: str) -> Optional[str]:
        """
        Busca la carpeta de un equipo específico
        
        Args:
            root_folder_id: ID de la carpeta raíz
            team_name: Nombre del equipo a buscar
        
        Returns:
            ID de la carpeta del equipo o None si no se encuentra
        """
        folders = self.list_folders_in_folder(root_folder_id)
        
        for folder in folders:
            if folder['name'].upper() == team_name.upper():
                return folder['id']
        
        return None
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada de un archivo
        
        Args:
            file_id: ID del archivo
        
        Returns:
            Diccionario con información del archivo o None si hay error
        """
        if not self.is_authenticated():
            return None
        
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, parents"
            ).execute()
            
            return file_info
            
        except Exception as e:
            return None


# Instancia global del cliente (singleton)
_drive_client = None

def get_drive_client() -> Optional[GoogleDriveClient]:
    """Obtiene la instancia global del cliente de Google Drive"""
    global _drive_client
    
    if _drive_client is None:
        _drive_client = GoogleDriveClient()
    
    if not _drive_client.is_authenticated():
        return None
        
    return _drive_client