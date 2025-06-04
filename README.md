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

```bash
python -m enriscador_web.main <url> <carpeta_salida> [opciones]
```

Opciones principales:

- `--theme-name` Nombre del tema WordPress a crear.
- `--user-agent` User-Agent personalizado para la descarga.
- `--depth` Profundidad máxima de crawling.
- `--exclude` Lista de dominios a excluir.

Ejemplo:

```bash
python -m enriscador_web.main https://ejemplo.com archivado --theme-name MiTema --depth 2
```

La carpeta `archivado` contendrá la descarga original y el tema WordPress generado.
