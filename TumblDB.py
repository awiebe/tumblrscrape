from __future__ import print_function

from posixpath import basename, dirname
from datetime import date, datetime, timedelta
import mysql.connector
import os





class TumblrPost:
    def __init__(self):
        self.title = None
        self.description = None
        self.tags = None
        self.timestamp = None
        self.source = None


class TumblDB:
    start_task_sql = ("INSERT INTO pull_task "
                  "(user_id,progress,progress_max,started_at,timeout_at,pid,running) "
                  "VALUES(%(uid)s, 0, %(progress_max)s,%(from)s,%(to)s,%(pid)s,1)")

    delete_task = ("DELETE FROM employees WHERE tid = %(tid)s ")
    selected_task_timedout = "SELECT tid,pid FROM TASK WHERE completed_at IS NULL AND timeout_at < DATE(%s) "
    flag_task_timeout_running = "UPDATE TASK SET RUNNING=0 WHERE tid=%s"

    update_user_referenced = ("UPDATE user SET reference_count=%s + reference_count WHERE USER_NAME=%s")
    create_user = ("INSERT INTO user(username) VALUES(%s)")
    update_user_last_pulled ="UPDATE uSER SET last_pulled=%s"

    create_file = ("INSERT INTO file(dirname,basename) VALUES (%s, %s)")

    create_post = "INTERT INTO post(user_id,text)"
    associate_file = ("INSERT INTO post_file(post_id,file_id) VALUES (%s, %s)")


    def __init__(self):
        # note autocommit off by default
        self.cnx = mysql.connector.connect(host="raspberrypi.local", user='root', database='autotumbl',
                                           password='')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cnx.close();

    def createUser(self, username):
        cursor = self.cnx.cursor()
        cursor.execute(self.create_user, username)
        return self.cnx.insertid()

    def addPostWithFiles(self, post, user, files):
        cursor = self.cnx.cursor()
        luid = self.get_uid(user)# create post
        cursor.execute(self.create_post, luid, post.description)
        postid = self.cnx.inser_id()
        # associate files
        for f in files:
            cursor.execute(self.create_file, dirname(f), basename(f))
            fid = self.cnx.inser_id()
            cursor.execute(self.associate_file, postid, fid)

    def get_uid(self, user):
        cursor = self.cnx.cursor()
        cursor.execute("SELECT id from user where username='%s'", user);
        luid = None
        for (uid) in cursor:
            luid = uid
        if luid == None:
            raise Exception("Tried to add posts to untracked user")

        return luid

    def bumpReferenceCounts(self, d):
        assert (isinstance(d, dict))

        for e in d.keys():
            self.bumpReferenceCount(e, d[e])

    def start_ask(self, username,progress_max,timeout_hours):
        timeout = datetime.now().date() + timedelta(hours=timeout_hours)
        d = dict()
        d["uid"]= self.get_uid(username)
        d["progress_max"]progress_max
        d["uid"] = self.get_uid(username)
        d["pid"] = os.getpid()
        d["from"]= datetime.now().date()
        d["to"] = timeout
        cursor = self.cnx.cursor()
        cursor.execute(self.start_task_sql,d)




    def bump_timeout(self,tid,seconds):
        raise Exception("Only setting timeout supported right now");
        #timeout = datetime.now().date() + timedelta(days=1)

    def set_timeout(self,tid,date):
        self.cnx.cursor().execute("UPDATE TASK SET timeout_At=%s WHERE tid=%s",date.date(),tid)


    def end_task(self, tid):
        cursor = self.cnx.cursor()
        cursor.execute("UPDATE TASK SET COMPLETED_AT=%s, RUNNING=%s", datetime.now().date(),0);

        for (uid) in cursor.execute("SELECT uid FROM TASK WHERE id=%s",tid):
            cursor.execute(self.update_user_last_pulled,uid)


    def bumpReferenceCount(self, username, qty):
        cursor = self.cnx.cursor()
        cursor.execute(self.update_user_referenced, username, qty)

    def commit(self):
        self.cns.commit();

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
                csr.execute(self.flag_task_timeout_running, 0)


