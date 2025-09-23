#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.auth.db_logger import DatabaseLogger

def test_video_functions():
    logger = DatabaseLogger()
    
    print("=== TESTING VIDEO FUNCTIONS ===")
    
    # Probar usuarios específicos
    test_users = ['jose_luis_ayala', 'carlos_barros']
    
    for username in test_users:
        print(f"\n--- Testing {username} ---")
        
        try:
            # Verificar si tiene videos disponibles
            has_videos = logger.user_has_videos_available(username)
            print(f"Tiene videos disponibles: {has_videos}")
            
            # Verificar si ha visto videos
            has_watched = logger.has_user_watched_videos(username)
            print(f"Ha visto videos: {has_watched}")
            
        except Exception as e:
            print(f"Error con {username}: {e}")
    
    print("\n=== TESTING GET_USERS_WITHOUT_VIDEO_VIEWS ===")
    try:
        users_without_views = logger.get_users_without_video_views()
        print(f"Usuarios sin ver videos: {users_without_views}")
        print(f"Total: {len(users_without_views)}")
    except Exception as e:
        print(f"Error obteniendo usuarios sin vistas: {e}")

if __name__ == "__main__":
    test_video_functions()