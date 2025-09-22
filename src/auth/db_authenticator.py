# src/auth/db_authenticator.py
# -*- coding: utf-8 -*-
"""
Sistema de autenticación con base de datos PostgreSQL
Compatible con el sistema actual pero usando Supabase
"""
import streamlit as st
import hashlib
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import uuid
import logging

from .database import db_manager
from .db_logger import DatabaseLogger

logger = logging.getLogger(__name__)

class DatabaseAuthenticator:
    """Sistema de autenticación usando PostgreSQL/Supabase"""
    
    def __init__(self, jwt_secret: str = None):
        self.jwt_secret = jwt_secret or self._get_jwt_secret()
        self.logger = DatabaseLogger()
        self.session_timeout = timedelta(hours=8)  # 8 horas de sesión
    
    def _get_jwt_secret(self) -> str:
        """Obtiene el secret para JWT desde configuración"""
        try:
            return st.secrets["auth"]["JWT_SECRET"]
        except (KeyError, AttributeError):
            # Fallback para desarrollo local
            return "default_jwt_secret_change_in_production"
    
    def _hash_password(self, password: str) -> str:
        """Genera hash de la contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica la contraseña contra su hash"""
        return self._hash_password(password) == password_hash
    
    def _generate_session_token(self, username: str) -> str:
        """Genera un token JWT para la sesión"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + self.session_timeout,
            'iat': datetime.utcnow(),
            'session_id': str(uuid.uuid4())
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def _verify_session_token(self, token: str) -> Optional[Dict]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expirado")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token JWT inválido")
            return None
    
    def register_user(self, username: str, password: str, role: str = "viewer", full_name: str = "") -> bool:
        """Registra un nuevo usuario en la base de datos"""
        try:
            conn = db_manager.get_connection()
            password_hash = self._hash_password(password)
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, full_name)
                    VALUES (%s, %s, %s, %s)
                """, (username, password_hash, role, full_name))
            
            conn.commit()
            logger.info(f"Usuario {username} registrado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error registrando usuario {username}: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Autentica un usuario contra la base de datos"""
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT password_hash, is_active, full_name, role 
                    FROM users 
                    WHERE username = %s
                """, (username,))
                
                result = cursor.fetchone()
                
                if not result:
                    self.logger.log_access(username, "login_failed", False, 
                                         additional_data={"reason": "user_not_found"})
                    return False, None, "user_not_found"
                
                password_hash, is_active, full_name, role = result
                
                if not is_active:
                    self.logger.log_access(username, "login_failed", False,
                                         additional_data={"reason": "user_inactive"})
                    return False, None, "user_inactive"
                
                if self._verify_password(password, password_hash):
                    # Login exitoso
                    token = self._generate_session_token(username)
                    
                    # Guardar sesión en base de datos
                    self._save_session(username, token)
                    
                    # Guardar en session_state de Streamlit
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["session_token"] = token
                    
                    # Log del login exitoso
                    self.logger.log_access(username, "login", True)
                    
                    # Devolver datos del usuario
                    user_data = {
                        "username": username,
                        "full_name": full_name,
                        "role": role,
                        "is_active": is_active
                    }
                    
                    return True, user_data, None
                else:
                    self.logger.log_access(username, "login_failed", False,
                                         additional_data={"reason": "invalid_password"})
                    return False, None, "invalid_password"
                    
        except Exception as e:
            logger.error(f"Error autenticando usuario {username}: {e}")
            self.logger.log_access(username, "login_failed", False,
                                 additional_data={"reason": "system_error", "error": str(e)})
            return False, None, "system_error"
    
    def _save_session(self, username: str, token: str):
        """Guarda la sesión en la base de datos"""
        try:
            payload = self._verify_session_token(token)
            if not payload:
                return
                
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_sessions (session_id, username, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        expires_at = EXCLUDED.expires_at
                """, (payload['session_id'], username, 
                     datetime.fromtimestamp(payload['exp'])))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error guardando sesión: {e}")
    
    def is_authenticated(self) -> bool:
        """Verifica si el usuario actual está autenticado"""
        if not st.session_state.get("authenticated", False):
            return False
        
        token = st.session_state.get("session_token")
        if not token:
            return False
        
        # Verificar token JWT
        payload = self._verify_session_token(token)
        if not payload:
            self.logout()
            return False
        
        # Verificar sesión en base de datos
        if not self._verify_session_in_db(payload['session_id']):
            self.logout()
            return False
        
        return True
    
    def _verify_session_in_db(self, session_id: str) -> bool:
        """Verifica que la sesión exista y no haya expirado en la base de datos"""
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT username FROM user_sessions 
                    WHERE session_id = %s AND expires_at > NOW()
                """, (session_id,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error verificando sesión en DB: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict]:
        """Obtiene la información completa del usuario actual autenticado"""
        if self.is_authenticated():
            username = st.session_state.get("username")
            if username:
                try:
                    conn = db_manager.get_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT username, full_name, role, is_active 
                            FROM users 
                            WHERE username = %s
                        """, (username,))
                        
                        result = cursor.fetchone()
                        if result:
                            return {
                                "username": result[0],
                                "full_name": result[1],
                                "role": result[2],
                                "is_active": result[3]
                            }
                except Exception as e:
                    logger.error(f"Error obteniendo datos del usuario {username}: {e}")
        return None
    
    def get_user_role(self, username: str = None) -> Optional[str]:
        """Obtiene el rol del usuario"""
        if not username:
            current_user = self.get_current_user()
            if current_user:
                return current_user.get("role")
            return None
        
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT role FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error obteniendo rol del usuario {username}: {e}")
            return None
    
    def logout(self):
        """Cierra la sesión del usuario"""
        username = st.session_state.get("username")
        session_token = st.session_state.get("session_token")
        
        # Eliminar sesión de la base de datos
        if session_token:
            try:
                payload = jwt.decode(session_token, self.jwt_secret, 
                                   algorithms=['HS256'], options={"verify_exp": False})
                session_id = payload.get('session_id')
                
                if session_id:
                    conn = db_manager.get_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM user_sessions WHERE session_id = %s", 
                                     (session_id,))
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Error eliminando sesión de DB: {e}")
        
        # Log del logout
        if username:
            self.logger.log_access(username, "logout", True)
        
        # Limpiar session_state
        for key in ["authenticated", "username", "session_token"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_all_users(self) -> List[Dict]:
        """Obtiene todos los usuarios (solo para admins)"""
        try:
            conn = db_manager.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT username, role, full_name, is_active, created_at, updated_at
                    FROM users
                    ORDER BY created_at DESC
                """)
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'username': row[0],
                        'role': row[1],
                        'full_name': row[2] or '',
                        'is_active': row[3],
                        'created_at': row[4].isoformat() if row[4] else None,
                        'updated_at': row[5].isoformat() if row[5] else None
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def update_user(self, username: str, **kwargs) -> bool:
        """Actualiza los datos de un usuario"""
        try:
            conn = db_manager.get_connection()
            
            # Construir query dinámicamente
            set_clauses = []
            values = []
            
            if 'password' in kwargs:
                set_clauses.append("password_hash = %s")
                values.append(self._hash_password(kwargs['password']))
            
            if 'role' in kwargs:
                set_clauses.append("role = %s")
                values.append(kwargs['role'])
            
            if 'full_name' in kwargs:
                set_clauses.append("full_name = %s")
                values.append(kwargs['full_name'])
            
            if 'is_active' in kwargs:
                set_clauses.append("is_active = %s")
                values.append(kwargs['is_active'])
            
            if not set_clauses:
                return True  # No hay nada que actualizar
            
            set_clauses.append("updated_at = NOW()")
            values.append(username)
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE username = %s"
            
            with conn.cursor() as cursor:
                cursor.execute(query, values)
            
            conn.commit()
            logger.info(f"Usuario {username} actualizado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando usuario {username}: {e}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """Elimina un usuario (desactiva en lugar de eliminar físicamente)"""
        return self.update_user(username, is_active=False)
    
    # Métodos de compatibilidad con el sistema anterior
    def log_access(self, username: str, action: str, success: bool = True, **kwargs):
        """Compatibilidad: delega al logger de base de datos"""
        return self.logger.log_access(username, action, success, **kwargs)
    
    def log_activity(self, username: str, action: str, page: str = "", **kwargs):
        """Compatibilidad: delega al logger de base de datos"""
        return self.logger.log_activity(username, action, page, **kwargs)
    
    def log_report_view(self, report_type: str, report_name: str):
        """Compatibilidad: delega al logger de base de datos"""
        return self.logger.log_report_view(report_type, report_name)
    
    def log_report_download(self, report_type: str, report_name: str):
        """Compatibilidad: delega al logger de base de datos"""
        return self.logger.log_report_download(report_type, report_name)