<?php
// Auto generated by enrocador Web
$index = __DIR__ . '/static/index.html';
if (is_file($index)) {
    if (function_exists('enrocador_filter_static_html')) {
        echo enrocador_filter_static_html(file_get_contents($index));
    } else {
        readfile($index);
    }
} else {
    status_header(404);
    echo 'Static index not found';
}
?>
