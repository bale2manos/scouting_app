# src/auth/db_logger.py
# -*- coding: utf-8 -*-
"""
Sistema de logging de actividades con base de datos PostgreSQL
Compatible con el sistema simplificado actual
"""
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging
import json

from .database import db_manager

db_logger = logging.getLogger(__name__)

class DatabaseLogger:
    """Sistema de logging usando PostgreSQL/Supabase"""
    
    def __init__(self):
        self.session_prefix = "db_log_"
    
    def _get_current_user(self) -> Optional[str]:
        """Obtiene el usuario actual desde session_state"""
        try:
            return st.session_state.get("username")
        except Exception:
            # Si session_state no está disponible, retornar None
            return None
    
    def _get_session_key(self, action: str, context: str = "") -> str:
        """Genera clave única para evitar duplicados por sesión"""
        base_key = f"{self.session_prefix}{action}"
        if context:
            base_key += f"_{context}"
        return base_key
    
    def _should_log(self, session_key: str) -> bool:
        """Verifica si se debe registrar la acción (evita duplicados)"""
        try:
            # Verificar si session_state está disponible y contiene la clave
            if hasattr(st.session_state, 'get') and st.session_state.get(session_key, False):
                return False
            
            # Marcar como procesado para evitar duplicados
            st.session_state[session_key] = True
            return True
        except Exception:
            # Si hay problemas con session_state, permitir el logging siempre
            return True
    
    def log_access(self, username: str, action: str, success: bool = True, 
                  additional_data: Dict = None) -> bool:
        """
        Registra un evento de acceso (login, logout, etc.)
        
        Args:
            username: Usuario que realiza la acción
            action: Tipo de acción (login, logout, login_failed, etc.)
            success: Si la acción fue exitosa
            additional_data: Datos adicionales en formato dict
        """
        try:
            conn = db_manager.get_connection()
            
            # Preparar datos adicionales como JSON
            extra_data = additional_data or {}
            extra_data.update({
                'success': success,
                'timestamp': datetime.now().isoformat(),
                'session_id': st.session_state.get('session_token', '')[:10] if st.session_state.get('session_token') else 'unknown'
            })
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO activity_logs (username, action, log_type, success, additional_data)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, action, 'access', success, json.dumps(extra_data, ensure_ascii=False)))
            
            conn.commit()
            return True
            
        except Exception as e:
            db_logger.error(f"Error registrando acceso para {username}: {e}")
            return False
    
    def log_activity(self, username: str, action: str, page: str = "", 
                    success: bool = True, additional_data: Dict = None) -> bool:
        """
        Registra una actividad general del usuario
        
        Args:
            username: Usuario que realiza la acción
            action: Tipo de acción (view_page, download_report, etc.)
            page: Página donde se realiza la acción
            success: Si la acción fue exitosa
            additional_data: Datos adicionales
        """
        # Evitar duplicados usando session_state
        session_key = self._get_session_key(action, page)
        if not self._should_log(session_key):
            return True  # Ya registrado en esta sesión
        
        try:
            conn = db_manager.get_connection()
            
            # Preparar datos adicionales
            extra_data = additional_data or {}
            extra_data.update({
                'page': page,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO activity_logs (username, action, log_type, success, additional_data)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, action, 'activity', success, json.dumps(extra_data, ensure_ascii=False)))
            
            conn.commit()
            return True
            
        except Exception as e:
            db_logger.error(f"Error registrando actividad para {username}: {e}")
            return False
    
    def log_report_view(self, report_type: str, report_name: str) -> bool:
        """
        Registra la visualización de un reporte
        
        Args:
            report_type: Tipo de reporte (team, player)
            report_name: Nombre del reporte/equipo/jugador
        """
        username = self._get_current_user()
        if not username:
            return False
        
        # Para visualizaciones, permitir múltiples registros pero evitar spam reciente
        session_key = self._get_session_key(f"view_{report_type}", report_name)
        
        # Solo verificar si ya se registró en los últimos 30 segundos
        import time
        current_time = time.time()
        last_log_key = f"{session_key}_last_time"
        
        try:
            last_log_time = st.session_state.get(last_log_key, 0)
            if current_time - last_log_time < 30:  # 30 segundos de cooldown
                return True  # Evitar spam
            
            st.session_state[last_log_key] = current_time
        except:
            pass  # Si hay problemas con session_state, continuar

        # Crear acción más corta que quepa en 50 caracteres
        if report_type == "team":
            action = f"Ver equipo: {report_name[:30]}"  # Máximo ~45 chars
        elif report_type == "player":
            action = f"Ver jugador: {report_name[:28]}"  # Máximo ~45 chars
        else:
            action = f"Ver informe: {report_name[:30]}"  # Máximo ~45 chars
        
        additional_data = {
            'report_type': report_type,
            'report_name': report_name,  # Guardamos el nombre completo aquí
            'action_detail': 'report_viewed'
        }
        
        return self.log_activity(username, action, 
                               page=f"{report_type}_report", 
                               additional_data=additional_data)
    
    def log_report_download(self, report_type: str, report_name: str) -> bool:
        """
        Registra la descarga de un reporte
        
        Args:
            report_type: Tipo de reporte (team, player)
            report_name: Nombre del reporte/equipo/jugador
        """
        username = self._get_current_user()
        if not username:
            return False
        
        # Para descargas, permitir múltiples registros con cooldown menor
        session_key = self._get_session_key(f"download_{report_type}_{report_name}")
        
        # Solo verificar si ya se registró en los últimos 10 segundos
        import time
        current_time = time.time()
        last_log_key = f"{session_key}_last_time"
        
        try:
            last_log_time = st.session_state.get(last_log_key, 0)
            if current_time - last_log_time < 10:  # 10 segundos de cooldown
                return True  # Evitar spam
            
            st.session_state[last_log_key] = current_time
        except:
            pass  # Si hay problemas con session_state, continuar

        # Crear acción más corta que quepa en 50 caracteres
        if report_type == "team":
            action = f"Descarga equipo: {report_name[:25]}"  # Máximo ~45 chars
        elif report_type == "player":
            action = f"Descarga jugador: {report_name[:23]}"  # Máximo ~45 chars
        else:
            action = f"Descarga: {report_name[:35]}"  # Máximo ~45 chars
        
        additional_data = {
            'report_type': report_type,
            'report_name': report_name,  # Guardamos el nombre completo aquí
            'action_detail': 'report_downloaded'
        }
        
        return self.log_activity(username, action, 
                               page=f"{report_type}_report",
                               additional_data=additional_data)
    
    def log_page_view(self, page_name: str, additional_data: Dict = None) -> bool:
        """
        Registra la visita a una página
        
        Args:
            page_name: Nombre de la página visitada
            additional_data: Datos adicionales
        """
        username = self._get_current_user()
        if not username:
            return False
        
        # Evitar duplicados por sesión
        session_key = self._get_session_key("page_view", page_name)
        if not self._should_log(session_key):
            return True
        
        extra_data = additional_data or {}
        extra_data['page_name'] = page_name
        
        return self.log_activity(username, 'page_view', page=page_name, 
                               additional_data=extra_data)
    
    def get_user_activity(self, username: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene el historial de actividad de un usuario
        Prioriza actividades reales sobre las migradas
        
        Args:
            username: Usuario del que obtener el historial
            limit: Número máximo de registros a devolver
        """
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT action, log_type, success, additional_data, created_at
                    FROM activity_logs
                    WHERE username = %s
                    ORDER BY 
                        CASE 
                            WHEN additional_data::jsonb->'migrated_from_json' = 'true' THEN 1 
                            ELSE 0 
                        END,
                        created_at DESC
                    LIMIT %s
                """, (username, limit))
                
                activities = []
                for row in cursor.fetchall():
                    try:
                        # Si additional_data es un dict, ya está parseado por psycopg2
                        if isinstance(row[3], dict):
                            additional_data = row[3]
                        elif row[3]:
                            additional_data = json.loads(row[3])
                        else:
                            additional_data = {}
                    except (json.JSONDecodeError, TypeError):
                        additional_data = {}
                    
                    activities.append({
                        'action': row[0],
                        'log_type': row[1],
                        'success': row[2],
                        'additional_data': additional_data,
                        'created_at': row[4].isoformat() if row[4] else None
                    })
                
                return activities
                
        except Exception as e:
            print(f"Error obteniendo actividad del usuario {username}: {e}")
            return []
    
    def get_activity_stats(self, username: str = None, days: int = 30) -> Dict:
        """
        Obtiene estadísticas de actividad
        
        Args:
            username: Usuario específico (None para todos)
            days: Días hacia atrás para las estadísticas
        """
        try:
            conn = db_manager.get_connection()
            
            base_query = """
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT username) as unique_users,
                    COUNT(CASE WHEN action = 'login' THEN 1 END) as logins,
                    COUNT(CASE WHEN action = 'view_report' OR action LIKE 'Visualizó informe%' THEN 1 END) as report_views,
                    COUNT(CASE WHEN action = 'download_report' OR action LIKE 'Descargó informe%' THEN 1 END) as downloads
                FROM activity_logs
                WHERE created_at >= NOW() - INTERVAL '%s days'
            """
            
            params = [days]
            
            if username:
                base_query += " AND username = %s"
                params.append(username)
            
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                row = cursor.fetchone()
                
                return {
                    'total_actions': row[0] or 0,
                    'unique_users': row[1] or 0,
                    'logins': row[2] or 0,
                    'report_views': row[3] or 0,
                    'downloads': row[4] or 0,
                    'period_days': days
                }
                
        except Exception as e:
            db_logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total_actions': 0,
                'unique_users': 0,
                'logins': 0,
                'report_views': 0,
                'downloads': 0,
                'period_days': days
            }
    
    def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """
        Obtiene la actividad reciente de todos los usuarios
        Prioriza actividades reales sobre las migradas
        
        Args:
            limit: Número máximo de registros
        """
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                # Consulta que prioriza actividades reales sobre migradas
                cursor.execute("""
                    SELECT username, action, log_type, success, additional_data, created_at
                    FROM activity_logs
                    ORDER BY 
                        CASE 
                            WHEN additional_data::jsonb->'migrated_from_json' = 'true' THEN 1 
                            ELSE 0 
                        END,
                        created_at DESC
                    LIMIT %s
                """, (limit,))
                
                activities = []
                for row in cursor.fetchall():
                    try:
                        # Si additional_data es un dict, ya está parseado por psycopg2
                        if isinstance(row[4], dict):
                            additional_data = row[4]
                        elif row[4]:
                            additional_data = json.loads(row[4])
                        else:
                            additional_data = {}
                    except (json.JSONDecodeError, TypeError):
                        additional_data = {}
                    
                    activities.append({
                        'username': row[0],
                        'action': row[1],
                        'log_type': row[2],
                        'success': row[3],
                        'additional_data': additional_data,
                        'created_at': row[5].isoformat() if row[5] else None
                    })
                
                return activities
                
        except Exception as e:
            print(f"Error obteniendo actividad reciente: {e}")
            return []
    
    def log_video_view(self, username: str, video_name: str, video_type: str, video_details: Dict = None) -> bool:
        """
        Registra la visualización de un video
        
        Args:
            username: Usuario que ve el video
            video_name: Nombre del archivo de video
            video_type: Tipo de video (team, team_player, user)
            video_details: Detalles adicionales del video (team_name, player_name, etc.)
        """
        try:
            # Para videos, permitir múltiples registros pero evitar spam reciente
            import time
            current_time = time.time()
            
            session_key = f"{self.session_prefix}video_{video_name}_{username}"
            last_log_key = f"{session_key}_last_time"
            
            try:
                last_log_time = st.session_state.get(last_log_key, 0)
                if current_time - last_log_time < 10:  # 10 segundos de cooldown para videos
                    return True  # Registrado recientemente
                
                st.session_state[last_log_key] = current_time
            except Exception:
                # Si hay problemas con session_state, continuar con el logging
                pass
            
            conn = db_manager.get_connection()
            
            # Preparar datos adicionales
            extra_data = video_details or {}
            extra_data.update({
                'video_name': video_name,
                'video_type': video_type,
                'timestamp': datetime.now().isoformat()
            })
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO activity_logs (username, action, log_type, success, additional_data)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, 'video_view', 'video', True, json.dumps(extra_data, ensure_ascii=False)))
            
            conn.commit()
            db_logger.info(f"Video view registrado: {username} vio {video_name}")
            return True
            
        except Exception as e:
            db_logger.error(f"Error registrando visualización de video para {username}: {e}")
            return False
    
    def has_user_watched_videos(self, username: str) -> bool:
        """
        Verifica si el usuario ha visto alguno de sus videos de PINTOBASKET
        
        Args:
            username: Usuario a verificar
            
        Returns:
            True si ha visto al menos un video, False si no
        """
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM activity_logs 
                    WHERE username = %s 
                    AND action = 'video_view' 
                    AND log_type = 'video'
                    AND additional_data->>'video_type' = 'user'
                """, (username,))
                
                result = cursor.fetchone()
                if result and len(result) > 0:
                    count = result[0] if result[0] is not None else 0
                    return count > 0
                return False
                
        except Exception as e:
            print(f"Error verificando videos vistos para {username}: {e}")
            return False
    
    def get_users_without_video_views(self) -> List[str]:
        """
        Obtiene lista de usuarios que nunca han visto sus videos de PINTOBASKET
        Solo incluye usuarios que realmente tienen videos disponibles
        
        Returns:
            Lista de usernames que no han visto videos
        """
        try:
            # Obtener todos los usuarios de tipo player
            from .database import db_manager
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                # Obtener todos los jugadores activos
                cursor.execute("""
                    SELECT username 
                    FROM users 
                    WHERE role = 'player' AND is_active = true
                """)
                
                all_players = [row[0] for row in cursor.fetchall()]
                
                # Verificar cuáles tienen videos y no los han visto
                players_without_views = []
                for player in all_players:
                    # Primero verificar si tiene videos disponibles
                    if self.user_has_videos_available(player):
                        # Solo entonces verificar si los ha visto
                        if not self.has_user_watched_videos(player):
                            players_without_views.append(player)
                
                return players_without_views
                
        except Exception as e:
            print(f"Error obteniendo usuarios sin visualizaciones: {e}")
            return []
    
    def get_all_players_with_video_activity(self) -> Dict[str, Dict]:
        """
        Obtiene información de actividad de videos para todos los jugadores
        Funciona solo con datos de la base de datos, sin depender de Google Drive
        
        Returns:
            Dict con información de cada jugador: {username: {has_watched: bool, video_count: int, last_view: datetime}}
        """
        try:
            from .database import db_manager
            conn = db_manager.get_connection()
            
            result = {}
            
            with conn.cursor() as cursor:
                # Obtener todos los jugadores activos
                cursor.execute("""
                    SELECT username, full_name 
                    FROM users 
                    WHERE role = 'player' AND is_active = true
                """)
                
                all_players = cursor.fetchall()
                
                for username, full_name in all_players:
                    # Contar visualizaciones de videos
                    cursor.execute("""
                        SELECT COUNT(*) as view_count,
                               MAX(created_at) as last_view
                        FROM activity_logs 
                        WHERE username = %s 
                        AND action = 'video_view' 
                        AND log_type = 'video'
                        AND additional_data->>'video_type' = 'user'
                    """, (username,))
                    
                    view_data = cursor.fetchone()
                    view_count = view_data[0] if view_data and view_data[0] else 0
                    last_view = view_data[1] if view_data and view_data[1] else None
                    
                    # Obtener videos únicos vistos
                    cursor.execute("""
                        SELECT DISTINCT additional_data->>'video_name' as video_name
                        FROM activity_logs 
                        WHERE username = %s 
                        AND action = 'video_view' 
                        AND log_type = 'video'
                        AND additional_data->>'video_type' = 'user'
                        AND additional_data->>'video_name' IS NOT NULL
                    """, (username,))
                    
                    unique_videos = [row[0] for row in cursor.fetchall() if row[0]]
                    
                    result[username] = {
                        'full_name': full_name,
                        'has_watched': view_count > 0,
                        'view_count': view_count,
                        'unique_videos': len(unique_videos),
                        'video_names': unique_videos,
                        'last_view': last_view
                    }
                
                return result
                
        except Exception as e:
            print(f"Error obteniendo actividad de videos: {e}")
            return {}
    
    def user_has_videos_available(self, username: str) -> bool:
        """
        Verifica si un usuario tiene videos disponibles en PINTOBASKET
        
        Args:
            username: Usuario a verificar
            
        Returns:
            True si tiene videos disponibles, False si no (o si no se puede verificar)
        """
        try:
            # Import local para evitar circular imports
            import sys
            import os
            
            # Agregar la ruta del proyecto al path si no está
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from src.utils.video_manager import video_manager
            
            # Verificar si Google Drive está autenticado
            if not video_manager.drive_client.is_authenticated():
                # Si no está autenticado, asumir que no hay videos disponibles
                # para evitar mostrar notificaciones falsas
                return False
            
            user_videos = video_manager.get_user_videos(username)
            return len(user_videos) > 0
        except Exception as e:
            print(f"Error verificando videos disponibles para {username}: {e}")
            return False
    
    def clear_session_logs(self):
        """Limpia los logs de la sesión actual (para testing o reset)"""
        keys_to_remove = [key for key in st.session_state.keys() 
                         if key.startswith(self.session_prefix)]
        
        for key in keys_to_remove:
            del st.session_state[key]