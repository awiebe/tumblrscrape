import pytumblr
import json;
import urlparse
import datetime
import time
import posixpath
import os.path
global str

from tumblrTools import TumblrDB,TumblrPost


client = pytumblr.TumblrRestClient(
)

# Make the request
class TumblrSlurp:



    def __init__(self,db):
        self.discovered_users={};
        self.visited_users = [];
        assert(isinstance(db,TumblrDB))
        self.db=db;

        now = datetime.datetime.now()
        self.throttleDay=now.timetuple().tm_yday
        self.throttleHour=now.time().hour;
        self.throttleDailyRequests=0;
        self.throttleHourlyRequests = 0;

    def discover_user(self,user):
        self.discovered_users.append(user);

    def isTumblrUrl(self,s):
        return "tumblr.com" in s

    def discover_user_with_source_string(self, s):

        if self.isTumblrUrl(s):
            url = urlparse.urlparse(s,scheme="http")
            domain = url.netloc
            username = domain.split(".")[0];

            if(username not in self.discovered_users):
                self.discovered_users[username] = 1
            else:
                self.discovered_users[username]+=1


          #extract username

    def slurp(self,user):
        posts =[0]
        i=0

        uid = db.get_uid(user)
        latest_fetch_time = self.db.getUserModified(uid)

        if uid == None:
            uid = self.db.createUser(user)

        done = False
        while len(posts) >0 and not done:

            data = client.posts(user,offset=i,type='photo');
            blogMeta = data['blog'];
            postCount = data['total_posts'];
            posts = data['posts'];



            for p in posts:


                post_id=p['id']
                unix_time=p['timestamp']

                if( int(unix_time) < latest_fetch_time ):
                    done = True
                    break

                if 'source_url' in p:
                    source= p['source_url']
                    self.discover_user_with_source_string(source);
                else:
                    source=None;

                if p['type'] == 'photo':

                    print "Photo Post:"+ str(post_id)+" time:"+ str(unix_time);
                    print u"source:"+ unicode(source)

                    post = TumblrPost();
                    post.id = post_id
                    post.source=unicode(source)
                    post.timestamp=unix_time

                    photos = p['photos'];

                    files =[];
                    concatenated_description=str("")
                    for photo in photos:
                        lurl = photo['original_size']['url']
                        caption = photo['caption']

                        path = urlparse.urlparse(lurl).path
                        dirname = self.local_path_for_file(path)
                        basename = os.path.basename(path)
                        files.append(os.path.join(dirname,basename))
                        concatenated_description.join(caption).join("\n-\n")
                        # print photo['alt_sizes']

                    post.description =  concatenated_description
                    self.db.addPostWithFiles(post, uid, files)

                elif p['type'] == 'video':
                    pass
                print

            i=i+20
            print str(i)+"/"+ str(postCount);

            #count requat
            self.throttleHourlyRequests+=1
            self.throttleDailyRequests+=1
            #todo hack because I don't feel like figuring out computing the actual amount of time I sohuld sleep
            #check request limits, sleep if throttled, then reset
            while self.throttleHourlyRequests >=250 and datetime.datetime.now().time().hour == self.throttleHour:
                time.sleep(5)
            self.throttleHour = datetime.datetime.now().time().hour
            self.throttleHourlyRequests=0

            while self.throttleDailyRequests >= 5000 and datetime.datetime.now().timetuple().tm_yday == self.throttleDay:
                 time.sleep(600)
            self.throttleDay= datetime.datetime.now().timetuple().tm_yday
            self.throttleDailyRequests=0
            #END requests

        self.visited_users.append(user);
        self.db.bumpReferenceCounts(self.discovered_users)
        self.db.bumpUserModified(uid)
        self.db.commit()
        self.discovered_users=[]

    def local_path_for_file(self,path):
        hashstr = os.path.basename(path).split("_")[1]
        a=[]
        for c in hashstr:
            a.append(c)
        return os.path.join(*a)




#print client.posts('gravity-falls-hunks').keys();
db = TumblrDB()
s = TumblrSlurp(db)

s.slurp("dalekboi")

#s.slurp("blogillegalbaraworld")
#print str(s.discovered_users)