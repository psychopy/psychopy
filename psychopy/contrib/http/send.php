<?php // --------file sender, to test up.php------------------------- ?>

<form enctype="multipart/form-data" action="up.php" method="POST">
    <input name='file_1' type='file' size='50'><br>
    <br>
    <input type="submit" value="Upload">
</form>

<?php // display file size & name for config debugging:
echo '[bytes] __filename__<br>';
$dl = scandir('/usr/local/psychopy_org/upload',1);
foreach ($dl as $d) {
  echo '['.filesize('/usr/local/psychopy_org/upload/'.$d).'] '.$d.'<br>';
}
?>


