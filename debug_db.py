#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.auth.database import db_manager
import json

def debug_activity_logs():
    try:
        conn = db_manager.get_connection()
        with conn.cursor() as cursor:
            # Verificar estructura de la tabla
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'activity_logs'
                ORDER BY ordinal_position
            """)
            
            print('=== ESTRUCTURA DE activity_logs ===')
            for row in cursor.fetchall():
                print(f'{row[0]}: {row[1]}')
            
            print('\n=== MUESTRA DE DATOS DE VIDEO ===')
            cursor.execute("""
                SELECT username, action, log_type, additional_data
                FROM activity_logs 
                WHERE action = 'video_view' 
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                print(f'Usuario: {row[0]}, Acción: {row[1]}, Tipo: {row[2]}')
                if row[3]:
                    print(f'  Datos adicionales: {row[3]}')
                print('---')
            
            # Verificar específicamente para carlos_barros y jose_luis_ayala
            print('\n=== DATOS ESPECÍFICOS CARLOS_BARROS ===')
            cursor.execute("""
                SELECT action, log_type, additional_data, created_at
                FROM activity_logs 
                WHERE username = 'carlos_barros'
                ORDER BY created_at DESC
                LIMIT 3
            """)
            
            for row in cursor.fetchall():
                print(f'Acción: {row[0]}, Tipo: {row[1]}, Fecha: {row[3]}')
                if row[2]:
                    print(f'  Datos: {row[2]}')
                print('---')
                
            print('\n=== DATOS ESPECÍFICOS JOSE_LUIS_AYALA ===')
            cursor.execute("""
                SELECT action, log_type, additional_data, created_at
                FROM activity_logs 
                WHERE username = 'jose_luis_ayala'
                ORDER BY created_at DESC
                LIMIT 3
            """)
            
            for row in cursor.fetchall():
                print(f'Acción: {row[0]}, Tipo: {row[1]}, Fecha: {row[3]}')
                if row[2]:
                    print(f'  Datos: {row[2]}')
                print('---')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_activity_logs()