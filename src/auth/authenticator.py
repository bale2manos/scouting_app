# src/auth/authenticator.py
# -*- coding: utf-8 -*-
"""
Autenticador principal para Streamlit
Gestiona sesiones, login y logout con persistencia
"""
import streamlit as st
import hashlib
import time
from typing import Optional, Dict, Tuple
from .user_manager import UserManager
from .logger import ActivityLogger


class Authenticator:
    """Gestiona la autenticación en Streamlit con persistencia de sesión"""
    
    def __init__(self, users_file_path: str = "data/auth/users.json"):
        self.user_manager = UserManager(users_file_path)
        self.activity_logger = ActivityLogger()
        
        # Inicializar session state si no existe
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user" not in st.session_state:
            st.session_state.user = None
        if "auth_error" not in st.session_state:
            st.session_state.auth_error = None
        if "session_token" not in st.session_state:
            st.session_state.session_token = None
        if "session_start_time" not in st.session_state:
            st.session_state.session_start_time = None
        
        # Verificar persistencia al inicializar
        self._check_session_persistence()
    
    def _generate_session_token(self, username: str) -> str:
        """Genera un token de sesión único"""
        timestamp = str(time.time())
        session_data = f"{username}:{timestamp}:{st.session_state.get('session_id', '')}"
        return hashlib.sha256(session_data.encode()).hexdigest()[:32]
    
    def _check_session_persistence(self) -> None:
        """Verifica si hay una sesión válida persistente"""
        # Verificar si tenemos un token de sesión válido
        if (st.session_state.get("session_token") and 
            st.session_state.get("user") and 
            st.session_state.get("session_start_time")):
            
            # Verificar que no haya expirado (24 horas)
            current_time = time.time()
            session_start = st.session_state.session_start_time
            session_duration = current_time - session_start
            
            # Sesión válida por 24 horas (86400 segundos)
            if session_duration < 86400:
                # Verificar que el usuario sigue existiendo y activo
                user_data = self.user_manager.get_user(st.session_state.user["username"])
                if user_data and user_data.get("is_active", True):
                    # Sesión válida - mantener autenticado
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    # Debug info
                    if st.query_params.get("debug") == "session":
                        st.sidebar.success(f"✅ Sesión persistente válida: {user_data['username']}")
                        st.sidebar.info(f"Tiempo restante: {(86400 - session_duration)/3600:.1f}h")
                    return
            
            # Sesión expirada o inválida - limpiar
            if st.query_params.get("debug") == "session":
                st.sidebar.error(f"❌ Sesión expirada: {session_duration/3600:.1f}h")
            self._clear_session()
    
    def _clear_session(self) -> None:
        """Limpia los datos de sesión"""
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.session_token = None
        st.session_state.session_start_time = None
        st.session_state.auth_error = None
    
    def is_authenticated(self) -> bool:
        """Verifica si el usuario está autenticado"""
        return st.session_state.get("authenticated", False)
    
    def get_current_user(self) -> Optional[Dict]:
        """Obtiene el usuario actual"""
        return st.session_state.get("user", None)
    
    def is_admin(self) -> bool:
        """Verifica si el usuario actual es admin"""
        user = self.get_current_user()
        return user and user.get("role") == "admin"
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Intenta hacer login con las credenciales
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        success, user_data = self.user_manager.authenticate_user(username, password)
        
        if success and user_data:
            # Establecer sesión con persistencia
            session_token = self._generate_session_token(username)
            st.session_state.authenticated = True
            st.session_state.user = user_data
            st.session_state.session_token = session_token
            st.session_state.session_start_time = time.time()
            st.session_state.auth_error = None
            
            # Registrar el acceso
            self.activity_logger.log_access(
                username=username,
                action="login",
                success=True,
                user_agent=st.context.headers.get("User-Agent", "Unknown"),
                ip_address=self._get_client_ip()
            )
            
            return True, f"¡Bienvenido, {user_data.get('full_name', username)}!"
        else:
            # Registrar intento fallido
            self.activity_logger.log_access(
                username=username,
                action="login_failed",
                success=False,
                user_agent=st.context.headers.get("User-Agent", "Unknown"),
                ip_address=self._get_client_ip()
            )
            
            return False, "Usuario o contraseña incorrectos"
    
    def logout(self) -> None:
        """Cierra la sesión del usuario"""
        user = self.get_current_user()
        if user:
            # Registrar logout
            self.activity_logger.log_access(
                username=user.get("username", "unknown"),
                action="logout",
                success=True,
                user_agent=st.context.headers.get("User-Agent", "Unknown"),
                ip_address=self._get_client_ip()
            )
        
        # Limpiar session state completamente
        self._clear_session()
        
        # Limpiar cualquier estado de navegación
        if "route" in st.session_state:
            st.session_state.route = "home"
        if "show_user_menu" in st.session_state:
            st.session_state.show_user_menu = False
    
    def require_auth(self) -> bool:
        """
        Verifica autenticación y redirige a login si es necesario
        
        Returns:
            bool: True si está autenticado, False si necesita login
        """
        if not self.is_authenticated():
            return False
        
        # Verificar que el usuario todavía existe y está activo
        current_user = self.get_current_user()
        if current_user:
            # Refrescar datos del usuario
            user_data = self.user_manager.get_user(current_user["username"])
            if not user_data or not user_data.get("is_active", True):
                # Usuario desactivado o eliminado
                self.logout()
                st.session_state.auth_error = "Tu cuenta ha sido desactivada"
                return False
            
            # Actualizar datos del usuario en session state
            st.session_state.user = user_data
        
        return True
    
    def require_admin(self) -> bool:
        """
        Verifica que el usuario sea admin
        
        Returns:
            bool: True si es admin, False en caso contrario
        """
        if not self.require_auth():
            return False
        
        if not self.is_admin():
            st.error("❌ Acceso denegado. Se requieren permisos de administrador.")
            return False
        
        return True
    
    def _get_client_ip(self) -> str:
        """Obtiene la IP del cliente (limitado en Streamlit Cloud)"""
        try:
            # En Streamlit Cloud esto puede no estar disponible
            headers = st.context.headers
            return (
                headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                headers.get("X-Real-IP", "") or
                headers.get("Remote-Addr", "") or
                "Unknown"
            )
        except:
            return "Unknown"
    
    def show_login_form(self) -> None:
        """Muestra el formulario de login"""
        st.markdown("### 🔐 Iniciar Sesión")
        
        # Mostrar error si existe
        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error)
            st.session_state.auth_error = None
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingresa tu nombre de usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submit_button = st.form_submit_button("🚀 Ingresar", use_container_width=True)
            
            if submit_button:
                if username and password:
                    success, message = self.login(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("⚠️ Por favor ingresa usuario y contraseña")
    
    def show_user_info(self) -> None:
        """Muestra información del usuario actual en la sidebar (DESHABILITADO)"""
        # Función deshabilitada - no mostrar sidebar
        pass
    
    def log_page_view(self, page_name: str, additional_data: Dict = None) -> None:
        """Registra una visita a una página"""
        user = self.get_current_user()
        if user:
            self.activity_logger.log_activity(
                username=user["username"],
                action="page_view",
                page=page_name,
                additional_data=additional_data or {}
            )
    
    def log_action(self, action: str, additional_data: Dict = None) -> None:
        """Registra una acción del usuario"""
        user = self.get_current_user()
        if user:
            self.activity_logger.log_activity(
                username=user["username"],
                action=action,
                additional_data=additional_data or {}
            )
    
    def log_report_view(self, report_type: str, report_name: str) -> None:
        """Registra visualización de informe con nombre específico"""
        user = self.get_current_user()
        if user:
            # Crear mensaje descriptivo para el historial
            if report_type == "team_report":
                action_description = f"Visualizó informe del equipo: {report_name}"
            elif report_type == "player_report":
                action_description = f"Visualizó informe del jugador: {report_name}"
            else:
                action_description = f"Visualizó {report_type}: {report_name}"
                
            self.activity_logger.log_activity(
                username=user["username"],
                action="view_report",
                additional_data={
                    "report_type": report_type,
                    "report_name": report_name,
                    "description": action_description
                }
            )
    
    def log_report_download(self, report_type: str, report_name: str) -> None:
        """Registra descarga de informe con nombre específico"""
        user = self.get_current_user()
        if user:
            # Crear mensaje descriptivo para el historial
            if report_type == "team_report":
                action_description = f"Descargó informe del equipo: {report_name}"
            elif report_type == "player_report":
                action_description = f"Descargó informe del jugador: {report_name}"
            else:
                action_description = f"Descargó {report_type}: {report_name}"
                
            self.activity_logger.log_activity(
                username=user["username"],
                action="download_report",
                additional_data={
                    "report_type": report_type,
                    "report_name": report_name,
                    "description": action_description
                }
            )