# src/auth/database.py
# -*- coding: utf-8 -*-
"""
Sistema de base de datos PostgreSQL para autenticación con Supabase
"""
import os
import psycopg2
import streamlit as st
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de conexiones y esquemas de PostgreSQL"""
    
    def __init__(self):
        self.connection_url = None
        self._connection = None
    
    # Definición de las tablas SQL
    USERS_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            role VARCHAR(20) DEFAULT 'viewer',
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    """
    
    ACTIVITY_LOGS_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            action VARCHAR(200) NOT NULL,
            log_type VARCHAR(20) DEFAULT 'activity',
            success BOOLEAN DEFAULT true,
            additional_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_activity_logs_username ON activity_logs(username);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);
    """
    
    USER_SESSIONS_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(100) PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_sessions_username ON user_sessions(username);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
    """
    
    def get_connection_url(self) -> str:
        """Obtiene la URL de conexión desde secrets o variables de entorno"""
        if self.connection_url:
            return self.connection_url
            
        # Intentar desde streamlit secrets
        try:
            self.connection_url = st.secrets["database"]["DATABASE_URL"]
            return self.connection_url
        except (KeyError, AttributeError):
            pass
        
        # Intentar desde variables de entorno
        self.connection_url = os.getenv("DATABASE_URL")
        if not self.connection_url:
            raise ValueError("DATABASE_URL no encontrada en secrets ni en variables de entorno")
        
        return self.connection_url
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        if self._connection and not self._connection.closed:
            return self._connection
            
        try:
            url = self.get_connection_url()
            self._connection = psycopg2.connect(url)
            return self._connection
        except Exception as e:
            logger.error(f"Error cerrando conexión: {e}")
    
    def initialize_tables(self) -> bool:
        """Inicializa todas las tablas necesarias en la base de datos"""
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Crear tabla de usuarios
                cursor.execute(self.USERS_TABLE_SQL)
                
                # Crear tabla de logs de actividad
                cursor.execute(self.ACTIVITY_LOGS_TABLE_SQL)
                
                # Crear tabla de sesiones
                cursor.execute(self.USER_SESSIONS_TABLE_SQL)
            
            conn.commit()
            logger.info("Tablas inicializadas correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            return False
            raise
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self._connection and not self._connection.closed:
            self._connection.close()
    
    def create_schema(self) -> bool:
        """Crea las tablas necesarias en la base de datos"""
        schema_sql = """
        -- Tabla de usuarios
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'viewer',
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Tabla de logs de actividad
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            username VARCHAR(50),
            action VARCHAR(200) NOT NULL,
            success BOOLEAN DEFAULT true,
            user_agent TEXT,
            ip_address VARCHAR(45),
            additional_data JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Tabla de sesiones de usuario
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(50),
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Índices para optimizar consultas
        CREATE INDEX IF NOT EXISTS idx_activity_logs_username ON activity_logs(username);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_username ON user_sessions(username);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
        """
        
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            conn.commit()
            logger.info("Schema creado exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error creando schema: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión y retorna información sobre la base de datos"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Información básica
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                
                # Verificar tablas existentes
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name IN ('users', 'activity_logs', 'user_sessions');
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Contar registros en tablas existentes
                counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    counts[table] = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'version': version,
                    'tables': tables,
                    'counts': counts,
                    'url_masked': self.get_connection_url().replace(
                        self.get_connection_url().split('@')[0].split(':')[-1], 
                        '***'
                    )
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()