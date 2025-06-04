# Enriscador Web

Herramienta para convertir un sitio web en un tema de WordPress estático.

## Requisitos

- Python 3.8+
- Las librerías `pywebcopy` y `html2image` incluidas en `requirements.txt`

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
carpeta `static` del tema sin modificar las URLs.
Si se trata de un HTML se inyecta una etiqueta `<base>` que apunta a esa carpeta,
por lo que las rutas relativas de estilos, imágenes o scripts funcionan correctamente.
El router también envía la cabecera `charset=UTF-8` para evitar caracteres extraños.
Durante la descarga los archivos HTML se recodifican a UTF-8 para que el texto
se muestre correctamente sin importar el charset original.
Además se crea automáticamente un `screenshot.png` usando la librería
`html2image` para que WordPress muestre una vista previa del tema.
Mientras PyWebCopy trabaja se muestra un pequeño mensaje "Descargando..." en la
consola para indicar que el proceso sigue en curso.

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

- `make` o `make help` muestra las opciones disponibles.
Al ejecutar `make` sin argumentos se mostrará esta misma ayuda.

- `make download` descarga un sitio de forma interactiva en la carpeta `downloads`.
- `make package` comprime cada carpeta de `downloads` en un archivo `.zip` con el mismo nombre.
- `make up` y `make down` inician y detienen un entorno local de WordPress usando `wp-env`.
- `make clean` elimina los entornos generados por `wp-env`.
- `make destroy` borra por completo los contenedores y volúmenes de `wp-env`.
- `make check-plugin` ejecuta el plugin "plugin-check" dentro del entorno para validar el tema.
- `make install` instala Python (en Windows via winget si es necesario) y crea un entorno virtual `env` con sus dependencias.

Con `.wp-env.json` se mapea la carpeta `downloads/` a `wp-content/themes/`, por lo que puedes copiar los temas allí para probarlos ejecutando `make up`.
El archivo también descarga automáticamente el tema oficial "twentytwentyfive" para que siga disponible junto con tus temas generados.

