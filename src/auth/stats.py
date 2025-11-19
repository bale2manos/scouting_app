# src/auth/stats.py
# -*- coding: utf-8 -*-
"""
Gestor de estadísticas y métricas para el sistema de autenticación
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List
from .database import db_manager
from .db_logger import DatabaseLogger


class StatsManager:
    """Gestiona y visualiza estadísticas del sistema"""
    
    def __init__(self):
        self.logger = DatabaseLogger()
    
    def _show_dashboard_header(self):
        """Muestra el header del dashboard con navegación"""
        # Importar aquí para evitar imports circulares
        from src.utils.ui import set_route
        
        col1, col2, col3 = st.columns([2, 6, 2])
        
        with col1:
            if st.button("🏠 Volver a Home", width="stretch"):
                set_route("home")
                st.rerun()
        
        with col2:
            st.markdown("<h3 style='text-align:center;margin:0'>📊 Panel de Administración</h3>", 
                       unsafe_allow_html=True)
        
        with col3:
            if st.button("🔄 Actualizar", width="stretch"):
                st.rerun()
        
        st.markdown("---")
    
    def show_dashboard(self):
        """Muestra el dashboard principal de estadísticas"""
        # Header con navegación
        self._show_dashboard_header()
        
        st.markdown("# 📊 Dashboard de Estadísticas")
        
        # Métricas principales
        self._show_main_metrics()
        
        st.markdown("---")
        
        # Tabs para diferentes secciones
        tab1, tab2, tab3 = st.tabs([
            "📈 Actividad", "👥 Usuarios", "🔍 Detalles"
        ])
        
        with tab1:
            self._show_activity_stats()
        
        with tab2:
            self._show_user_stats()
        
        with tab3:
            self._show_detailed_stats()
    
    def _get_user_stats(self):
        """Obtiene estadísticas de usuarios de la base de datos"""
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                # Total de usuarios
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                # Usuarios activos
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
                active_users = cursor.fetchone()[0]
                
                # Usuarios por rol
                cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
                roles = dict(cursor.fetchall())
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "admin_users": roles.get("admin", 0),
                    "coach_users": roles.get("coach", 0),
                    "player_users": roles.get("player", 0)
                }
        except Exception as e:
            st.error(f"Error obteniendo estadísticas de usuarios: {e}")
            # Cerrar conexión problemática
            try:
                conn.rollback()
            except:
                pass
            return {
                "total_users": 0,
                "active_users": 0,
                "admin_users": 0,
                "coach_users": 0,
                "player_users": 0
            }
    
    def _get_activity_stats(self):
        """Obtiene estadísticas de actividad de la base de datos"""
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                # Total de logs de acceso
                cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action = 'login' AND success = true")
                total_logins = cursor.fetchone()[0]
                
                # Usuarios únicos hoy
                today = datetime.now().date()
                cursor.execute("""
                    SELECT COUNT(DISTINCT username) 
                    FROM activity_logs 
                    WHERE action = 'login' AND success = true 
                    AND DATE(created_at) = %s
                """, (today,))
                unique_users_today = cursor.fetchone()[0]
                
                # Total de visualizaciones de páginas
                cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action = 'page_view'")
                total_page_views = cursor.fetchone()[0]
                
                return {
                    "total_logins": total_logins,
                    "unique_users_today": unique_users_today,
                    "total_page_views": total_page_views
                }
        except Exception as e:
            st.error(f"Error obteniendo estadísticas de actividad: {e}")
            # Cerrar conexión problemática
            try:
                conn.rollback()
            except:
                pass
            return {
                "total_logins": 0,
                "unique_users_today": 0,
                "total_page_views": 0
            }
    
    def _show_main_metrics(self):
        """Muestra métricas principales en cards"""
        # Obtener estadísticas
        user_stats = self._get_user_stats()
        activity_stats = self._get_activity_stats()
        
        # Layout de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="👥 Total Usuarios",
                value=user_stats["total_users"],
                delta=f"{user_stats['active_users']} activos"
            )
        
        with col2:
            st.metric(
                label="🔐 Total Logins",
                value=activity_stats["total_logins"],
                delta=f"{activity_stats['unique_users_today']} hoy"
            )
        
        with col3:
            st.metric(
                label="👨‍💼 Administradores",
                value=user_stats["admin_users"],
                delta=f"{user_stats['coach_users']} entrenadores"
            )
        
        with col4:
            st.metric(
                label="📄 Páginas Vistas",
                value=activity_stats["total_page_views"],
                delta=f"{user_stats['player_users']} jugadores"
            )
    
    def _show_activity_stats(self):
        """Muestra estadísticas de actividad"""
        st.markdown("### 📈 Actividad Reciente")
        
        # Logs de acceso recientes
        recent_logs = self.logger.get_recent_activity(20)
        
        if recent_logs:
            # Preparar datos para mostrar con descripciones específicas
            display_data = []
            for log in recent_logs:
                # Obtener descripción específica si existe
                additional_data = log.get("additional_data", {})
                description = additional_data.get("description", "") if isinstance(additional_data, dict) else ""
                
                # Usar descripción específica o mostrar la acción directamente si ya es específica
                if description:
                    action_display = description
                elif log["action"].startswith(("Visualizó", "Descargó")):
                    # Las acciones ya contienen información específica del informe
                    action_display = log["action"]
                else:
                    # Mejorar la presentación de acciones genéricas antiguas
                    action = log["action"]
                    if action == "view_report":
                        report_name = additional_data.get("report_name", "") if isinstance(additional_data, dict) else ""
                        report_type = additional_data.get("report_type", "") if isinstance(additional_data, dict) else ""
                        if report_name and report_type:
                            if report_type == "team_report":
                                action_display = f"Visualizó informe del equipo: {report_name}"
                            elif report_type == "player_report":
                                action_display = f"Visualizó informe del jugador: {report_name}"
                            else:
                                action_display = f"Visualizó {report_type}: {report_name}"
                        else:
                            action_display = "Visualizó informe"
                    elif action == "download_report":
                        report_name = additional_data.get("report_name", "") if isinstance(additional_data, dict) else ""
                        report_type = additional_data.get("report_type", "") if isinstance(additional_data, dict) else ""
                        if report_name and report_type:
                            if report_type == "team_report":
                                action_display = f"Descargó informe del equipo: {report_name}"
                            elif report_type == "player_report":
                                action_display = f"Descargó informe del jugador: {report_name}"
                            else:
                                action_display = f"Descargó {report_type}: {report_name}"
                        else:
                            action_display = "Descargó informe"
                    elif action == "login":
                        action_display = "Inició sesión"
                    elif action == "logout":
                        action_display = "Cerró sesión"
                    elif action == "login_failed":
                        action_display = "Intento de login fallido"
                    else:
                        action_display = action
                
                # Formatear timestamp
                try:
                    if isinstance(log["created_at"], str):
                        timestamp = datetime.fromisoformat(log["created_at"].replace('Z', '+00:00'))
                    else:
                        timestamp = log["created_at"]
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp_str = str(log["created_at"])
                
                display_data.append({
                    "Usuario": log["username"],
                    "Fecha/Hora": timestamp_str,
                    "Acción": action_display,
                    "Éxito": "✅" if log["success"] else "❌"
                })
            
            display_df = pd.DataFrame(display_data)
            
            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True
            )
        else:
            st.info("📝 No hay logs de acceso disponibles")
    
    def _show_user_stats(self):
        """Muestra estadísticas de usuarios"""
        st.markdown("### 👥 Estadísticas de Usuarios")
        
        # Lista de usuarios con sus estadísticas
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT username, full_name, role, is_active, created_at
                    FROM users 
                    ORDER BY created_at DESC
                """)
                users = cursor.fetchall()
                
                if users:
                    # Preparar datos
                    user_data = []
                    for user in users:
                        username, full_name, role, is_active, created_at = user
                        
                        # Obtener estadísticas de actividad del usuario
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM activity_logs 
                            WHERE username = %s AND action = 'login' AND success = true
                        """, (username,))
                        total_sessions = cursor.fetchone()[0]
                        
                        # Último acceso
                        cursor.execute("""
                            SELECT MAX(created_at) 
                            FROM activity_logs 
                            WHERE username = %s AND action = 'login' AND success = true
                        """, (username,))
                        last_login_result = cursor.fetchone()
                        last_login = last_login_result[0] if last_login_result[0] else None
                        
                        user_data.append({
                            "Usuario": full_name,
                            "Username": username,
                            "Rol": role.title(),
                            "Estado": "✅ Activo" if is_active else "❌ Inactivo",
                            "Total Sesiones": total_sessions,
                            "Último Acceso": last_login.strftime("%Y-%m-%d %H:%M") if last_login else "Nunca",
                            "Creado": created_at.strftime("%Y-%m-%d") if created_at else "N/A"
                        })
                    
                    df_users = pd.DataFrame(user_data)
                    
                    # Mostrar tabla
                    st.dataframe(
                        df_users,
                        width="stretch",
                        hide_index=True
                    )
                else:
                    st.info("👥 No hay usuarios registrados")
                    
        except Exception as e:
            st.error(f"Error obteniendo usuarios: {e}")
            # Cerrar conexión problemática
            try:
                conn.rollback()
            except:
                pass
    
    def _show_detailed_stats(self):
        """Muestra estadísticas detalladas"""
        st.markdown("### 🔍 Análisis Detallado")
        
        # Selector de usuario para análisis individual
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT username FROM users ORDER BY username")
                users = [row[0] for row in cursor.fetchall()]
                
                if users:
                    # Selector de usuario con paginación
                    page_size = 10
                    total_pages = (len(users) + page_size - 1) // page_size
                    page = st.number_input("Página:", min_value=1, max_value=total_pages, step=1, value=1)
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    paginated_users = users[start_idx:end_idx]

                    selected_user = st.selectbox(
                        "👤 Seleccionar usuario para análisis:",
                        ["Todos"] + paginated_users
                    )
                    
                    if selected_user != "Todos":
                        self._show_user_detailed_stats(selected_user)
                    else:
                        self._show_system_detailed_stats()
                else:
                    st.info("👥 No hay usuarios para analizar")
                    
        except Exception as e:
            st.error(f"Error obteniendo usuarios: {e}")
    
    def _show_user_detailed_stats(self, username: str):
        """Muestra estadísticas detalladas de un usuario"""
        st.markdown(f"#### 👤 Análisis de {username}")
        
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                # Estadísticas del usuario
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM activity_logs 
                    WHERE username = %s AND action = 'login' AND success = true
                """, (username,))
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM activity_logs 
                    WHERE username = %s
                """, (username,))
                total_actions = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM activity_logs 
                    WHERE username = %s AND action = 'page_view'
                """, (username,))
                total_page_views = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT MAX(created_at) 
                    FROM activity_logs 
                    WHERE username = %s
                """, (username,))
                last_activity_result = cursor.fetchone()
                last_activity = last_activity_result[0] if last_activity_result[0] else None
                
                # Métricas del usuario
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🔐 Sesiones", total_sessions)
                
                with col2:
                    st.metric("🎯 Acciones", total_actions)
                
                with col3:
                    st.metric("📄 Páginas", total_page_views)
                
                with col4:
                    if last_activity:
                        last_date = last_activity.strftime("%d/%m/%Y")
                        st.metric("🕒 Último", last_date)
                    else:
                        st.metric("🕒 Último", "Nunca")
                
                # Logs recientes del usuario
                st.markdown("##### 📋 Actividad Reciente")
                cursor.execute("""
                    SELECT username, action, success, created_at, additional_data
                    FROM activity_logs 
                    WHERE username = %s 
                    ORDER BY created_at DESC 
                    LIMIT 20
                """, (username,))
                
                recent_logs = []
                for row in cursor.fetchall():
                    recent_logs.append({
                        "username": row[0],
                        "action": row[1],
                        "success": row[2],
                        "created_at": row[3],
                        "additional_data": row[4] if row[4] else {}
                    })
                
                if recent_logs:
                    # Preparar datos para mostrar con descripciones específicas
                    display_data = []
                    for log in recent_logs:
                        # Obtener descripción específica si existe
                        additional_data = log.get("additional_data", {})
                        description = additional_data.get("description", "")
                        
                        # Usar descripción específica o mostrar la acción directamente si ya es específica
                        if description:
                            action_display = description
                        elif log["action"].startswith(("Visualizó", "Descargó")):
                            # Las acciones ya contienen información específica del informe
                            action_display = log["action"]
                        else:
                            # Mejorar la presentación de acciones genéricas antiguas
                            action = log["action"]
                            if action == "view_report":
                                report_name = additional_data.get("report_name", "")
                                report_type = additional_data.get("report_type", "")
                                if report_name and report_type:
                                    if report_type == "team_report":
                                        action_display = f"Visualizó informe del equipo: {report_name}"
                                    elif report_type == "player_report":
                                        action_display = f"Visualizó informe del jugador: {report_name}"
                                    else:
                                        action_display = f"Visualizó {report_type}: {report_name}"
                                else:
                                    action_display = "Visualizó informe"
                            elif action == "download_report":
                                report_name = additional_data.get("report_name", "")
                                report_type = additional_data.get("report_type", "")
                                if report_name and report_type:
                                    if report_type == "team_report":
                                        action_display = f"Descargó informe del equipo: {report_name}"
                                    elif report_type == "player_report":
                                        action_display = f"Descargó informe del jugador: {report_name}"
                                    else:
                                        action_display = f"Descargó {report_type}: {report_name}"
                                else:
                                    action_display = "Descargó informe"
                            elif action == "login":
                                action_display = "Inició sesión"
                            elif action == "logout":
                                action_display = "Cerró sesión"
                            elif action == "login_failed":
                                action_display = "Intento de login fallido"
                            else:
                                action_display = action
                        
                        # Formatear timestamp
                        try:
                            timestamp_str = log["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            timestamp_str = str(log["created_at"])
                        
                        display_data.append({
                            "Fecha/Hora": timestamp_str,
                            "Acción": action_display,
                            "Éxito": "✅" if log["success"] else "❌"
                        })
                    
                    display_df = pd.DataFrame(display_data)
                    
                    st.dataframe(
                        display_df,
                        width="stretch",
                        hide_index=True
                    )
                else:
                    st.info("📝 No hay actividad reciente para este usuario")
                    
        except Exception as e:
            st.error(f"Error obteniendo estadísticas del usuario: {e}")
    
    def _show_system_detailed_stats(self):
        """Muestra estadísticas detalladas del sistema"""
        st.markdown("#### 🖥️ Análisis del Sistema")
        
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                # Estadísticas generales
                stats = {}
                
                # Total de logs
                cursor.execute("SELECT COUNT(*) FROM activity_logs")
                stats["total_logs"] = cursor.fetchone()[0]
                
                # Acciones más comunes
                cursor.execute("""
                    SELECT action, COUNT(*) as count 
                    FROM activity_logs 
                    GROUP BY action 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                stats["top_actions"] = dict(cursor.fetchall())
                
                # Usuarios más activos
                cursor.execute("""
                    SELECT username, COUNT(*) as count 
                    FROM activity_logs 
                    GROUP BY username 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                stats["most_active_users"] = dict(cursor.fetchall())
                
                # Actividad por día (últimos 7 días) - convertir fechas a string
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count 
                    FROM activity_logs 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY DATE(created_at) 
                    ORDER BY date DESC
                """)
                daily_results = cursor.fetchall()
                # Convertir datetime.date a string para serialización JSON
                stats["daily_activity"] = {str(date): count for date, count in daily_results}
                
                # Mostrar estadísticas
                st.json(stats)
                
        except Exception as e:
            st.error(f"Error obteniendo estadísticas del sistema: {e}")
            st.json({"error": str(e)})