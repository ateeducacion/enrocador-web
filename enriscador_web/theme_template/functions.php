<?php
/**
 * Functions for Enriscador Web generated themes.
 */

/**
 * Simple router that serves files from the theme "static" directory.
 *
 * This allows requests to asset paths like `/style.css` or `/images/foo.png`
 * to be resolved to the downloaded static site bundled with the theme.
 */
function enriscador_static_router() {
    $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    $path = ltrim($path, '/');

    if ($path === '') {
        $path = 'index.html';
    }

    $file = get_template_directory() . '/static/' . $path;
    if (file_exists($file) && !is_dir($file)) {
        $mime = mime_content_type($file);
        if ($mime) {
            header('Content-Type: ' . $mime);
        }
        readfile($file);
        exit;
    }
}
add_action('init', 'enriscador_static_router', 0);

?>
