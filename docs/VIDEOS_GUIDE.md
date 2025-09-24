# Guía para el staff — Gestión de videos (Scouting Hub)

Esta guía explica dónde subir los videos, cómo nombrarlos, qué formatos son soportados y quién puede ver qué videos en la aplicación Scouting Hub.

## Resumen rápido

- Carpeta principal para videos de usuario: `PINTOBASKET/`
- Carpeta para videos compartidos generales: `PINTOBASKET/videos/`
- Carpetas por equipo: cada equipo tiene su carpeta raíz con subcarpetas `videos/` y `jugadores/`.

## Dónde subir los videos

- Videos **personales** (mis videos de análisis):

  - Subir a la carpeta raíz `PINTOBASKET/`.
  - Nombre recomendado: `{username}.mp4` (ej.: `david_sanchez.mp4`).
  - Los videos con este nombre se mostrarán automáticamente en la sección "Mis Videos" del usuario cuyo `username` coincida con el nombre del archivo.
- Videos compartidos para **todos los jugadores PINTOBASKET**:

  - Subir a la subcarpeta `PINTOBASKET/videos/`.
  - Nombres recomendados: descriptivos con `_` como separador (ej.: `off_pinto.mp4`, `deff_pinto.mp4`, `mejores_goles_de_cr7.mp4`).
  - Estos videos aparecerán en la sección "Videos compartidos" de la vista "Mis Videos" y estarán disponibles para todos los jugadores/entrenadores.
- Videos por equipo y por jugador (equipos rivales):

  - Cada **equipo rival** tiene una carpeta principal (nombre del equipo). Dentro tiene las subcarpetas:
    - `videos/` (videos del equipo en general)
    - `jugadores/` (videos por jugador; el nombre del video debe coincidir con el nombre del informe o el slug del jugador)
  - Para **videos de jugador rivales**, nombre recomendado: `NOMBRE_APELLIDOS.mp4` (en mayúsculas o minúsculas, la app compara en MAYÚSCULAS internamente para robustez).

## Formatos y extensiones soportadas

La aplicación soporta los siguientes formatos:

- `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`

Recomendaciones:

- Preferir `.mp4` por compatibilidad.
- Incluir audio y evitar códecs exóticos.
- Mantener nombres de archivo ASCII/UTF-8; usar `_` para separar palabras.

## Convenciones de nombres

- Usuarios personales: `{username}.{ext}` (ej.: `mike_sanz.mp4`).
- Compartidos: `tema_descriptivo_YYYYMMDD.ext` o `nombre_evento.ext`.
- Jugadores rivales: `NOMBRE_APELLIDOS.ext` o `slug_jugador.ext`. La app comprobará el stem del archivo en MAYÚSCULAS para emparejar con los informes.

## Quién puede ver qué

- Entrenadores:

  - Pueden ver todos los videos de equipos rivales (`team/videos` y `team/jugadores`).
  - Pueden ver los videos compartidos de `PINTOBASKET/videos` y los videos personales de usuarios si tienen permisos administrativos.
- Jugadores (usuarios PINTOBASKET):

  - Ven sus propios videos personales (archivos en `PINTOBASKET/` que coincidan con su username).
  - Ven los videos compartidos en `PINTOBASKET/videos/` (se muestran en "Mis Videos").
  - Pueden ver videos de equipos rivales en la sección de equipos/jugadores según la UI.
