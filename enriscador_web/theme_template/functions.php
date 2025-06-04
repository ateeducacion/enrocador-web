<?php
/**
 * Functions for Enriscador Web generated themes.
 */

/**
 * Serve static assets stored in the theme's `static` folder.
 *
 * Requests to paths like `/style.css` or `/images/foo.png` will be
 * resolved against the downloaded site without modifying the HTML.
 * Runs on `template_redirect` so WordPress routing is already set up.
 */
function enriscador_static_router() {
    if (is_admin()) {
        return;
    }

    $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    $path = ltrim($path, '/');

    if ($path === '') {
        // Home page is handled by index.php
        return;
    }

    $file = get_stylesheet_directory() . '/static/' . $path;
    if (is_file($file)) {
        $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
        $types = wp_get_mime_types();
        if (isset($types[$ext]) && !headers_sent()) {
            header('Content-Type: ' . $types[$ext]);
        }
        readfile($file);
        exit;
    }
}
add_action('template_redirect', 'enriscador_static_router', 0);

?>
