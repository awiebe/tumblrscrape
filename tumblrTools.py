from __future__ import print_function

from posixpath import basename, dirname
from datetime import date, datetime, timedelta
import mysql.connector
import os





class TumblrPost:
    def __init__(self):
        self.id = None
        self.title = None
        self.description = None
        self.tags = None
        self.timestamp = None
        self.source = None


class TumblrDB:
    start_task_sql = ("INSERT INTO PULL_TASK "
                  "(user_id,progress,progress_max,started_at,timeout_at,pid,running) "
                  "VALUES(%(uid)s, 0, %(progress_max)s,%(from)s,%(to)s,%(pid)s,1)")

    delete_task = ("DELETE FROM PULL_TASK WHERE tid = %(tid)s ")
    selected_task_timedout = "SELECT tid,pid FROM TASK WHERE completed_at IS NULL AND timeout_at < DATE(%s) "
    flag_task_timeout_running_sql = "UPDATE TASK SET RUNNING=0 WHERE tid=%s"

    update_user_referenced_sql = ("UPDATE USER SET reference_count=%s + reference_count WHERE id=%s")
    create_user_sql = 'INSERT IGNORE INTO USER(name) VALUES( %s )'
    update_user_last_pulled_sql = "UPDATE USER SET last_pulled=%s WHERE id=%s"

    create_file = ("INSERT IGNORE INTO FILE(dirname,basename) VALUES (%s, %s) " )

    create_post_sql = "INSERT INTO POST(id,user_id,text,unix_time) VALUES(%s,%s,%s,%s)"
    associate_file_sql = ("INSERT IGNORE INTO POST_FILE(post_id,file_id) VALUES (%s, %s)")


    def __init__(self,host,user,dbname,password=''):
        # note autocommit off by default
        self.cnx = mysql.connector.connect(host=host, user=user, database=dbname,
                                           password=password)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cnx.close();

    def createUser(self, username):
        cursor = self.cnx.cursor()
        cursor.execute(self.create_user_sql, (username,))
        cursor.close()
        return cursor.lastrowid

    def addPostWithFiles(self, post, uid, files):
        cursor = self.cnx.cursor()
        luid = uid
        pid = post.id
        t = post.timestamp
        d = post.description
        try:
            cursor.execute(self.create_post_sql, (pid , luid, d, t))
        except mysql.connector.errors.IntegrityError as err :

            cursor.close()
            return

        postid = cursor.lastrowid

        # associate files
        for f in files:
            cursor.execute(self.create_file, (dirname(f), basename(f)) )
            fid = cursor.lastrowid
            cursor.execute(self.associate_file_sql, (postid, fid))
        cursor.close()

    def get_uid(self, user):
        cursor = self.cnx.cursor()
        cursor.execute("SELECT id from USER where name = %s ", (user,));
        luid = None
        for t in cursor:
            luid = t[0]

        cursor.close()
        return luid

    def getUserModified(self,uid):

        if(uid == None):
            return -9999999
        cursor = self.cnx.cursor()
        cursor.execute("SELECT UNIX_TIMESTAMP(last_pulled) from USER where id = %s ", (uid,));
        tt = None
        for t in cursor:
            tt = t[0]
        return int(tt)




    def bumpReferenceCounts(self, d):
        assert (isinstance(d, dict))

        for e in d.keys():
            self.bumpReferenceCount(e, d[e])

    def start_ask(self, username,progress_max,timeout_hours):
        timeout = datetime.now().date() + timedelta(hours=timeout_hours)
        d = dict()
        d["uid"]= self.get_uid(username)
        d["progress_max"]=progress_max
        d["uid"] = self.get_uid(username)
        d["pid"] = os.getpid()
        d["from"]= datetime.now().date()
        d["to"] = timeout
        cursor = self.cnx.cursor()
        cursor.execute(self.start_task_sql,d)
        cursor.close()




    def bump_timeout(self,tid,seconds):
        raise Exception("Only setting timeout supported right now");
        #timeout = datetime.now().date() + timedelta(days=1)

    def set_timeout(self,tid,date):
        cursor =self.cnx.cursor()
        cursor.execute("UPDATE TASK SET timeout_At=%s WHERE tid=%s", (date.date(),tid) )
        cursor.close


    def end_task(self, tid):
        cursor = self.cnx.cursor()
        cursor.execute("UPDATE TASK SET COMPLETED_AT=%s, RUNNING=%s", (datetime.now().date(),0) );

        for (uid) in cursor.execute("SELECT uid FROM TASK WHERE id=%s", (tid,) ):
            self.bumpUserModified(uid)
        cursor.close()

    def bumpUserModified(self,uid):
        cursor = self.cnx.cursor()
        cursor.execute(self.update_user_last_pulled_sql, (datetime.now(), uid))
        cursor.close()

    def bumpReferenceCount(self, username, qty):
        cursor = self.cnx.cursor()
        uid =self.get_uid(username)
        if uid == None:
            self.createUser(username)
        cursor.execute(self.update_user_referenced_sql, ( qty,uid))
        cursor.close()

    def commit(self):
        self.cnx.commit();

    def check_pid(pid):
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def check_timeout(self):

        csr = self.cnx.cursor()
        for t in csr.execute(self.selected_task_timedout):
            if not self.check_pid(t.pid):
                csr.execute(self.flag_task_timeout_running_sql, 0)
        csr.close()


