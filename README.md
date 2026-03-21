# Chusmeator 📍

<p align="center">
  <img src="frontend/src/assets/logo.png" alt="Chusmeator Logo" width="200"/>
</p>

**Chusmeator** es una plataforma comunitaria interactiva que permite a los usuarios visualizar y compartir información local sobre su entorno a través de un mapa dinámico.

## 🚀 ¿En qué consiste?

La aplicación permite a los usuarios:
- **Colocar Pines**: Marcar puntos específicos de interés o incidencias en el mapa.
- **Definir Áreas**: Delimitar zonas de interés, barrios o regiones específicas.
- **Búsqueda Inteligente**: Localizar direcciones y lugares rápidamente.
- **Moderación y Privacidad**: Sistema de gestión de contenidos y perfiles de usuario.

---

## 🛠️ Aspectos Técnicos

La arquitectura de **Chusmeator** está diseñada para ser moderna, rápida y escalable.

### Backend (Python/FastAPI)
- **FastAPI**: Un framework de alto rendimiento para construir APIs con Python.
- **Gestión de Dependencias**: Utiliza `uv` para una instalación y manejo de paquetes extremadamente veloz.
- **Base de Datos**: Soporte para **SQLite** (por defecto) y **PostgreSQL**.
- **Autenticación**: Validación basada en identificadores únicos por sesión.

### Frontend (React/Vite)
- **React**: Interfaz de usuario reactiva y componente-céntrica.
- **Vite**: Herramienta de construcción de última generación para una experiencia de desarrollo fluida.
- **Mapas Interactivos**: Integración fluida para visualizar pines y polígonos.

### Infraestructura
- **Docker**: Servicios completamente contenedorizados para un despliegue sencillo en cualquier entorno.
- **Docker Compose**: Orquestación de contenedores para levantar el proyecto completo con un solo comando.

---

## 🏗️ Estructura del Proyecto

- `/frontend`: Aplicación web moderna en React.
- `/backend`: API RESTful construida con FastAPI.
- `/docker-compose.yml`: Configuración para levantar el entorno completo.

---

*Desarrollado con ❤️ para la comunidad.*
