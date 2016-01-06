# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import traceback
from xbmcplugin import addDirectoryItem
from libPrimaPlay import PrimaPlay
import urllib
from urlparse import parse_qs

_addon_ = xbmcaddon.Addon('plugin.video.primaplay')
_scriptname_ = _addon_.getAddonInfo('name')
_version_ = _addon_.getAddonInfo('version')

###############################################################################
def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__ == 'unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s" % (_scriptname_, msg.__str__()), level)

def logDbg(msg):
    log(msg, level=xbmc.LOGDEBUG)

def logErr(msg):
    log(msg, level=xbmc.LOGERROR)

def _exception_log(exc_type, exc_value, exc_traceback):
    logErr(traceback.format_exception(exc_type, exc_value, exc_traceback))
    xbmcgui.Dialog().notification(_scriptname_, _toString(exc_value), xbmcgui.NOTIFICATION_ERROR)
    
def _toString(text):
    if type(text).__name__ == 'unicode':
        output = text.encode('utf-8')
    else:
        output = str(text)
    return output

try:
    _icon_ = xbmc.translatePath(os.path.join(_addon_.getAddonInfo('path'), 'icon.png'))
    _handle_ = int(sys.argv[1])
    _baseurl_ = sys.argv[0]
    _play_parser = PrimaPlay.Parser()

    def main_menu(pageurl):
        page = _play_parser.get_page(pageurl)
        if page.player: add_player(page.player)
        for filter_list in page.filter_lists:
            add_title(filter_list)
            add_item_list(filter_list.item_list)
        for video_list in page.video_lists:
            if video_list.title: add_title(video_list)
            add_item_list(video_list.item_list)
            if video_list.next_link: add_next_link(video_list.next_link)

        xbmcplugin.endOfDirectory(_handle_)

    def next_menu(nexturl):
        next_list = _play_parser.get_next_list(nexturl)
        add_item_list(next_list.list)
        if next_list.next_link: add_next_link(next_list.next_link)

        xbmcplugin.endOfDirectory(_handle_, updateListing=True)

    def add_title(video_list):
        li = list_item('[B]'+video_list.title+'[/B]')
        url = '#'
        if video_list.link:
            url = get_menu_link( pageurl = video_list.link )
        xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_item_list(item_list):
        for item in item_list:
            li = list_item(item.title, item.image_url)
            url = get_menu_link( pageurl = item.link )
            xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)
    
    def add_next_link(next_link):
        li = list_item(u'Další stránka')
        url = get_menu_link( nexturl = next_link )
        xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_player(player):
        li = list_item(player.title, player.image_url)
        xbmcplugin.addDirectoryItem(handle=_handle_, url=player.video_link, listitem=li, isFolder=False)

    def list_item(label, thumbnail = None):
        li = xbmcgui.ListItem(label)
        liVideo = {'title': label}
        if thumbnail:
            li.setThumbnailImage(thumbnail)
        li.setInfo("video", liVideo)
        return li

    def get_menu_link(**kwargs):
        return _baseurl_ + "?" + urllib.urlencode(kwargs)

    def get_params():
            if len(sys.argv[2])<2: return []
            encoded_query = sys.argv[2].lstrip('?')
            decoded_params = parse_qs(encoded_query)
            param = {}
            for key in decoded_params:
                if len(decoded_params[key]) <= 0: continue
                param[key] = decoded_params[key][0]
            return param

    def assign_params(params):
        for param in params:
            try:
                globals()[param] = params[param]
            except:
                pass


    pageurl = "http://play.iprima.cz"
    nexturl = None
    params = get_params()
    assign_params(params)
    logDbg("PrimaPlay Parameters!!!")
    logDbg("PAGE: "+str(pageurl))
    logDbg("NEXT PAGE: "+str(nexturl))
    try:
        if nexturl:
            next_menu(nexturl)
        else:
            main_menu(pageurl)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        _exception_log(exc_type, exc_value, exc_traceback)

except Exception as ex:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    _exception_log(exc_type, exc_value, exc_traceback)
