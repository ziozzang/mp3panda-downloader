#!python3
################################################
# Code by Jioh L. Jung(ziozzang@gmail.com)
# [downloader for mp3panda.com]
################################################

import os
import eyed3
import requests
from bs4 import BeautifulSoup
import argparse

base_path = "./"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'"
req_headers = {
    'User-Agent': user_agent,
}

# Get UNIX Compatible file name
def get_safe_filename(filename):
    for c in r'/\;><&*%@!#|?':
        filename = filename.replace(c,'_')
    filename = filename.strip()
    return filename

# Get Login Session ID
def get_login(_id, _pw):
    _url = 'https://mp3panda.com/user/auth/'
    _data = 'login=%s&pass=%s' % (_id.replace('@','%40'), _pw)
    _headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': user_agent,
    }
    # Get login info
    res = requests.post(_url, data=_data, headers=_headers, allow_redirects=False)
    # Parse cookie parts
    cka = []
    for i in res.headers['Set-Cookie'].split(';'):
        for j in i.split(','):
            j = j.strip()
            if j.find('=') < 0:
                continue
            if j.split('=')[0] in ('Max-Age', 'path', 'expires', 'domain'):
                continue
            cka.append(j)
            #print(j)
    cookie = '; '.join(cka)
    req_headers['Cookie'] = cookie
    return cookie

# Download body
def get_file(url):
    res = requests.get(url)
    if res.ok:
        return res.text
    return None

cover_file = "cover.jpg"
mp3file = "audio.mp3"

# check purchased list pages and download mp3
def get_list(page=1):
    print("> Request Page: %d" %(page,))
    res = requests.get('https://mp3panda.com/account/download/%d/' %(page,),
                       headers=req_headers, allow_redirects=False)
    soup = BeautifulSoup(res.text,features="html.parser")
    a = soup.div.find_all(class_="album_block")
    for m in a:
        # Get Cover arts
        cover_url = m.div.find(class_="album_cover").img['src'].replace('_sm','_big')
        os.system('curl -s -o %s "%s"' % (cover_file, cover_url,))
        # Get Album infomation
        b = m.div.find(class_="album_dwn_m").find_all('a')
        artist = b[0].text.strip()
        album_title = b[1].text.strip()
        artist_url = 'https://mp3panda.com%s' % (b[0]['href'],)
        album_url = 'https://mp3panda.com%s' % (b[1]['href'],)
        p = m.div.find(class_="album_dwn_m").find_all('p')
        t = p[0].text.split(':')
        release = 0
        if len(t) > 1:
            release = t[1].strip()
        total_tracks = 0
        t = p[1].text.split(':')
        if len(t) > 1:
            total_tracks = int(t[1].strip())
        print("===========================================")
        print("Artist: '%s' [%s]" % (artist, artist_url))
        print("Album : '%s'(%s) [%s]" % (album_title, release, album_url))
        print("Tracks: %s" % (total_tracks,))
        print("[ART] : %s" %(cover_url,))
        print("-------------------------------------------")
        # Unix Compatible File & Folder name
        artist_safe = get_safe_filename(artist)
        album_title_safe = get_safe_filename(album_title)
        os.system('mkdir -p "%s/%s/%s"' % (base_path, artist_safe, album_title_safe))
        b = m.tbody.find_all('tr')[1:] # remove table's 1st line
        for n in b:
            # Parsing track info.
            c = n.find_all('td')
            track_id = int(c[0].text.strip())
            track_name = c[1].text.strip()
            track_url = "http://%s" % (n.iframe['src'].split('http://')[1],)
            print("%d - '%s' [%s]" %(track_id, track_name, track_url))
            # Check already downloaded
            track_name_safe = get_safe_filename(track_name)
            if os.path.exists(
                    "%s/%s/%s/%d.%s.mp3" % (
                            base_path, artist_safe, album_title_safe, track_id, track_name_safe)
                    ):
                print("> File Exist - Skipping")
            else:
                # Download mp3 file
                os.system('curl -o %s "%s"' % (mp3file, track_url,))
                # Update ID3 tags
                audiofile = eyed3.load(mp3file)
                if (audiofile.tag == None):
                    audiofile.initTag()
                #print(dir(audiofile.tag))
                audiofile.tag.images.set(3, open(cover_file,'rb').read(), 'image/jpeg',description="cover")
                audiofile.tag.artist = artist
                audiofile.tag.artist_url = artist_url
                audiofile.tag.album = album_title
                audiofile.tag.audio_source_url = album_url
                audiofile.tag.album_artist = artist
                audiofile.tag.title = track_name
                if total_tracks != 0:
                    audiofile.tag.recording_date = release
                if total_tracks != 0:
                    audiofile.tag.track_num = (track_id, total_tracks)
                else:
                    audiofile.tag.track_num = track_id
                audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
                # Give Correct filename
                os.system(
                    'mv -f %s "%s/%s/%s/%d.%s.mp3"' % (
                        mp3file, base_path, artist_safe, album_title_safe, track_id, track_name_safe)
                )
        # Remove Temporary Cover file
        os.system("rm -f %s" %(cover_file,))
        print("===========================================")
    if len(a) > 0:
        # Process next pages
        get_list(page+1)


if __name__ == '__main__':
    # Parameter Processing
    parser = argparse.ArgumentParser(description='UserID / Passwords...')
    parser.add_argument('userid', metavar='userid', type=str, nargs=1,
                        help='mp3panda.com login id (e-mail type)',)
    parser.add_argument('password', metavar='password', type=str, nargs=1,
                        help='login password', )
    parser.add_argument('path', metavar='path', type=str, nargs=1,
                        help='download destination path', )
    args = parser.parse_args()

    # Login Try
    ck = get_login(args.userid[0], args.password[0])
    if ck.find("registered=yes") > 0:
        print("> Login OK")
    else:
        print("> Login Failed")
        exit(1)
    base_path = args.path[0]
    # Start Downloading
    get_list()
