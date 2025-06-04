<?php
/**
 * Functions for Enriscador Web generated themes.
 */

/**
 * Replace root-relative asset URLs in HTML so they point to this theme's
 * `static` directory.
 */
function enriscador_filter_static_html($html) {
    $base = content_url('themes/' . get_stylesheet() . '/static');
    $domain = parse_url(home_url(), PHP_URL_HOST);
    $html = preg_replace('#https?://' . preg_quote($domain, '#') . '/#', '/', $html);
    $html = preg_replace(
        '#(src|href)="/(?!wp-content/|wp-includes/)([^"\s]+)"#',
        '$1="' . $base . '/$2"',
        $html
    );
    $html = preg_replace(
        '#url\(/(?!wp-content/|wp-includes/)([^)]+)\)#',
        'url(' . $base . '/$1)',
        $html
    );
    return $html;
}

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
        if (in_array($ext, array('html', 'htm'))) {
            echo enriscador_filter_static_html(file_get_contents($file));
        } else {
            readfile($file);
        }
        exit;
    }
}
add_action('template_redirect', 'enriscador_static_router', 0);

?>
