<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">	
<head>
<title>The PsychoPy Wiki - usage statistics</title>
<META NAME="DESCRIPTION" CONTENT="This page contains no content of interest to users, merely a way for psychopy to store usage data">
<META HTTP-EQUIV="CACHE-CONTROL" CONTENT="NO-CACHE">
<META NAME="ROBOTS" CONTENT="NONE"> 
</head>
<body>
<?php$user="psychopy_stat";$host="localhost";$password="ps1ch0p1";
$database="psychopy";
$table="stats02";$connection= mysql_connect($host,$user,$password) or Die("Couldn't connect to server");
@mysql_select_db($database) or die( "Unable to select database");
$date=$_GET['date'];
$date_receipt = date("Y-m-d H:i");
echo(date("Y-m-d H:i"));
$version=$_GET['version'];
$sys=$_GET['sys'];
$misc=$_GET['misc'];
$len = strlen($date);
$host= $_SERVER [ 'REMOTE_ADDR' ] ;

if (strlen($date)>1 ) 
  {
  echo "\n<br>got data<br>";
  //table field format is: id,date,sys,version,misc,date_received
  $query = "INSERT INTO $table VALUES ('','$date','$sys','$version','$misc','$date_received','$host')";
  mysql_query($query)
  or die(mysql_error());
  }
else {  
  $i=1;
  $all=mysql_query("SELECT * FROM $table");
  $tot=mysql_numrows($all);
  $totMachines=mysql_numrows(mysql_query("SELECT DISTINCT(host) FROM $table"));
  $firstDate=substr(mysql_result($all,1,"date"),0,10);        
  echo "<br>Since $firstDate the PsychoPy application has been run $tot times on $totMachines computers<br>";   
  
  $lastMonth=date("Y-m-d_H:i", time()-60*60*24*28);
  $sql="SELECT * FROM $table WHERE date > ('$lastMonth')";
  $monthRuns=mysql_numrows(mysql_query($sql));
  $sql="SELECT DISTINCT(host) FROM $table WHERE date > ('$lastMonth')";
  $monthMachines=mysql_numrows(mysql_query($sql));
  echo "In the last 28 days the PsychoPy application has been run $monthRuns times on $monthMachines computers<br>";
  
  $lastWeek=date("Y-m-d_H:i", time()-60*60*24*7);
  $sql="SELECT * FROM $table WHERE date > ('$lastWeek')";
  $weekRuns=mysql_numrows(mysql_query($sql));
  $sql="SELECT DISTINCT(host) FROM $table WHERE date > ('$lastWeek')";
  $weekMachines=mysql_numrows(mysql_query($sql));
  echo "In the last 7 days the PsychoPy application has been run $weekRuns times on $weekMachines computers<br>";
  echo "NB these stats don't include users that opt out of providing stats or the many that use PsychoPy libraries without the application<hr><br>";
  while ($i <= min($tot,10)) {    
    $id=mysql_result($all,$tot-$i,"id");
    $date=mysql_result($all,$tot-$i,"date");
    $sys=mysql_result($all,$tot-$i,"sys");
    $version=mysql_result($all,$tot-$i,"version");
    $misc=mysql_result($all,$tot-$i,"misc");
    $host=substr(mysql_result($all,$tot-$i,"host"),0,-3)."XXX";
    echo "$id  $date $version    $misc  $host    $sys<br>";
    $i++;
    }
  }
mysql_close();
?>
</body>
</html>