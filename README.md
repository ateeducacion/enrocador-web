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

Enriscador Web se organiza en dos subcomandos. Si no se especifica ninguno,
se asume `download` por defecto. El sitio descargado se guarda dentro de una
carpeta `static` y en la raíz se copian los ficheros mínimos de un tema de
WordPress (`index.php`, `style.css` y `functions.php`). El `index.php`
mostrará el contenido de `static/index.html`:

### Descargar un sitio

```bash
python -m enriscador_web.main download <url> <carpeta_destino> [opciones]
# O bien, simplemente
python -m enriscador_web.main <url> <carpeta_destino> [opciones]
```

Opciones de descarga:

- `--user-agent` User-Agent personalizado.
- `--depth` Profundidad máxima de crawling.
- `--exclude` Lista de dominios a excluir.
- `--theme-name` Nombre del tema generado.
- `--sanitize` Aplica `--restrict-file-names=windows` para sanear nombres de archivos.
- Si `wget` finaliza con el código `8` debido a recursos que devuelven
  `404`, el proceso continúa y se copian igualmente los ficheros del tema.

### Empaquetar la carpeta descargada

```bash
python -m enriscador_web.main package <carpeta_descarga> [--output paquete.zip]
```

El comando `package` solo comprime la carpeta indicada en un archivo ZIP. Se generará `paquete.zip` en la misma ruta si no se especifica `--output`.

Ejemplo completo:

```bash
# Descargar el sitio (equivalente a usar el subcomando `download`)
python -m enriscador_web.main https://ejemplo.com downloads/archivado --theme-name MiTema --depth 1

# Comprimir para distribuir
python -m enriscador_web.main package downloads/archivado --output downloads/archivado.zip
```

## Uso con Makefile

Para facilitar el flujo de trabajo se incluye un `Makefile` sencillo.

- `make download` descarga un sitio de forma interactiva en la carpeta `downloads`.
- `make package` comprime cada carpeta de `downloads` en un archivo `.zip` con el mismo nombre.
- `make up` y `make down` inician y detienen un entorno local de WordPress usando `wp-env`.

Con `.wp-env.json` se mapea la carpeta `downloads/` a `wp-content/themes/`, por lo que puedes copiar los temas allí para probarlos ejecutando `make up`.
El archivo también descarga automáticamente el tema oficial "twentytwentyfive" para que siga disponible junto con tus temas generados.

