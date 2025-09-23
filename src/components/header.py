import streamlit as st
from src.utils.ui import back_button, set_route
from src.auth.db_authenticator import DatabaseAuthenticator


def header_bar():
    """Renderiza la barra de header simplificada con autenticación"""
    auth = DatabaseAuthenticator()
    current_user = auth.get_current_user()
    
    left, mid, right = st.columns([3, 6, 3], vertical_alignment="center")
    
    with left:
        home_col, back_col = st.columns([1, 1])
        
        with home_col:
            if st.button("🏠 Home", use_container_width=True, key="header_home"):
                set_route("home")
                st.rerun()
        
        with back_col:
            route = st.session_state.get("route", "home")
            if route != "home":
                back_button()
    
    with mid:
        st.markdown("<h2 style='text-align:center;margin:0'>🏀 Scouting Hub</h2>", unsafe_allow_html=True)
    
    with right:
        if current_user:
            col1, col2 = st.columns(2)
            
            with col1:
                user_name = current_user.get('full_name', current_user['username'])
                role_icon = "👨‍💼" if current_user.get('role') == 'admin' else "👤"
                
                if st.button(f"{role_icon} {user_name}", use_container_width=True, key="header_user"):
                    st.session_state['show_user_menu'] = not st.session_state.get('show_user_menu', False)
                    st.rerun()
            
            with col2:
                if st.button("📚 Equipos", use_container_width=True, key="header_teams"):
                    set_route("teams")
                    st.rerun()
        
        if st.session_state.get('show_user_menu', False):
            show_user_menu(auth, current_user)


def show_user_menu(auth, current_user):
    """Muestra el menú desplegable del usuario"""
    with st.container():
        st.markdown("---")
        
        # Solo admins ven estadísticas en su propia fila
        if current_user.get('role') == 'admin':
            if st.button("📊 Estadísticas", use_container_width=True, key="menu_stats"):
                set_route("stats")
                st.session_state['show_user_menu'] = False
                st.rerun()
        
        # Fila principal: Videos y Logout lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            # Verificar el rol del usuario para mostrar botón apropiado
            username = current_user.get('username', '')
            user_role = current_user.get('role', '')
            
            if user_role in ['admin', 'coach']:
                # Para admins y coaches: mostrar botón "Log Videos"
                if st.button("📊 Log Videos", use_container_width=True, key="menu_log_videos"):
                    set_route("log_videos")
                    st.session_state['show_user_menu'] = False
                    st.rerun()
            else:
                # Botón estándar para jugadores
                if st.button("🎥 Mis Videos", use_container_width=True, key="menu_my_videos"):
                    # Configurar contexto para mostrar videos del usuario
                    st.session_state['video_context'] = {
                        'type': 'user',
                        'username': username
                    }
                    set_route("videos")
                    st.session_state['show_user_menu'] = False
                    st.rerun()
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True, key="menu_logout"):
                auth.logout()
                st.session_state['show_user_menu'] = False
                st.rerun()
        
        st.markdown("---")