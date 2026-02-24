import pymysql

# Fake the version number to trick Django into thinking it's newer
pymysql.version_info = (2, 2, 6, "final", 0)

pymysql.install_as_MySQLdb()
