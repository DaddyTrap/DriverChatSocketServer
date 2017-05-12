import pymysql

import config

g_db_connection = pymysql.connect(**config.DATABASE['main'], cursorclass=pymysql.cursors.DictCursor)

def checkConn(conn):
    sq = "SELECT NOW()"
    try:
        with conn.cursor() as cur:
            cur.execute( sq )
            conn.commit()
    except Exception as e:
        return False
    return True

def get_db_conn():
    global g_db_connection
    if g_db_connection is None or not checkConn(g_db_connection):
        g_db_connection = pymysql.connect(**config.DATABASE['main'], cursorclass=pymysql.cursors.DictCursor)
    return g_db_connection