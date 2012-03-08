<?php // --------file sender, to test up.php------------------------- ?>

<form enctype="multipart/form-data" action="up.php" method="POST">
    <input name='file_1' type='file' size='50'><br>
    <br>
    <input type="submit" value="Upload">
</form>

<?php // display file size & name for config debugging:
// fixed version of public domain http://www.jonasjohn.de/snippets/php/listdir-by-date.htm
$path =	'/usr/local/psychopy_org/upload';
$dir = opendir($path);
$dl = array();
while ($file = readdir($dir)) {
    if ($file != '.' and $file != '..') {
        $ctime = filectime($path .'/'. $file) . ',' . $file;
        $dl[$ctime] = $file;
    }
}
closedir($dir);
krsort($dl);
// end listdir-by-date

print '<table border="0" cellpadding="3"><tr><td>bytes</td><td>filename</td></tr>';
foreach ($dl as $d) {
    echo '<td>'.filesize('/usr/local/psychopy_org/upload/'.$d).'</td><td>'.$d.'</td></tr>';
}
?>




