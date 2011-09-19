<?php

// Outputs file progressively, waits for more if reaches EOF
// Allows to stream during video conversion

// Complete hack 
// FIXME Path is hardcoded
// FIXME Need to validate file_path
$file_path = $_GET['file_path'];
$full_file_path = "/var/www/downloads/series/banners/$file_path";
$url_path = 'http://www.thetvdb.com/banners/'.$file_path;
if(substr($full_file_path, -4) !== '.jpg') {
    exit(0);
}

if(!file_exists($full_file_path)) {
    $fp = fopen($url_path, "r");
    $fp2 = fopen($full_file_path, "w");
} else {
    $fp = fopen($full_file_path, "r");
}

header('Content-type: image/jpeg');
while ($buf = fread($fp, 1024)) {
    echo $buf;

    if($fp2) {
        fwrite($fp2, $buf);
    }
}

fclose($fp);
if($fp2) {
    fclose($fp2);
}


?>
