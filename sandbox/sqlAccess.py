import MySQLdb
db = MySQLdb.connect(host="localhost", user="psychopy_stat",
    passwd="ps1ch0p1", db="psychopy")
cursor = db.cursor()
sql = """SELECT * FROM stats02"""
cursor.execute(sql)
data = cursor.fetchone()
db.close()