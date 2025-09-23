#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.auth.db_logger import DatabaseLogger

def test_new_video_functions():
    logger = DatabaseLogger()
    
    print("=== TESTING NEW VIDEO FUNCTIONS ===")
    
    try:
        # Probar la nueva función que usa solo base de datos
        players_activity = logger.get_all_players_with_video_activity()
        
        print(f"Total jugadores: {len(players_activity)}")
        
        for username, data in players_activity.items():
            print(f"\n--- {username} ({data['full_name']}) ---")
            print(f"Ha visto videos: {data['has_watched']}")
            print(f"Total visualizaciones: {data['view_count']}")
            print(f"Videos únicos: {data['unique_videos']}")
            if data['video_names']:
                print(f"Videos vistos: {', '.join(data['video_names'])}")
            if data['last_view']:
                print(f"Última visualización: {data['last_view']}")
        
        # Separar por actividad
        with_activity = {k: v for k, v in players_activity.items() if v['has_watched']}
        without_activity = {k: v for k, v in players_activity.items() if not v['has_watched']}
        
        print(f"\n=== RESUMEN ===")
        print(f"Jugadores con actividad: {len(with_activity)}")
        print(f"Jugadores sin actividad: {len(without_activity)}")
        
        if without_activity:
            print("\nJugadores SIN actividad:")
            for username, data in without_activity.items():
                print(f"  - {data['full_name']} ({username})")
        
        if with_activity:
            print("\nJugadores CON actividad:")
            for username, data in with_activity.items():
                print(f"  - {data['full_name']} ({username}) - {data['view_count']} visualizaciones")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_video_functions()