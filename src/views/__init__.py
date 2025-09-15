# src/views/__init__.py
"""
Vistas de la aplicación Scouting Hub
"""

from .home import view_home
from .team import view_team
from .reports import view_equipo_informe, view_jugador_informe
from .players import view_players

__all__ = [
    'view_home',
    'view_team',
    'view_equipo_informe',
    'view_jugador_informe',
    'view_players'
]