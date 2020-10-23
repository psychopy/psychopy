REM codesign_and_chk.bat <filename>
REM requires that the dongle is installed and will ask for password too
signtool sign /v /a /tr http://timestamp.comodoca.com /td sha256 /fd sha256 /n "Open Science Tools Limited" %1
signtool verify /v /pa %1