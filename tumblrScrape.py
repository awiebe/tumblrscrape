import os
import sys
import shutil

import re
import requests
from bs4 import BeautifulSoup
from bs4 import Tag
import json


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
    posts = soup.find_all(class_='post')
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
    for image in images:
        print 'Downloading Image: %s' % image['src']

        #try to click down and get highest quality image
        try:
            r = session.get(image.parent["href"])
            if r.status_code != 200:
                print 'Got status code %s' % r.status_code

            html = r.text.encode("utf-8")
            soup = BeautifulSoup(html, 'html.parser')

            # content = soup.find('div', id='content')
            # posts = soup.findall('div', re.compile(".*"))
            url = soup.find(id='content-image')["src"]
        except:
            pass

        url = image['src']
        filename = url.split('/')[-1]

        image_path = os.path.join(user_dir, 'img',filename)
        paths.append(image_path)
        if os.path.isfile(image_path):
            continue
        r = session.get(url, stream=True)
        with open(image_path, 'wb') as out_file:
            shutil.copyfileobj(r.raw, out_file)

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

        posts = get_page_posts(username, page, session)
        while (len(posts) >0):
            for p in posts:
                pid = getPostID(p)

                #not a real post just using that classname for formatting
                if pid == None:
                    continue

                images = imagesInPost(p)
                tags = tagsInPost(p)

                if not postDict.has_key(pid):
                    postDict[pid]={}
                    postDict[pid]["tags"]= []
                    postDict[pid]["images"] = []
                    postDict[pid]["text"] = ""

                postDict[pid]["tags"]=set(postDict[pid]["tags"])
                for t in tags:
                    if isinstance(t,Tag):
                        tagString= t.getText().replace("#","")
                        postDict[pid]["tags"].add(tagString)


                images = imagesInPost(p)
                postDict[pid]["images"] = map(os.path.basename,download_images(user_dir,images,session))
                postDict[pid]["tags"] = list(postDict[pid]["tags"])
                postDict[pid]["text"]= str(p)
            page += 1
            posts = get_page_posts(username, page, session)
        json.dump(postDict,fd)
        fd.close()
    except KeyboardInterrupt:
        json.dump(postDict, fd)
        fd.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
