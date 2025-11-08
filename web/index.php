<?php
$request = trim($_SERVER['REQUEST_URI'], '/');
$request = explode('?', $request)[0];

if ($request === 'auth') {
    include __DIR__ . "/auth.html";
} else {
    http_response_code(404);
    echo "404 - Page Not Found";
}
?>
