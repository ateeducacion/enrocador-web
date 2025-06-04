# Enriscador Web

Herramienta para convertir un sitio web en un tema de WordPress estático.

## Requisitos

- Python 3.8+
- `wget` instalado en el sistema

Instala las dependencias de Python:

```bash
pip install -r requirements.txt
```

## Uso básico

Enriscador Web se organiza en dos subcomandos:

### Descargar un sitio

```bash
python -m enriscador_web.main download <url> <carpeta_destino> [opciones]
```

Opciones de descarga:

- `--user-agent` User-Agent personalizado.
- `--depth` Profundidad máxima de crawling.
- `--exclude` Lista de dominios a excluir.

### Empaquetar como tema de WordPress

```bash
python -m enriscador_web.main package <carpeta_descarga> <themes/mi_tema> --theme-name MiTema [--url <url_original>]
```

Al empaquetar se copiarán los archivos de una plantilla PHP mínima y se generará `style.css`. También se crea un ZIP del tema para facilitar su distribución.

Ejemplo completo:

```bash
# Descargar el sitio
python -m enriscador_web.main download https://ejemplo.com archivado --depth 1

# Crear el tema
python -m enriscador_web.main package archivado themes/archivado --theme-name MiTema --url https://ejemplo.com
```

## Uso con Makefile

Para facilitar el flujo de trabajo se incluye un `Makefile` sencillo.

- `make download` descarga un sitio de forma interactiva en la carpeta `downloads`.
- `make package` empaqueta todas las descargas de `downloads` como temas WordPress en `themes`.
- `make up` y `make down` inician y detienen un entorno local de WordPress usando `wp-env`.

Con `.wp-env.json` se mapea la carpeta `themes/` a `wp-content/themes/`, por lo que podrás probar los temas empaquetados ejecutando `make up`.

