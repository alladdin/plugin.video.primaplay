#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import time
import re
import sys

__author__ = "Ladislav Dokulil"
__license__ = "GPL 2"
__version__ = "1.0.0"
__email__ = "alladdin@zemres.cz"

class UserAgent:
    def __init__(self, agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'):
        self.agent = agent
        self.play_url = 'http://play.iprima.cz'

    def get(self, url):
        req = urllib2.Request(self.sanitize_url(url))
        req.add_header('User-Agent', self.agent)
        res = urllib2.urlopen(req)
        output = res.read()
        res.close()
        return output

    def sanitize_url(self, url):
        abs_url_re = re.compile('^/')
        if (abs_url_re.match(url)):
            return self.play_url + url
        return url

class Parser:
    def __init__(self, ua = UserAgent(), time_obj = time):
        self.ua = ua
        self.player_init_url = 'http://play.iprima.cz/prehravac/init?'
        self.time = time_obj

    def get_player_init_url(self, productID):
        return self.player_init_url + urllib.urlencode({
            '_infuse': '1',
            '_ts': int(self.time.time()),
            'productId': productID
        })
        #http://play.iprima.cz/prehravac/init?_infuse=1&_ts=1450864235286&productId=p135603

    def get_video_link(self, productID):
        content = self.ua.get(self.get_player_init_url(productID))
        link_re = re.compile("'src'\s*:\s+'(https?://[^']+\\.m3u8)'")
        return link_re.search(content).group(1)

    def get_next_list(self, link):
        content = self.ua.get(link)
        next_link = self.get_next_list_link(content)
        list = self.get_next_list_items(content)
        return NextList(next_link, list)

    def get_next_list_items(self, content):
        cdata_re = re.compile('<!\[CDATA\[(.*)\]\]>', re.S)
        cdata_match = cdata_re.search(content)
        return self.get_items_from_wrapper(cdata_match.group(1), '')

    def get_next_list_link(self, content):
        next_link_re = re.compile('(https?://play.iprima.cz/tdi/dalsi.*offset=\d+)')
        result = next_link_re.search(content)
        if result: return result.group(1)
        return None

    def get_page(self, link):
        content = self.ua.get(link)
        return Page(
            self.get_page_player(content),
            self.get_video_lists(content, link),
            self.get_filter_lists(content, link)
        )

    def get_page_player(self, content):
        fake_player_re = re.compile('<div id="fake-player" class="[^"]+" data-product="([^"]+)">[^<]*<img src="([^"]+)" alt="([^"]+)"', re.S)
        fake_player_result = fake_player_re.search(content)
        if fake_player_result is None:
            return None
        product_id = fake_player_result.group(1)
        image_url = fake_player_result.group(2)
        title = fake_player_result.group(3).strip().decode('utf-8')
        video_link = self.get_video_link(product_id)
        return Player(title, video_link, image_url)

    def get_video_lists(self, content, src_link):
        list = []
        tdi_items_re = re.compile('<div class="[^"]+" id="js-tdi-items-next"')

        if tdi_items_re.search(content):
            items = self.get_items_from_wrapper(content, src_link)
            if (len(items) <= 0): return list

            next_link_re = re.compile('<div class="infinity-scroll" data-href="([^"]+)"')
            next_link_result = next_link_re.search(content)
            next_link = None
            if next_link_result: next_link = next_link_result.group(1)

            list.append(PageVideoList(None,
                None, self.make_full_link(next_link, src_link),
                items))
            
            return list

        wrapper_items = re.split('<section class="l-constrained movies-list-carousel-wrapper">', content)

        title_re = re.compile('<h2 class="[^"]+" data-scroll="cid-[^"]+">(.+)</h2>[^<]*<div class="l-movies-list', re.S)
        link_re = re.compile('<h2[^>]*>[^<]*<a href="([^"]+)">', re.S)
        for wrapper_item in wrapper_items:
            title_result = title_re.search(wrapper_item)
            if title_result is None: continue
            title = self.strip_tags(title_result.group(1))
            link_result = link_re.search(wrapper_item)
            link = None
            if link_result: link = self.make_full_link(link_result.group(1), src_link)
            items = self.get_items_from_wrapper(wrapper_item, src_link)
            if (len(items) <= 0): continue
            list.append(PageVideoList(title.decode('utf-8'),
                self.make_full_link(link, src_link),
                None, items))

        return list

    def get_items_from_wrapper(self, content, src_link):
        list = []

        html_items = re.split('<div id="[^"]+" class="movie-border"[^>]+>', content)

        item_link_re = re.compile('<a href="([^"]+)">')
        item_img_re = re.compile('<img data-srcset="(\S+)')
        item_title_re = re.compile('<div class="back">[^<]*<a[^>]*>[^<]*<div class="header">(.+)</div>[^<]*<div class="content">', re.S)

        for html_item in html_items:
            link_result = item_link_re.search(html_item)
            img_result = item_img_re.search(html_item)
            title_result = item_title_re.search(html_item)
            if title_result is None: continue
            title = self.strip_tags(title_result.group(1))
            link = self.make_full_link(link_result.group(1), src_link)
            image_url = None
            if img_result: image_url = img_result.group(1)
            list.append(Item(title.decode('utf-8'), link, image_url))
        return list

    def get_filter_lists(self, content, src_link):
        list = []
        before_wrapper_re = re.compile('(.*)<div class="loading-wrapper">', re.S)
        before_content = before_wrapper_re.search(content).group(1)

        filter_wrappers = re.split('<li class="hamburger-parent[^"]*">', before_content)

        title_re = re.compile('<span data-jnp="[^"]+" class="hamburger-toggler">([^<]+)</span>')
        for filter_wrapper in filter_wrappers:
            title_result = title_re.search(filter_wrapper)
            if title_result is None: continue
            title = title_result.group(1)
            items = self.get_filter_items(filter_wrapper, src_link)
            if (len(items) <= 0): continue 
            list.append(PageVideoList(title.decode('utf-8'), None, None, items))
        return list

    def get_filter_items(self, content, src_link):
        list = []

        filter_item_re = re.compile('<li>[^<]*<a class="tdi" href="([^"]+)"[^>]*>([^<]+)</a>[^<]*</li>', re.S)
        for raw_link, raw_title in filter_item_re.findall(content):
            link = self.make_full_link(raw_link, src_link)
            title = self.strip_tags(raw_title)
            list.append(Item(title.decode('utf-8'), link))

        return list

    def make_full_link(self, target_link, src_link):
        if target_link is None:
            return None
        target_link = target_link.replace('&amp;','&')
        full_link_re = re.compile('^https?://')
        if full_link_re.match(target_link):
            return target_link
        abs_link_re = re.compile('^/')
        if abs_link_re.match(target_link):
            dom_re = re.compile('^(https?://[^/]+)')
            dom = dom_re.match(src_link).group(1)
            return dom + target_link
        link_re = re.compile('^(https?://[^\?]+)')
        link = link_re.match(src_link).group(1)
        return link + target_link

    def strip_tags(self, string):
        result = re.sub('<[^>]+>', '', string)
        result = result.replace("\n",' ')
        result = result.replace("\t",' ')
        result = result.replace("\r",' ')
        result = re.sub('\s+', ' ', result)
        return result.strip()
    
class Page:
    def __init__(self, player = None, video_lists = [], filter_lists = []):
        self.video_lists = video_lists
        self.filter_lists = filter_lists
        self.player = player

class PageVideoList:
    def __init__(self, title = None, link = None, next_link = None, item_list = []):
        self.title = title
        self.link = link
        self.next_link = next_link
        self.item_list = item_list

class Player:
    def __init__(self, title, video_link, image_url):
        self.title = title
        self.video_link = video_link
        self.image_url = image_url

class NextList:
    def __init__(self, next_link, list):
        self.next_link = next_link
        self.list = list

class Item:
    def __init__(self, title, link, image_url = None):
        self.title = title
        self.link = link
        self.image_url = image_url
