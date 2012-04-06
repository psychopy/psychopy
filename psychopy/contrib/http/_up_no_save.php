<?php

// this is a non-saving version of up.php to allow testing against my server
// by anyone anywhere using their psychopy coder/demo/misc/http_upload.py
// it calls up.php (= file uploaded, digest calc'd, etc) then the file is deleted
// JRG note to self: put in webroot/upload_test/up_no_save.php

require('../psychopy_org/up.php'); # run up.php
unlink($target); # remove the saved file
print ' demo_no_save'; # appended to up.php output if that runs to completion

?>