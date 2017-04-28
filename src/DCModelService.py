# -- coding: utf-8 --

import pymysql
import hashlib
import config

class DCModelService:
    def __init__(self, conn):
        self.conn = conn

    def SearchDriverWithDid(self, did):
        sql = "select * from Driver where did = ?"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (did))
                driver = cursor.fetchone()
        except Exception as e:
            print(str(e))

        return driver

    def SearchDriverWithUsername(self, username):
        sql = "select * from Driver where username = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (username))
                driver = cursor.fetchone()
        except Exception as e:
            print(str(e))

        return driver

    def CreateDriver(self, username, password, name):            
        sql = "insert into Driver (username,password,name) values (%s,%s,%s)"
        try:
            with self.conn.cursor() as cursor:
                search_dup_sql = "select did from Driver where username = %s"
                cursor.execute(search_dup_sql, username)
                count = cursor.rowcount
            if count > 0:
                raise Exception("重复的用户名")

            password = password.encode('utf-8') + config.DRIVER_SALT
            password = hashlib.sha256(password).hexdigest()
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (username, password, name))
                lastrowid = cursor.lastrowid
            self.conn.commit()
        except Exception as e:
            print(str(e))
            return {'status': False, 'msg': str(e)}
        return {'status': True, 'did': lastrowid}

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
