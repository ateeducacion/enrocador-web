<?php
/**
 * Functions for Enriscador Web generated themes.
 */

/**
 * Replace root-relative asset URLs in HTML so they point to this theme's
 * `static` directory.
 */
function enriscador_filter_static_html($html) {
    $base = trailingslashit(content_url('themes/' . get_stylesheet() . '/static'));
    $domain = parse_url(home_url(), PHP_URL_HOST);

    // Convert absolute URLs of this site to relative paths
    $html = preg_replace('#https?://' . preg_quote($domain, '#') . '/#i', '', $html);

    // Make root-relative references relative so <base> works
    $html = preg_replace(
        '#(src|href)="/(?!wp-content/|wp-includes/)([^"\s]+)"#i',
        '$1="$2"',
        $html
    );
    $html = preg_replace(
        '#url\(/(?!wp-content/|wp-includes/)([^)]+)\)#i',
        'url($1)',
        $html
    );

    // Insert or replace <base> so resources resolve to the static folder
    if (preg_match('#<base[^>]*>#i', $html)) {
        $html = preg_replace('#<base[^>]*>#i', '<base href="' . $base . '">', $html, 1);
    } elseif (preg_match('#<head[^>]*>#i', $html)) {
        $html = preg_replace('#<head([^>]*)>#i', '<head$1><base href="' . $base . '">', $html, 1);
    }

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
    if (!is_file($file)) {
        $index = rtrim($file, '/') . '/index.html';
        if (is_file($index)) {
            $file = $index;
        }
    }
    if (is_file($file)) {
        $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
        $types = wp_get_mime_types();
        if (isset($types[$ext]) && !headers_sent()) {
            $type = $types[$ext];
            if (in_array($ext, array('html', 'htm'))) {
                $type .= '; charset=UTF-8';
            }
            header('Content-Type: ' . $type);
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
