<?php
$request = trim($_SERVER['REQUEST_URI'], '/');
$request = explode('?', $request)[0];

if ($request === '' || $request === 'dashboard') {
    include __DIR__ . '/dashboard.html';
    return;
}

if ($request === 'auth') {
    include __DIR__ . '/auth.html';
    return;
}

if ($request === 'manage-world') {
    include __DIR__ . '/manage-world.html';
    return;
}

http_response_code(404);
echo '404 - Page Not Found';
?>
