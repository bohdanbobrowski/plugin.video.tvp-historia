# -*- coding: utf-8 -*-
import hashlib
import json
import os
import re
import time
import urllib
import urllib2
import xbmcaddon
import xbmcgui
import xbmcplugin
from operator import itemgetter

# TVP Historia - plugin do XBMC
# by Bohdan Bobrowski 2016

addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)
linki = {}  

def ListaKategorii():
        req = urllib2.Request('http://vod.tvp.pl/shared/listing.php?parent_id=6718966&page=1&type=website&direct=false&template=directory/listing_series.html&count=100')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        html=response.read()
        response.close()        
        categories=re.findall('<img src="([^"]+)" alt="[^"]*" />[\s]*</div>[\s]*<div class="itemContent">[\s]*<div>[\s]*<ul class="headP">[\s]*<li>[\s]*<span class="icon more"></span>[\s]*</li>[\s]*<li>[\s]*<strong[\s]+class="shortTitle">[\s]*<a[\s]+href="/([0-9]{1,10})/([^"]+)"[\s]+title="([^"]*)',html)
        categories=sorted(categories, key=itemgetter(2))
        for image,tvp_id,tvp_url,title in categories:
            title = title.strip()
            href="http://vod.tvp.pl/shared/listing.php?parent_id="+tvp_id+"&page=PAGENR&type=video&order=release_date_long,-1&filter={%22playable%22:true}&direct=false&template=directory/listing.html&count=12"
            addDir(title,href,image,1)

def ListaFilmow(url,name,page):
        m = hashlib.md5()
        m.update(url+time.strftime("%Y%m%d"))
        page_url = url.replace('PAGENR',str(page))
        req = urllib2.Request(page_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        html = response.read()
        response.close()
        filmy = re.findall('<img src="([^"]+)" alt="[^"]*" />[\s]*</div>[\s]*<div class="itemContent">[\s]*<div>[\s]*<ul class="headP">[\s]*<li>[\s]*<span class="icon more"></span>[\s]*</li>[\s]*<li>[\s]*<strong[\s]+class="shortTitle">[\s]*<a[\s]+href="/([0-9]{1,10})/([^"]+)"[\s]+title="([^"]*)',html)
        videos = {}
        ilosc_filmow=0
        if os.path.isfile(addonUserDataFolder + "/videos.json"):
            with open(addonUserDataFolder + "/videos.json", "r") as f:
                for line in f:
                    videos.update(json.loads(line))            
        for image,tvp_id,tvp_url,title in filmy:
            if videos.get(tvp_id) is not None:
                if videos[tvp_id]:
                    ilosc_filmow=ilosc_filmow+1
                    addLink(title, videos[tvp_id], image) 
            else:
                req_v = urllib2.Request('http://www.tvp.pl/sess/tvplayer.php?object_id='+tvp_id)            
                req_v.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                response_v = urllib2.urlopen(req_v)
                html_v = response_v.read()
                response_v.close()
                plikwideo = re.findall("{src:'([^']*)', type: 'video/mp4'}",html_v)
                if plikwideo and plikwideo[0]:
                    plikwideo = plikwideo[0]
                    plikwideo = plikwideo.replace('video-3.mp4','video-6.mp4')
                    plikwideo = plikwideo.replace('video-4.mp4','video-6.mp4')
                    plikwideo = plikwideo.replace('video-5.mp4','video-6.mp4')
                    videos[tvp_id] = plikwideo
                    ilosc_filmow=ilosc_filmow+1
                    addLink(title, plikwideo, image) 
                else:
                    videos[tvp_id] = False
        if ilosc_filmow > 11:
            addPageLink("Strona "+str(page+1), url, page+1)
        # Cache z informacjami o plikach wideo:
        videos_json = json.dumps(videos)
        videos_file = open(addonUserDataFolder + "/videos.json", "w")
        videos_file.write(videos_json)
        videos_file.close()        

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
        return param

def addLink(name,url,iconimage):
        ok = True
        print name, url, iconimage
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addPageLink(name,url,page):
        u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+'&page='+str(page)
        ok = True
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png")
        liz.setInfo( type="Video", infoLabels={ "Title": name })
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addDir(name,url,iconimage,page):
        u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+'&page='+str(page)
        ok = True
        liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
              
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        page=int(params["page"])
except:
        pass

if url==None or len(url)<1:
        ListaKategorii()
       
else:
        ListaFilmow(url,name,page)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
