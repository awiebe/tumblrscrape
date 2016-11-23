import hashlib
import os
import sys
import shutil

import re
import requests
from bs4 import BeautifulSoup
from bs4 import Tag
from socket import error as SocketError
import json
import threading
import  random
import time


def create_users_directory(username):
    base_dir = ""
    base_dir = os.path.join(base_dir, 'data')
    user_dir = os.path.join(base_dir, username)
    if not os.path.isdir(user_dir):
        os.makedirs(os.path.join(user_dir,'img'))
    return user_dir


def get_page_posts(username, page, session=requests):
    url = 'http://%s.tumblr.com/page/%s' % (username, page)
    print 'Getting Page: %s' % page

    r = session.get(url)

    if r.status_code != 200:
        print 'Got status code %s' % r.status_code

    html = r.text.encode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')

    # content = soup.find('div', id='content')
    # posts = soup.findall('div', re.compile(".*"))
    posts = soup.find_all(class_=re.compile('.*post.*'))
    return posts


def imagesInPost(p):
    assert isinstance(p,Tag)
    return p.find_all('img')


def tagsInPost(p):
    tags = p.find_all('a',class_=re.compile("tag.*"))
    tags.append(p.find_all(id=re.compile("tag.*")))
    return tags



def download_images(user_dir, images, session=requests):
    paths=[]
    # throttle
    time.sleep(random.randrange(0, 1000) / 500.0)
    for image in images:



        print 'Downloading Image: %s' % image['src']
        url=image["src"]
        #try to click down and get highest quality image
        try:
            parent = image.parent
            while parent is not None and not parent.has_attr("href"):
                parent = parent.parent

            href = parent["href"]
            r = session.get(href)
            if r.status_code != 200:
                print 'Got status code %s' % r.status_code

            html = r.text.encode("utf-8")
            soup = BeautifulSoup(html, 'html.parser')

            # content = soup.find('div', id='content')
            # posts = soup.findall('div', re.compile(".*"))
            img = soup.find(id='content-image')
            if img is not None:
                url = img["data-src"]
                if url is  None:
                    url = img["src"]
        except:
            # this has to pass so we can fall back to not big images, if an exception occurs for another reason
            # handle it but not here
            pass

        filename = url.split('/')[-1]

        image_path = os.path.join(user_dir, 'img',filename)

        #not a tumblr image, we might have crossed a site boundary.
        if not str(filename).startswith("tumblr"):
            continue;

        paths.append(image_path)
        if not os.path.isfile(image_path):
            try:
                r = session.get(url, stream=True)
                with open(image_path, 'wb') as out_file:
                    shutil.copyfileobj(r.raw, out_file)
                    out_file.close()
            except:
                continue


        #Try to get higher res
        filename = url.split('/')[-1]

        suffix = url.split("_")[-1];
        extension = suffix.split(".")[-1];
        highResUrl= url.replace(suffix,"1280."+extension)
        highResFilename = filename.replace(suffix,"1280."+extension)
        image_path = os.path.join(user_dir, 'img', highResFilename)

        if not os.path.isfile(highResFilename):
            print 'Trying for 1280: ' +highResUrl
            try:
                r = session.get(highResUrl, stream=True)
                with open(image_path, 'wb') as out_file:
                    shutil.copyfileobj(r.raw, out_file)
                    out_file.close()
                if r.status_code != 200:
                    print 'Got status code %s' % r.status_code
            except:
                continue



    return paths

def getPostID(p):
    regex = re.compile(".*tumblr.com/post/.*")

    ida= p.find('a',href=regex)

    if ida is None:
        return None;

    try:
        ida = str(ida["href"]).split("/")
        i=0
        while ida[i] != "post":
            i+=1
        i+=1
        id =ida[i]
    except:
        return -1
    return id

def main():
    if len(sys.argv) != 2:
        print 'no Tumblr username given'
        return

    username = sys.argv[1]
    user_dir = create_users_directory(username)
    session = requests.session()
    page = 1
    postPath= os.path.join(user_dir,"posts.json")
    postDict={}
    try:
        if os.path.isfile(postPath):
            fd = open(postPath, "r")

            try:
                postDict.update(json.load(fd))
            except:
                pass
            fd.close()
        fd = open(postPath, "w")

        MAX_GET_POST_ATTEMPT=30;
        getPostsAttempt=1;
        posts = get_page_posts(username, page, session)
        while (getPostsAttempt < MAX_GET_POST_ATTEMPT):

            if len(posts) < 1:
                getPostsAttempt+=1
            else:
                getPostsAttempt=0;

            for p in posts:

                success = False
                while not success:
                    success = grab_post(p, postDict, session, success, user_dir)

            page += 1
            posts = get_page_posts(username, page, session)

        if getPostsAttempt >= MAX_GET_POST_ATTEMPT:
            print ">>Stopped because no posts after %d attempts<<" % getPostsAttempt;

        json.dump(postDict,fd)
        fd.close()
    except KeyboardInterrupt:
        json.dump(postDict, fd)
        fd.close()


def grab_post(p, postDict, session, success, user_dir):
    try:
        pid = getPostID(p)

        if pid == None:
            m = hashlib.md5()
            m.update(str(p))
            pid = "__md5" + m.hexdigest()

        tags = tagsInPost(p)

        if not postDict.has_key(pid):
            postDict[pid] = {}
            postDict[pid]["tags"] = []
            postDict[pid]["images"] = []
            postDict[pid]["text"] = ""

        postDict[pid]["tags"] = set(postDict[pid]["tags"])
        for t in tags:
            if isinstance(t, Tag):
                tagString = t.getText().replace("#", "")
                postDict[pid]["tags"].add(tagString)

        images = imagesInPost(p)
        longImagePaths = download_images(user_dir, images, session)
        postDict[pid]["images"] = map(os.path.basename, longImagePaths)
        postDict[pid]["tags"] = list(postDict[pid]["tags"])
        postDict[pid]["text"] = str(p)
        success = True
    except SocketError:
        success = False
        threading.sleep(10);
    return success


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
