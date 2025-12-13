<?php
$request = trim($_SERVER['REQUEST_URI'], '/');
$request = explode('?', $request)[0];

if (strpos($request, '..') === false && ($request === 'src' || str_starts_with($request, 'src/'))) {
    $file_path = __DIR__ . '/' . $request;
    if (file_exists($file_path) && is_file($file_path)) {
        return false;
    }
}

if ($request === '' || $request === 'dashboard') {
    include __DIR__ . '/dashboard.html';
    return;
}

if ($request === 'game') {
    include __DIR__ . '/game.html';
    return;
}

if ($request === 'auth') {
    include __DIR__ . '/auth.html';
    return;
}

if ($request === 'manage-world') {
    include __DIR__ . '/manage_world.html';
    return;
}

if ($request === 'game') {
    include __DIR__ . '/game.html';
    return;
}

if (file_exists(__DIR__ . '/404.html')) {
    http_response_code(404);
    include __DIR__ . '/404.html';
    return;
}

http_response_code(404);
echo '404 - Page Not Found';
?>
