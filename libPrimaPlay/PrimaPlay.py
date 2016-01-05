#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import time
import re
import sys
from bs4 import BeautifulSoup

__author__ = "Ladislav Dokulil"
__license__ = "MIT"
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
        soup = BeautifulSoup(cdata_match.group(1), 'html.parser')
        return self.get_items_from_wrapper(soup, '')

    def get_next_list_link(self, content):
        search = re.compile('(https?://play.iprima.cz/tdi/dalsi.*offset=\d+)')
        result = search.search(content)
        if result: return result.group(1)
        return None

    def get_page(self, link):
        content = self.ua.get(link)
        soup = BeautifulSoup(content, 'html.parser')
        return Page(
            self.get_page_title(soup),
            self.get_page_player(soup),
            self.get_video_lists(soup, link)
        )

    def get_page_title(self, soup):
        h1_title = soup.find('h1')
        if h1_title:
            return " ".join(h1_title.stripped_strings)
        return " ".join(soup.title.stripped_strings)

    def get_page_player(self, soup):
        fake_player = soup.find(id='fake-player');
        if fake_player is None:
            return None
        product_id = fake_player['data-product']
        image_url = fake_player.img['src']
        title = fake_player.img['alt'].strip()
        video_link = self.get_video_link(product_id)
        return Player(title, video_link, image_url)

    def get_video_lists(self, soup, src_link):
        list = []
        for next_wrapper in soup.select('#js-tdi-items-next'):
            items = self.get_items_from_wrapper(next_wrapper, src_link)
            next_link_soup = soup.select('div.infinity-scroll')
            next_link = None
            if len(next_link_soup) > 0:
                next_link_tag = next_link_soup[0]
                next_link = next_link_tag['data-href']
            if (len(items) <= 0): continue
            list.append(PageVideoList(None,
                None, self.make_full_link(next_link, src_link),
                items))

        for wrapper in soup.select('section.movies-list-carousel-wrapper'):
            title = self.strip_join_strings(wrapper.h2.stripped_strings)
            link_tag = wrapper.h2.a
            link = None
            if link_tag: link = link_tag['href']
            items = self.get_items_from_wrapper(wrapper, src_link)
            if (len(items) <= 0): continue
            list.append(PageVideoList(title,
                self.make_full_link(link, src_link),
                None, items))
        return list

    def get_items_from_wrapper(self, wrapper, src_link):
        list = []
        for item_soup in wrapper.select('div.movie-border'):
            link = self.make_full_link(item_soup.div.a['href'], src_link)
            title_list = item_soup.select('div.back div.header')
            if len(title_list) <= 0: continue
            title = self.strip_join_strings(title_list[0].stripped_strings)
            image_url = None
            image_tag = item_soup.select('img.lazyload')
            if len(image_tag) > 0:
                image_re = re.compile('^([^ ]+)')
                image_url = image_re.search(image_tag[0]['data-srcset']).group(1)
            list.append(Item(title, link, image_url))
        return list

    def make_full_link(self, target_link, src_link):
        if target_link is None:
            return None
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

    def strip_join_strings(self, strings):
        result = (" ".join(strings)).strip()

        result = result.replace("\n",'')
        result = result.replace("\t",'')
        result = result.replace("\r",'')

        return result
        
    
class Page:
    def __init__(self, title, player = None, video_lists = []):
        self.title = title
        self.video_lists = video_lists
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
