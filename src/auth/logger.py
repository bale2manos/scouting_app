# src/auth/logger.py
# -*- coding: utf-8 -*-
"""
Sistema de logging de actividad para el sistema de autenticación
"""
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any


class ActivityLogger:
    """Registra actividad de usuarios y accesos"""
    
    def __init__(self, 
                 access_logs_file: str = "data/auth/access_logs.json",
                 stats_file: str = "data/auth/user_stats.json"):
        self.access_logs_file = Path(access_logs_file)
        self.stats_file = Path(stats_file)
        
        # Cargar datos existentes
        self.access_logs = self._load_access_logs()
        self.stats_data = self._load_stats()
    
    def _load_access_logs(self) -> Dict:
        """Carga logs de acceso desde archivo"""
        try:
            if self.access_logs_file.exists():
                with open(self.access_logs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                initial_data = {
                    "access_logs": [],
                    "created_at": datetime.now().isoformat()
                }
                self._save_access_logs(initial_data)
                return initial_data
        except Exception as e:
            print(f"Error loading access logs: {e}")
            return {
                "access_logs": [],
                "created_at": datetime.now().isoformat()
            }
    
    def _save_access_logs(self, data: Dict = None) -> bool:
        """Guarda logs de acceso"""
        try:
            if data is None:
                data = self.access_logs
            
            # Crear directorio si no existe
            self.access_logs_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.access_logs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.access_logs = data
            return True
        except Exception as e:
            print(f"Error saving access logs: {e}")
            return False
    
    def _load_stats(self) -> Dict:
        """Carga estadísticas desde archivo"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                initial_data = {
                    "stats": {
                        "total_logins": 0,
                        "unique_users_today": 0,
                        "page_views": {},
                        "popular_teams": {},
                        "active_sessions": 0
                    },
                    "user_stats": {},
                    "daily_stats": {},
                    "last_updated": datetime.now().isoformat()
                }
                self._save_stats(initial_data)
                return initial_data
        except Exception as e:
            print(f"Error loading stats: {e}")
            return {
                "stats": {
                    "total_logins": 0,
                    "unique_users_today": 0,
                    "page_views": {},
                    "popular_teams": {},
                    "active_sessions": 0
                },
                "user_stats": {},
                "daily_stats": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_stats(self, data: Dict = None) -> bool:
        """Guarda estadísticas"""
        try:
            if data is None:
                data = self.stats_data
            
            data["last_updated"] = datetime.now().isoformat()
            
            # Crear directorio si no existe
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.stats_data = data
            return True
        except Exception as e:
            print(f"Error saving stats: {e}")
            return False
    
    def log_access(self, username: str, action: str, success: bool = True,
                   user_agent: str = "", ip_address: str = "", 
                   additional_data: Dict = None) -> None:
        """
        Registra un acceso (login, logout, intento fallido)
        
        Args:
            username: Nombre del usuario
            action: Tipo de acción (login, logout, login_failed)
            success: Si la acción fue exitosa
            user_agent: User agent del navegador
            ip_address: Dirección IP
            additional_data: Datos adicionales
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "action": action,
            "success": success,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "additional_data": additional_data or {}
        }
        
        # Agregar al log
        self.access_logs["access_logs"].append(log_entry)
        
        # Limpiar logs antiguos (mantener últimos 1000)
        if len(self.access_logs["access_logs"]) > 1000:
            self.access_logs["access_logs"] = self.access_logs["access_logs"][-1000:]
        
        # Actualizar estadísticas
        if action == "login" and success:
            self._update_login_stats(username)
        
        # Guardar
        self._save_access_logs()
    
    def log_activity(self, username: str, action: str, page: str = "", 
                    additional_data: Dict = None) -> None:
        """
        Registra actividad del usuario dentro de la app
        
        Args:
            username: Nombre del usuario
            action: Tipo de acción (page_view, download_report, search, etc.)
            page: Página visitada
            additional_data: Datos adicionales (team_name, search_query, etc.)
        """
        # Registrar en access logs también para tener historial completo
        self.log_access(
            username=username,
            action=action,
            success=True,
            additional_data=additional_data or {}
        )
        
        # Actualizar estadísticas de usuario
        today = date.today().isoformat()
        
        # Inicializar estadísticas del usuario si no existen
        if username not in self.stats_data["user_stats"]:
            self.stats_data["user_stats"][username] = {
                "total_sessions": 0,
                "page_views": {},
                "actions": {},
                "last_activity": None,
                "first_activity": datetime.now().isoformat()
            }
        
        user_stats = self.stats_data["user_stats"][username]
        user_stats["last_activity"] = datetime.now().isoformat()
        
        # Determinar la etiqueta para estadísticas
        # Si hay una descripción específica, usarla para stats más descriptivos
        additional_data = additional_data or {}
        description = additional_data.get("description", "")
        
        # Para estadísticas de conteo, usar una versión simplificada de la descripción o la acción
        stat_label = action
        if description:
            if "informe del equipo:" in description:
                stat_label = "Visualización de informes de equipos" if "Visualizó" in description else "Descarga de informes de equipos"
            elif "informe del jugador:" in description:
                stat_label = "Visualización de informes de jugadores" if "Visualizó" in description else "Descarga de informes de jugadores"
        
        # Actualizar contadores de acciones con etiqueta descriptiva
        if stat_label not in user_stats["actions"]:
            user_stats["actions"][stat_label] = 0
        user_stats["actions"][stat_label] += 1
        
        # Actualizar páginas visitadas
        if page and action == "page_view":
            if page not in user_stats["page_views"]:
                user_stats["page_views"][page] = 0
            user_stats["page_views"][page] += 1
            
            # Actualizar estadísticas globales de páginas
            if page not in self.stats_data["stats"]["page_views"]:
                self.stats_data["stats"]["page_views"][page] = 0
            self.stats_data["stats"]["page_views"][page] += 1
        
        # Procesar datos adicionales específicos
        self._process_additional_activity_data(action, additional_data or {})
        
        # Actualizar estadísticas diarias
        if today not in self.stats_data["daily_stats"]:
            self.stats_data["daily_stats"][today] = {
                "unique_users": set(),
                "total_page_views": 0,
                "actions": {}
            }
        
        daily_stats = self.stats_data["daily_stats"][today]
        
        # Convertir set a lista para JSON (y viceversa)
        if isinstance(daily_stats["unique_users"], list):
            daily_stats["unique_users"] = set(daily_stats["unique_users"])
        
        daily_stats["unique_users"].add(username)
        
        if action == "page_view":
            daily_stats["total_page_views"] += 1
        
        if action not in daily_stats["actions"]:
            daily_stats["actions"][action] = 0
        daily_stats["actions"][action] += 1
        
        # Convertir set de vuelta a lista para JSON
        daily_stats["unique_users"] = list(daily_stats["unique_users"])
        
        # Actualizar estadísticas generales
        if action == "page_view":
            # Manejar datos adicionales como team_name
            if additional_data and "team_name" in additional_data:
                team_name = additional_data["team_name"]
                if team_name not in self.stats_data["stats"]["popular_teams"]:
                    self.stats_data["stats"]["popular_teams"][team_name] = 0
                self.stats_data["stats"]["popular_teams"][team_name] += 1
        
        # Guardar
        self._save_stats()
    
    def _update_login_stats(self, username: str) -> None:
        """Actualiza estadísticas de login"""
        # Incrementar login total
        self.stats_data["stats"]["total_logins"] += 1
        
        # Actualizar estadísticas del usuario
        if username not in self.stats_data["user_stats"]:
            self.stats_data["user_stats"][username] = {
                "total_sessions": 0,
                "page_views": {},
                "actions": {},
                "last_activity": None,
                "first_activity": datetime.now().isoformat()
            }
        
        self.stats_data["user_stats"][username]["total_sessions"] += 1
        
        # Actualizar usuarios únicos hoy
        today = date.today().isoformat()
        if today not in self.stats_data["daily_stats"]:
            self.stats_data["daily_stats"][today] = {
                "unique_users": [],
                "total_page_views": 0,
                "actions": {}
            }
        
        unique_users = set(self.stats_data["daily_stats"][today]["unique_users"])
        unique_users.add(username)
        self.stats_data["daily_stats"][today]["unique_users"] = list(unique_users)
        self.stats_data["stats"]["unique_users_today"] = len(unique_users)
    
    def get_recent_access_logs(self, limit: int = 50) -> List[Dict]:
        """Obtiene los logs de acceso más recientes"""
        logs = self.access_logs.get("access_logs", [])
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_user_activity(self, username: str) -> Dict:
        """Obtiene la actividad de un usuario específico"""
        user_stats = self.stats_data["user_stats"].get(username, {})
        
        # Obtener logs de acceso del usuario
        user_access_logs = [
            log for log in self.access_logs.get("access_logs", [])
            if log["username"] == username
        ]
        
        return {
            "username": username,
            "stats": user_stats,
            "recent_access_logs": sorted(user_access_logs, 
                                       key=lambda x: x["timestamp"], 
                                       reverse=True)[:20]
        }
    
    def get_daily_stats(self, days: int = 7) -> Dict:
        """Obtiene estadísticas de los últimos días"""
        daily_stats = {}
        
        for i in range(days):
            target_date = date.today() - timedelta(days=i)
            date_str = target_date.isoformat()
            
            if date_str in self.stats_data["daily_stats"]:
                daily_stats[date_str] = self.stats_data["daily_stats"][date_str].copy()
                # Asegurar que unique_users sea un número
                if isinstance(daily_stats[date_str]["unique_users"], list):
                    daily_stats[date_str]["unique_users"] = len(daily_stats[date_str]["unique_users"])
            else:
                daily_stats[date_str] = {
                    "unique_users": 0,
                    "total_page_views": 0,
                    "actions": {}
                }
        
        return daily_stats
    
    def get_general_stats(self) -> Dict:
        """Obtiene estadísticas generales"""
        return {
            "total_logins": self.stats_data["stats"]["total_logins"],
            "unique_users_today": self.stats_data["stats"]["unique_users_today"],
            "total_users": len(self.stats_data["user_stats"]),
            "popular_pages": dict(sorted(
                self.stats_data["stats"]["page_views"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "popular_teams": dict(sorted(
                self.stats_data["stats"]["popular_teams"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "last_updated": self.stats_data["last_updated"]
        }
    
    def _process_additional_activity_data(self, action: str, additional_data: Dict) -> None:
        """Procesa datos adicionales específicos según el tipo de acción"""
        
        # Tracking de equipos populares
        if action in ["view_team", "download_team_report"] and "team_name" in additional_data:
            team_name = additional_data["team_name"]
            if "popular_teams" not in self.stats_data["stats"]:
                self.stats_data["stats"]["popular_teams"] = {}
            
            if team_name not in self.stats_data["stats"]["popular_teams"]:
                self.stats_data["stats"]["popular_teams"][team_name] = 0
            self.stats_data["stats"]["popular_teams"][team_name] += 1
        
        # Tracking de jugadores populares
        if action in ["view_player", "download_player_report"] and "player_name" in additional_data:
            player_name = additional_data["player_name"]
            if "popular_players" not in self.stats_data["stats"]:
                self.stats_data["stats"]["popular_players"] = {}
            
            if player_name not in self.stats_data["stats"]["popular_players"]:
                self.stats_data["stats"]["popular_players"][player_name] = 0
            self.stats_data["stats"]["popular_players"][player_name] += 1
        
        # Tracking de búsquedas
        if action == "search" and "search_query" in additional_data:
            if "search_queries" not in self.stats_data["stats"]:
                self.stats_data["stats"]["search_queries"] = {}
            
            query = additional_data["search_query"].lower().strip()
            if query:
                if query not in self.stats_data["stats"]["search_queries"]:
                    self.stats_data["stats"]["search_queries"][query] = 0
                self.stats_data["stats"]["search_queries"][query] += 1
    
    # Funciones de logging específicas para facilitar el uso
    def log_team_view(self, username: str, team_name: str) -> None:
        """Registra la visualización de un equipo"""
        self.log_activity(
            username=username,
            action="view_team",
            page="team",
            additional_data={"team_name": team_name}
        )
    
    def log_player_view(self, username: str, player_name: str) -> None:
        """Registra la visualización de un jugador"""
        self.log_activity(
            username=username,
            action="view_player", 
            page="player",
            additional_data={"player_name": player_name}
        )
    
    def log_download(self, username: str, file_type: str, file_name: str) -> None:
        """Registra una descarga de archivo"""
        self.log_activity(
            username=username,
            action="download",
            additional_data={
                "file_type": file_type,
                "file_name": file_name
            }
        )
    
    def log_search(self, username: str, search_query: str, search_type: str = "general") -> None:
        """Registra una búsqueda"""
        self.log_activity(
            username=username,
            action="search",
            additional_data={
                "search_query": search_query,
                "search_type": search_type
            }
        )
    
    def log_navigation(self, username: str, from_page: str, to_page: str) -> None:
        """Registra navegación entre páginas"""
        self.log_activity(
            username=username,
            action="navigation",
            additional_data={
                "from_page": from_page,
                "to_page": to_page
            }
        )
    
    def log_button_click(self, username: str, button_name: str, page: str = "") -> None:
        """Registra clicks en botones específicos"""
        self.log_activity(
            username=username,
            action="button_click",
            page=page,
            additional_data={"button_name": button_name}
        )
    
    def log_form_submission(self, username: str, form_name: str, page: str = "") -> None:
        """Registra envío de formularios"""
        self.log_activity(
            username=username,
            action="form_submission",
            page=page,
            additional_data={"form_name": form_name}
        )


# Importar timedelta para get_daily_stats
from datetime import timedelta