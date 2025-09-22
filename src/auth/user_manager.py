# src/auth/user_manager.py
# -*- coding: utf-8 -*-
"""
Gestor de usuarios para el sistema de autenticación
"""
import json
import hashlib
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class UserManager:
    """Gestiona usuarios, contraseñas y roles"""
    
    def __init__(self, users_file_path: str = "data/auth/users.json"):
        self.users_file = Path(users_file_path)
        self.users_data = self._load_users()
    
    def _load_users(self) -> Dict:
        """Carga los usuarios desde el archivo JSON"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            else:
                # Crear estructura inicial
                initial_data = {
                    "users": {},
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
                self._save_users(initial_data)
                return initial_data
        except Exception as e:
            print(f"Error loading users: {e}")
            return {
                "users": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_users(self, data: Dict = None) -> bool:
        """Guarda los usuarios en el archivo JSON"""
        try:
            if data is None:
                data = self.users_data
            
            data["last_updated"] = datetime.now().isoformat()
            
            # Crear directorio si no existe
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.users_data = data
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash de la contraseña usando SHA-256 con salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verifica si la contraseña coincide con el hash almacenado"""
        try:
            salt, password_hash = stored_hash.split(':', 1)
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def generate_random_password(self, length: int = 12) -> str:
        """Genera una contraseña aleatoria"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for i in range(length))
    
    def create_user(self, username: str, password: str, role: str = "user", 
                   full_name: str = "", email: str = "") -> Tuple[bool, str]:
        """
        Crea un nuevo usuario
        
        Args:
            username: Nombre de usuario único
            password: Contraseña en texto plano
            role: Rol del usuario ('admin' o 'user')
            full_name: Nombre completo opcional
            email: Email opcional
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        # Validar entrada
        if not username or len(username) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres"
        
        if not password or len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        
        if role not in ["admin", "user"]:
            return False, "El rol debe ser 'admin' o 'user'"
        
        # Verificar que el usuario no exista
        if username in self.users_data["users"]:
            return False, f"El usuario '{username}' ya existe"
        
        # Crear usuario
        user_data = {
            "username": username,
            "password_hash": self._hash_password(password),
            "role": role,
            "full_name": full_name or username.title(),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True,
            "login_count": 0
        }
        
        self.users_data["users"][username] = user_data
        
        if self._save_users():
            return True, f"Usuario '{username}' creado exitosamente"
        else:
            return False, "Error al guardar el usuario"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Autentica un usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            Tuple[bool, Optional[Dict]]: (éxito, datos del usuario)
        """
        if username not in self.users_data["users"]:
            return False, None
        
        user = self.users_data["users"][username]
        
        # Verificar si el usuario está activo
        if not user.get("is_active", True):
            return False, None
        
        # Verificar contraseña
        if self._verify_password(password, user["password_hash"]):
            # Actualizar estadísticas de login
            user["last_login"] = datetime.now().isoformat()
            user["login_count"] = user.get("login_count", 0) + 1
            self._save_users()
            
            # Retornar datos del usuario sin la contraseña
            user_data = user.copy()
            del user_data["password_hash"]
            return True, user_data
        
        return False, None
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Obtiene los datos de un usuario sin la contraseña"""
        if username in self.users_data["users"]:
            user_data = self.users_data["users"][username].copy()
            del user_data["password_hash"]
            return user_data
        return None
    
    def list_users(self) -> List[Dict]:
        """Lista todos los usuarios sin las contraseñas"""
        users_list = []
        for username, user_data in self.users_data["users"].items():
            user_copy = user_data.copy()
            del user_copy["password_hash"]
            users_list.append(user_copy)
        return users_list
    
    def deactivate_user(self, username: str) -> Tuple[bool, str]:
        """Desactiva un usuario (no lo elimina)"""
        if username not in self.users_data["users"]:
            return False, f"El usuario '{username}' no existe"
        
        self.users_data["users"][username]["is_active"] = False
        
        if self._save_users():
            return True, f"Usuario '{username}' desactivado exitosamente"
        else:
            return False, "Error al desactivar el usuario"
    
    def activate_user(self, username: str) -> Tuple[bool, str]:
        """Reactiva un usuario"""
        if username not in self.users_data["users"]:
            return False, f"El usuario '{username}' no existe"
        
        self.users_data["users"][username]["is_active"] = True
        
        if self._save_users():
            return True, f"Usuario '{username}' activado exitosamente"
        else:
            return False, "Error al activar el usuario"
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Elimina completamente un usuario"""
        if username not in self.users_data["users"]:
            return False, f"El usuario '{username}' no existe"
        
        del self.users_data["users"][username]
        
        if self._save_users():
            return True, f"Usuario '{username}' eliminado exitosamente"
        else:
            return False, "Error al eliminar el usuario"
    
    def reset_password(self, username: str, new_password: str = None) -> Tuple[bool, str, str]:
        """
        Resetea la contraseña de un usuario
        
        Returns:
            Tuple[bool, str, str]: (éxito, mensaje, nueva_contraseña)
        """
        if username not in self.users_data["users"]:
            return False, f"El usuario '{username}' no existe", ""
        
        if new_password is None:
            new_password = self.generate_random_password()
        
        if len(new_password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres", ""
        
        self.users_data["users"][username]["password_hash"] = self._hash_password(new_password)
        
        if self._save_users():
            return True, f"Contraseña de '{username}' reseteada exitosamente", new_password
        else:
            return False, "Error al resetear la contraseña", ""
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas básicas de usuarios"""
        total_users = len(self.users_data["users"])
        active_users = sum(1 for user in self.users_data["users"].values() if user.get("is_active", True))
        admin_users = sum(1 for user in self.users_data["users"].values() if user.get("role") == "admin")
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "regular_users": total_users - admin_users,
            "last_updated": self.users_data.get("last_updated")
        }