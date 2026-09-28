# Assault Fire Server Emulator

**Idioma:** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [Más idiomas](README-LANGUAGES.md)

Proyecto no oficial para preservar **Assault Fire PH** y emular su servidor. Ni este proyecto ni los servidores operados por terceros están afiliados a Tencent, Level Up! Games o a los titulares originales, ni cuentan con su respaldo. Los servidores comunitarios son independientes.

> **Única versión compatible y probada:** Assault Fire PH **v1.0.0.24**. Este repositorio no incluye los archivos del juego. Debes tener tu propia copia.

## La forma más fácil de empezar

1. Coloca la carpeta completa `af-emulator` dentro de la carpeta del juego Assault Fire PH.
2. Haz clic derecho en `START_ASSAULT_FIRE.ps1` y elige **Run with PowerShell**. Acepta el aviso de administrador si aparece.
3. El lanzador verifica la versión y la configuración, prepara las claves locales y abre el servidor, la ayuda de inicio y el cliente del juego.
4. Inicia sesión en el cliente. Cuando aparezca **START**, haz clic para continuar.

Con el flujo normal de un clic no tienes que iniciar manualmente el servidor ni las herramientas de parcheo. El script no descarga ni redistribuye archivos del juego: solo usa los tuyos. Si la versión no coincide o no se puede verificar la firma de `TGame.exe` o `TCLS.dll`, detente; no fuerces el parche. Antes de iniciar, el lanzador aplica permanentemente el parche verificado de fecha y hora a `TGame.exe`, tras guardar una copia exacta como `TGame.exe.bak`. Si no puede verificar la firma o encontrar un espacio de código seguro, no modifica el archivo.

## Configuración manual y desarrollo

Consulta la [guía completa en inglés](README.md) para ver todos los pasos y comandos exactos. Necesitas Windows, Python 3.10 o posterior y tu propia copia de la versión compatible. En la configuración manual, espera a que la comprobación previa muestre `UNLOCKED`. Si usas el inicio manual, no pulses **START** hasta que la herramienta muestre `TCLS ARMED`. La opción `--server-only` sirve para alojar el servidor; no habilita el inicio local del juego.

## Estado y ayuda

La base estable pública actual es **v143b**. Funcionan las rutas VERSION, AUTH, DIR, ROLE y ZONE, las salas y el flujo de partidas PvE. Siguen en desarrollo la creación inicial de apodo/cuenta y algunas funciones sociales y de progreso. La sincronización inicial de AP del cliente todavía usa una solución local temporal.

Para pedir ayuda, envía una captura del error, el paso que estabas realizando, el comando exacto, `server/af_server_live.log` y la versión del juego. **No envíes** `PRIVATE.PEM`, contraseñas, datos de acceso, tokens ni archivos originales del juego.

- [Estado del proyecto](docs/STATUS.md) · [Errores del lanzador](docs/LAUNCHER_ERRORS.md) · [Notas importantes de instalación](docs/VITAL_SETUP_NOTES.md) · [Índice de documentación](docs/README.md)
- [Todos los README por idioma](README-LANGUAGES.md)

**Licencia:** MIT.
