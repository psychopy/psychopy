<?php

// up.php  Jeremy R. Gray, Feb 2012

// receive a file uploaded via POST: limited size, strict base64 check, save outside webroot
// names of the saved files includes upload time and IP address
// html output goes to back psychopy to communicate upload status:
//    good_upload digest | too_big | no_file | bad_base64:<last4chars>
// the usual html error messages (404, 403, and so on) will be sent, but not by this script

// this script goes in a server's webroot
// only tested with apache 2.2.3 on CentOS 5.7 32-bit, php 5.1.6, selinux enforcing, .htaccess basic auth
// might want rate-limiting firewall for internet deployment; keep an eye on disk space

//apache 2.2 Basic auth (sent in clear text). to set up on server, as root:
// # mkdir -p /usr/local/etc/apache
// # htpasswd /usr/local/etc/apache/.htpasswd psychopy # add -c option to create / overwrite
// # chown -R apache:apache /usr/local/etc/apache
// # chmod -R 400 /usr/local/etc/apache
// might need to edit your httpd.conf file to enable auth (& restart apache)
// need to allow POST'ing to your server (and the up.php directory in particular)


$project = 'ppo-'; # for file labels
$max_file_size = 10 * 1024; // in bytes; allow +30% due to base64; 1300 is ~min for upload demo
$final_permissions = 0600; // == the apache/http user, might not be what you want

$targetDir = '/usr/local/psychopy_org/upload/'; # outside of webroot, need final /
#mkdir -p /usr/local/psychopy_org/upload/
#chown -R apache:apache /usr/local/psychopy_org/
#chcon -R user_u:object_r:httpd_sys_content_t /usr/local/psychopy_org/

$digest_name = "sha256";

// name of file on server -> sort order:  project - IP.addr - filename - date.time
$prefix = $project.$_SERVER['REMOTE_ADDR'].'-';

// ensure alpha-numeric (plus '._') file name == legal, no spaces, no ../.htaccesss:
$filename = "file_1"; // must match in _POST, else get 'no_file' status
$fname = preg_replace("/[^A-Za-z0-9._]/", '_', basename($_FILES[$filename]['name']));
$target = $targetDir.$prefix.$fname.'-'.date('Y.m.d.His'); // u for microseconds in php 5.2.2+
while (file_exists($target)) {
    $target = $target.'+'; // ensure unique name
}

if (basename( $_FILES[$filename]['name']) == '') {
    echo "no_file"; }
else { // try to upload it
    if ($_FILES[$filename]["size"] > $max_file_size) {
        echo "too_large";
    }
    else {
        $contents_b64 = file_get_contents($_FILES[$filename]['tmp_name']);
        if (preg_match('%^[a-zA-Z0-9/+]*={0,1,2}$%', $contents_b64)) { // do 'strict'
          echo 'bad_base64:'.substr($contents_b64, -4);
          return; // no file creation
        }
        $contents = base64_decode($contents_b64);
        file_put_contents($target, $contents);
        chmod($target, $final_permissions); 
        $integrity_check = hash_file($digest_name, $target);
        echo 'good_upload '.$integrity_check.' '.filesize($target);
    }
}

?>
