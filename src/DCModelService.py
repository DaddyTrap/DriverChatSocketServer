# -- coding: utf-8 --

import pymysql
import hashlib
import config
import json

class DCModelService:
    def __init__(self, conn):
        self.conn = conn

    def SearchDriverWithDid(self, did):
        sql = "select * from Driver where did = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (did))
                driver = cursor.fetchone()
            self.conn.commit()
        except Exception as e:
            print(str(e))

        return driver

    def SearchDriverWithUsername(self, username):
        sql = "select * from Driver where username = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (username))
                driver = cursor.fetchone()
            self.conn.commit()
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

    def ListRooms(self):
        sql = "select * from Room"
        rooms = []
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                rooms = cursor.fetchall()
                return rooms
            self.conn.commit()
        except Exception as e:
            print(str(e))
            return []

    def SetAvatar(self, did, name):
        sql = "update Driver set avatar = %s where did = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (name, did))
                self.conn.commit()
            return True
        except Exception as e:
            print(str(e))
            return False

    def GetAvatar(self, did):
        sql = "select avatar from Driver where did = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (did))
                name = cursor.fetchone()['avatar']
            return name
            self.conn.commit()
        except Exception as e:
            print(str(e))
            return None

    def SetRoomAvatar(self, rid, name):
        sql = "update Room set avatar = %s where rid = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (name, rid))
                self.conn.commit()
            return True
        except Exception as e:
            print(str(e))
            return False

    def GetRoomAvatar(self, rid):
        sql = "select avatar from Room where rid = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (rid))
                name = cursor.fetchone()['avatar']
            return name
            self.conn.commit()
        except Exception as e:
            print(str(e))
            return None

    def GetBadge(self, did):
        sql = "select badge from Driver where did = %s"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (did))
                badge_json = cursor.fetchone()['badge']
            if badge_json is not None:
                badge = json.loads(badge_json)
                return badge
            else:
                return None
            self.conn.commit()
        except Exception as e:
            print(str(e))
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
