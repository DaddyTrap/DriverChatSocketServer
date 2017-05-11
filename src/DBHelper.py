import pymysql

import config

g_db_connection = pymysql.connect(**config.DATABASE['main'], cursorclass=pymysql.cursors.DictCursor)

def get_db_conn():
    if g_db_connection is None or not g_db_connection.open:
        g_db_connection = pymysql.connect(**config.DATABASE['main'], cursorclass=pymysql.cursors.DictCursor)
    return g_db_connection