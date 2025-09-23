#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.utils.video_manager import video_manager

def test_video_manager():
    print("=== TESTING VIDEO MANAGER ===")
    
    # Verificar si Google Drive está autenticado
    try:
        is_auth = video_manager.drive_client.is_authenticated()
        print(f"Google Drive autenticado: {is_auth}")
        
        if not is_auth:
            print("⚠️ Google Drive no está autenticado!")
            return
        
        # Verificar carpeta PINTOBASKET
        pintobasket_id = video_manager._get_folder_id('PINTOBASKET')
        print(f"ID carpeta PINTOBASKET: {pintobasket_id}")
        
        if pintobasket_id:
            # Listar archivos en PINTOBASKET
            files = video_manager._list_files_in_folder(pintobasket_id)
            print(f"Archivos en PINTOBASKET: {len(files)}")
            
            for file in files:
                print(f"  - {file['name']} (ID: {file['id']})")
                
            # Probar usuarios específicos
            test_users = ['jose_luis_ayala', 'carlos_barros']
            
            for username in test_users:
                print(f"\n--- Videos para {username} ---")
                user_videos = video_manager.get_user_videos(username)
                print(f"Videos encontrados: {len(user_videos)}")
                for video in user_videos:
                    print(f"  - {video.get('name', 'Sin nombre')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_manager()