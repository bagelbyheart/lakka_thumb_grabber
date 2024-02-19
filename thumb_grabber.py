#!/usr/bin/env python

import argparse
import os
import re
import html.parser
import urllib.parse
import urllib.request
from pprint import pprint


BASEURL = "http://thumbnailpacks.libretro.com"
BASEDIR = "/storage/thumbnails"
DEBUG = False
STRIP = True


def vprint(obj):
    if DEBUG:
        pprint(obj)


def remove_extras(str):
    str = re.sub('\(.*\)', '', str)
    str = re.sub('\[.*\]', '', str)
    str = str.rstrip()
    return(str)


def process_args():
    description = ("A tool to grab lakka thumbnails for games without direct "
                   "title matches")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("system",
                        help="libretro system name")
    parser.add_argument("source",
                        help="directory to search for games")
    return(parser.parse_args())


def Pop_Extension(str):
    chunks = str.split('.')
    if len(chunks) > 1:
        chunks.pop()
    return('.'.join(chunks))


class link_grabber(html.parser.HTMLParser):
    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.data = {}

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.data[Pop_Extension(urllib.parse.unquote(value))] = None


def Get_Games(system):
    INDEXURL = f"{BASEURL}/{urllib.parse.quote(system)}/Named_Boxarts"
    try:
        response = urllib.request.urlopen(INDEXURL)
        data = response.read()
        filecontent = data.decode('utf-8')
        parser = link_grabber()
        parser.feed(filecontent)
        links = parser.data
        return(links)
    except:
        print(f"Unable to find: {system}")
        exit(1)


def Get_Files(path):
    dir_list = os.listdir(path)
    dir_list.sort()
    return(dir_list)


def Check_Games(file, list):
    # thumbnailpacks.libretro.com has & in filenames shown as _
    # this if statement corrects for that in our search
    # if "&" in file:
    #     file = re.sub('&', '_', file)
    matches = []
    try:
        if list[file] == None:
            matches.append(file)
    except:
        for key in list:
            if file in key:
                matches.append(key)
    # we sort matches by length, as the site returns virtual console release
    # before original releases, etc. This undoes that.
    matches.sort(key=len)
    return(matches)


def Find_Targets(files, games):
    tuples = []
    for file in files:
        if "&" in file:
            file = re.sub('&', '_', file)
        file = Pop_Extension(file)
        cfile = file
        if STRIP:
            cfile = remove_extras(cfile)
        matches = Check_Games(cfile, games)
        if len(matches) == 0:
            print(f" No match for: {cfile}")
        else:
            final = ''
            for match in matches:
                if "(USA" in match:
                    final = (f"{file}.png", f"{match}.png")
                    break
                elif "(World)" in match:
                    final = (f"{file}.png", f"{match}.png")
                    break
                elif "(Japan" in match:
                    final = (f"{file}.png", f"{match}.png")
            if final == '':
                final = (f"{file}.png", f"{matches[0]}.png")
            tuples.append(final)
    return(tuples)


def Get_Thumbs(dst, src):
    src = urllib.parse.quote(src)
    System_URL = f"{BASEURL}/{urllib.parse.quote(System)}"
    PATHS = ['Named_Boxarts', 'Named_Titles', 'Named_Snaps']
    for PATH in PATHS:
        Image_SRC = f"{System_URL}/{PATH}/{src}"
        Image_DST = f"{BASEDIR}/{System}/{PATH}/{dst}"
        try:
            urllib.request.urlretrieve(Image_SRC, Image_DST)
        except urllib.error.HTTPError:
            # this error is mostly to help folks that might want to provide
            # the missing thumbs down the line.
            print(f" No {PATH} for: {urllib.parse.unquote(src)}")


def Main():
    args = process_args()
    global System
    System = args.system
    Source = args.source
    print(f"Grabbing thumbnails for {System}")
    Games = Get_Games(System)
    Files = Get_Files(Source)
    Full_List = Find_Targets(Files, Games)
    PATHS = ['Named_Boxarts', 'Named_Titles', 'Named_Snaps']
    for PATH in PATHS:
        try:
            os.makedirs(f"{BASEDIR}/{System}/{PATH}")
        except FileExistsError:
            pass
    c = 0
    for pair in Full_List:
        c = c+1
        print(f" Grabbing set {c} out of {len(Full_List)}", end='\r')
        vprint(pair)
        Get_Thumbs(pair[0], pair[1])
    print(f" {len(Full_List)} thumbnail sets were downloaded")
    exit(0)


Main()
