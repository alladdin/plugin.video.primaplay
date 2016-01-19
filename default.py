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
    _hd_enabled = False;
    if (_addon_.getSetting('hd_enabled') == 'true'): _hd_enabled = True
    _play_parser = PrimaPlay.Parser(hd_enabled=_hd_enabled)
    _play_account = None
    if (_addon_.getSetting('account_enabled') == 'true'):
        _play_account = PrimaPlay.Account( _addon_.getSetting('account_email'), _addon_.getSetting('account_password'), _play_parser )

    def main_menu(pageurl, list_only = False):
        page = _play_parser.get_page(pageurl)
        if not list_only:
            if page.player:
                add_player(page.player)
            else:
                add_search_menu()
                add_account_menu()
            add_filters(page, pageurl)

        for video_list in page.video_lists:
            if video_list.title: add_title(video_list)
            add_item_list(video_list.item_list)
            if video_list.next_link: add_next_link(video_list.next_link)

    def next_menu(nexturl):
        next_list = _play_parser.get_next_list(nexturl)
        add_item_list(next_list.list)
        if next_list.next_link: add_next_link(next_list.next_link)

    def search():
        keyboard = xbmc.Keyboard('',u'Hledej')
        keyboard.doModal()
        if (not keyboard.isConfirmed()): return
        search_query = keyboard.getText()
        if len(search_query) <= 1: return
        main_menu(_play_parser.get_search_url(search_query))

    def account():    
        if not _play_account.login():
            li = list_item('[B]Chyba přihlášení![/B] Zkontrolujte e-mail a heslo.')
            xbmcplugin.addDirectoryItem(handle=_handle_, url='#', listitem=li, isFolder=True)
            return
        main_menu(_play_account.video_list_url, True)

    def remove_filter(removefilterurl):
        link = _play_parser.get_redirect_from_remove_link(removefilterurl)
        main_menu(link)

    def manage_filter(pageurl, filterid):
        if filterid is None:
            main_menu(pageurl)
            return

        page = _play_parser.get_page(pageurl)
        dlg = xbmcgui.Dialog()
        filter_list = page.filter_lists[filterid]
        add_id = dlg.select(filter_list.title, map(lambda x: x.title, filter_list.item_list))
        if add_id < 0:
            main_menu(pageurl)
            return

        main_menu(filter_list.item_list[add_id].link)

    def add_filters(page, pageurl):
        if page.current_filters:
            li = list_item(u'[B]Odstranit nastavené filtry: [/B]' + ", ".join(map(lambda x: x.title, page.current_filters.item_list)))
            url = get_menu_link( action = 'FILTER-REMOVE', linkurl = page.current_filters.link )
            xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)
        for filterid, filter_list in enumerate(page.filter_lists):
            li = list_item(u'[B]Nastav filtr: [/B]' + filter_list.title)
            url = get_menu_link( action = 'FILTER-MANAGE', linkurl = pageurl, filterid = filterid )
            xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_search_menu():
        li = list_item(u'[B]Hledej[/B]')
        url = get_menu_link( action = 'SEARCH' )
        xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_account_menu():
        if _play_account is None: return
        li = list_item(u'[B]Můj PLAY[/B]')
        url = get_menu_link( action = 'ACCOUNT' )
        xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_title(video_list):
        li = list_item('[B]'+video_list.title+'[/B]')
        url = '#'
        if video_list.link:
            url = get_menu_link( action = 'PAGE', linkurl = video_list.link )
        xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_item_list(item_list):
        for item in item_list:
            li = list_item(item.title, item.image_url)
            url = get_menu_link( action = 'PAGE', linkurl = item.link )
            xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)
    
    def add_next_link(next_link):
        li = list_item(u'Další stránka')
        url = get_menu_link( action = 'PAGE-NEXT', linkurl = next_link )
        xbmcplugin.addDirectoryItem(handle=_handle_, url=url, listitem=li, isFolder=True)

    def add_player(player):
        li = list_item(u"[B]Přehraj:[/B] "+player.title, player.image_url)
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

    action = None
    linkurl = None
    filterid = None

    params = get_params()
    assign_params(params)
    logDbg("PrimaPlay Parameters!!!")
    logDbg("action: "+str(action))
    logDbg("linkurl: "+str(linkurl))
    logDbg("filterid: "+str(filterid))
    try:
        if action == "FILTER-REMOVE":
            remove_filter(linkurl)
            xbmcplugin.endOfDirectory(_handle_, updateListing=True)
        if action == "FILTER-MANAGE":
            manage_filter(linkurl, int(filterid))
            xbmcplugin.endOfDirectory(_handle_, updateListing=True)
        elif action == "PAGE-NEXT":
            next_menu(linkurl)
            xbmcplugin.endOfDirectory(_handle_, updateListing=True)
        elif action == "SEARCH":
            search()
            xbmcplugin.endOfDirectory(_handle_)
        elif action == "ACCOUNT":
            account()
            xbmcplugin.endOfDirectory(_handle_)
        elif action == "PAGE":
            main_menu(linkurl)
            xbmcplugin.endOfDirectory(_handle_)
        else:
            main_menu("http://play.iprima.cz")
            xbmcplugin.endOfDirectory(_handle_)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        _exception_log(exc_type, exc_value, exc_traceback)

except Exception as ex:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    _exception_log(exc_type, exc_value, exc_traceback)
