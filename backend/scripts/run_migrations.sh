#!/bin/bash

# Script helper para ejecutar migraciones de Alembic dentro de Docker
# Uso: ./scripts/run_migrations.sh [comando] [opciones]

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Script Helper para Alembic en Docker${NC}"
    echo ""
    echo "Uso: $0 [comando] [opciones]"
    echo ""
    echo "Comandos disponibles:"
    echo "  current              - Ver estado actual de migraciones"
    echo "  history              - Ver historial de migraciones"
    echo "  upgrade [revision]   - Aplicar migraciones (por defecto: head)"
    echo "  downgrade [revision] - Rollback a revisión específica"
    echo "  revision [opciones]  - Crear nueva migración"
    echo "  help                 - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 current"
    echo "  $0 upgrade"
    echo "  $0 downgrade -1"
    echo "  $0 revision --autogenerate -m 'Agregar tabla productos'"
    echo ""
    echo -e "${YELLOW}Nota: Este script ejecuta Alembic dentro del contenedor Docker${NC}"
}

# Verificar si Docker está corriendo
check_docker() {
    if ! docker ps | grep -q backend_FastOps; then
        echo -e "${RED}Error: El contenedor 'backend_FastOps' no está corriendo${NC}"
        echo "Ejecuta: docker-compose up -d"
        exit 1
    fi
}

# Función principal
main() {
    local comando="$1"
    shift  # Remover el primer argumento

    case "$comando" in
        current|history|upgrade|downgrade|revision)
            check_docker
            echo -e "${BLUE}Ejecutando: alembic $comando $@${NC}"
            docker exec -it backend_FastOps python -m alembic "$comando" "$@"
            ;;
        help|"")
            show_help
            ;;
        *)
            echo -e "${RED}Error: Comando '$comando' no reconocido${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal con todos los argumentos
main "$@"
