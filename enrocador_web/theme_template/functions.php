<?php
/**
 * Functions for enrocador Web generated themes.
 */

/**
 * Replace root-relative asset URLs in HTML so they point to this theme's
 * `static` directory.
 */
function enrocador_filter_static_html($html) {
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
 * Includes protections against spam URL parameters, path traversal, and unsafe file types.
 */
function enrocador_static_router() {
    if (is_admin()) {
        return;
    }

    // --- PROTECT AGAINST MALICIOUS QUERY PARAMETERS ---
    $path_clean = strtok($_SERVER['REQUEST_URI'], '?');
    $query_string = $_SERVER['QUERY_STRING'] ?? '';

    if ($query_string !== '') {
        header('Location: ' . $path_clean, true, 301);
        exit();
    }

    $path = ltrim($path_clean, '/');
    if ($path === '') {
        return;
    }

    // --- PATH TRAVERSAL PROTECTION ---
    $static_dir = get_stylesheet_directory() . '/static/';
    $requested_file = $static_dir . $path;

    $base_path = realpath($static_dir);
    $real_file_path = realpath($requested_file);

    if ($real_file_path === false || strpos($real_file_path, $base_path) !== 0) {
        status_header(404);
        return;
    }

    // --- FILE EXTENSION SAFELIST (ALLOW ONLY THESE TYPES) ---
    $allowed_extensions = array(
        'html', 'htm', 'css', 'js',
        'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg',
        'woff', 'woff2', 'ttf', 'eot', 'otf',
        'mp4', 'webm', 'ogg',
        'pdf', 'zip', 'rar', 'tar', 'gz', '7z',
        'json', 'xml'
    );

    $ext = strtolower(pathinfo($real_file_path, PATHINFO_EXTENSION));

    if (!in_array($ext, $allowed_extensions)) {
        // Block any disallowed file types
        status_header(403);
        echo 'Forbidden';
        exit;
    }

    // --- FILE SERVING LOGIC ---
    if (is_file($real_file_path)) {
        $types = wp_get_mime_types();
        if (isset($types[$ext]) && !headers_sent()) {
            $type = $types[$ext];
            if (in_array($ext, array('html', 'htm'))) {
                $type .= '; charset=UTF-8';
            }
            header('Content-Type: ' . $type);
        }

        if (in_array($ext, array('html', 'htm'))) {
            echo enrocador_filter_static_html(file_get_contents($real_file_path));
        } else {
            readfile($real_file_path);
        }
        exit;
    }
}

add_action('template_redirect', 'enrocador_static_router', 0);
