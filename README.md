# Enriscador Web

Herramienta para convertir un sitio web en un tema de WordPress estático.

## Requisitos

- Python 3.8+
- La librería `pywebcopy` incluida en `requirements.txt`

Crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Uso básico

Enriscador Web se organiza en dos subcomandos. Si no se especifica ninguno,
se asume `download` por defecto. El sitio descargado se guarda dentro de una
carpeta `static` y en la raíz se copian los ficheros mínimos de un tema de
WordPress (`index.php`, `style.css` y `functions.php`). El `index.php`
mostrará el contenido de `static/index.html` si existe y devolverá un 404 en caso contrario.
`functions.php` incorpora un pequeño router que, durante
`template_redirect`, comprueba si la ruta solicitada existe dentro de la
carpeta `static` del tema. En tal caso envía el archivo correspondiente
para que los recursos descargados funcionen con sus URLs originales.

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
- `--sanitize` opcional para sanear nombres de archivos (actualmente sin efecto con `pywebcopy`).

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
- `make clean` elimina los entornos generados por `wp-env`.
- `make destroy` borra por completo los contenedores y volúmenes de `wp-env`.
- `make check-plugin` ejecuta el plugin "plugin-check" dentro del entorno para validar el tema.

Con `.wp-env.json` se mapea la carpeta `downloads/` a `wp-content/themes/`, por lo que puedes copiar los temas allí para probarlos ejecutando `make up`.
El archivo también descarga automáticamente el tema oficial "twentytwentyfive" para que siga disponible junto con tus temas generados.

