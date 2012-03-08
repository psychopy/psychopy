<?php

// this is a version of up.php to allow anyone anywhere to test against my server
// using psychopy coder/demo/misc/http_upload.py
// it works the same as up.php except that no file is saved on my machine
// JRG note to self: put in webroot/upload_test/up_no_save.php

require('../psychopy_org/up.php'); # run up.php
unlink($target); # remove the saved file
print ' (demo only, not saved)';

?>