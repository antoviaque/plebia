<?php

// Outputs file progressively, waits for more if reaches EOF
// Allows to stream during video conversion

// Complete hack 
// FIXME Path is hardcoded
// FIXME Need to validate file_path
$file_path = $_GET['file_path'];
$full_file_path = "/var/www/downloads/$file_path";
if(substr($full_file_path, -5) !== '.webm' || !file_exists($full_file_path)) {
    exit(0);
}

$fp = fopen($full_file_path, "r");
while (true) {
    set_time_limit(10);
    $buf = fread($fp, 1024);
    echo $buf;
    usleep(4000); // 1kB every 0.004s (4000) = 250 kB/s = 2 Mbps
}
fclose($fp);


?>
