# -*- coding: utf-8 -*-

import unittest
import PrimaPlay

class mockTime:
    def time(self):
        return 1450875766

class mockUserAgent:
    def __init__(self, filenames = []):
        self.filenames = filenames

    def get(self, url):
        fl = open(self.filenames.pop(0), 'r')
        content = fl.read()
        return content

class PrimaPlayUnitTest(unittest.TestCase):
 
    def setUp(self):
        pass
 
    def test_get_player_init_link(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_player_init.js']), mockTime())

        self.assertEqual(prima_play.get_player_init_url('p135603'),
            'http://play.iprima.cz/prehravac/init?_ts=1450875766&_infuse=1&productId=p135603')

    def test_get_video_link(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_player_init.js']), mockTime())

        self.assertEqual(prima_play.get_video_link('p135603'),
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8')

    def test_get_next_list(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_ajax_response.data']), mockTime())

        next_list = prima_play.get_next_list('https://play.iprima.cz/tdi/dalsi?')
        self.assertEqual(next_list.next_link,
            'https://play.iprima.cz/tdi/dalsi?filter=allShows&sort[]=title&offset=72')

        self.assertEqual(len(next_list.list), 18)
        self.assertEqual(next_list.list[0].title, u'Největší esa mafie 1 Epizoda')
        self.assertEqual(next_list.list[0].link, 'http://play.iprima.cz/nejvetsi-esa-mafie-1')

    def test_get_next_list_series(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_ajax_response_p.data']), mockTime())

        next_list = prima_play.get_next_list('https://play.iprima.cz/tdi/dalsi/prostreno?')
        self.assertEqual(next_list.next_link,
            'https://play.iprima.cz/tdi/dalsi/prostreno?season=p14877&sort[]=Rord&sort[]=latest&offset=36')

    def test_get_page__player_page(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_video_page.html', 'test_player_init.js']), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/prostreno-IX-9')

        self.assertEqual(page.player.title, u'Prostřeno!')
        self.assertEqual(page.player.video_link,
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8')
        self.assertEqual(page.player.image_url,
            'http://static.play-backend.iprima.cz/cdn/img/splash169/p135609-p183945/l_xhdpi')
        self.assertEqual(len(page.video_lists), 2)
        self.assertEqual(page.video_lists[0].title, u'Další epizody')
        self.assertEqual(page.video_lists[0].link,
            'http://play.iprima.cz/prostreno-IX-9?season=p135603&sort[]=ord&sort[]=Rlatest')
        self.assertEqual(len(page.video_lists[0].item_list), 20)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'Prostřeno! Sezóna 12: Epizoda 9')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno/videa/prostreno-xii-9')

    def test_get_page__homepage(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_homepage.html']), mockTime())
        page = prima_play.get_page('http://play.iprima.cz')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 7)
        self.assertEqual(page.video_lists[0].title, u'Oblíbené seriály')
        self.assertEqual(page.video_lists[0].link,
            'http://play.iprima.cz?genres[]=p128387&reltype=general&cat[]=SERIES&sort[]=latest')
        self.assertEqual(len(page.video_lists[0].item_list), 12)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'Vinaři 2 Řady , 32 Epizod')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/vinari')

    def test_get_page__episodes(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_prostreno_epizody.html']), mockTime())
        page = prima_play.get_page('http://play.iprima.cz')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 1)
        self.assertEqual(page.video_lists[0].title, None)
        self.assertEqual(page.video_lists[0].link, None)
        self.assertEqual(page.video_lists[0].next_link, 
            'https://play.iprima.cz/tdi/dalsi/prostreno?season=p14877&sort[]=Rord&sort[]=latest&offset=18')
        self.assertEqual(len(page.video_lists[0].item_list), 18)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'Praha Sezóna 3: Epizoda 10')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno-ix-10')

        self.assertEqual(len(page.filter_lists), 3)
        self.assertEqual(page.filter_lists[0].title, u'Řada')

        self.assertEqual(len(page.filter_lists[0].item_list), 11)
        self.assertEqual(page.filter_lists[0].item_list[0].title, u'Sezóna 1')
        self.assertEqual(page.filter_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno?season=p14883&sort[]=Rord&sort[]=latest')

    def test_get_page__search(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_search_page.html']), mockTime())
        page = prima_play.get_page('http://play.iprima.cz')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 3)
        self.assertEqual(page.video_lists[0].title, u'Mezi seriály')
        self.assertEqual(page.video_lists[0].link,
            'http://play.iprima.cz/vysledky-hledani?query=prostreno&searchGroup=SERIES')
        self.assertEqual(len(page.video_lists[0].item_list), 2)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'VIP PROSTŘENO! 3 Řady , 32 Epizod')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/vip-prostreno')

    def test_get_page__current_filters(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_filters.html']), mockTime())
        page = prima_play.get_page('http://play.iprima.cz')

        self.assertEqual(page.current_filters.link,
            'https://play.iprima.cz/tdi/filtr/zrusit/prostreno?availability=new&season=p14894')
        self.assertEqual(len(page.current_filters.item_list), 2)
        self.assertEqual(page.current_filters.item_list[0].title, u'Novinky')
        self.assertEqual(page.current_filters.item_list[0].link,
            'http://play.iprima.cz/prostreno?season=p14894&action=remove')

    def test_get_redirect_from_remove_link(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(['test_remove_all_filters.html']), mockTime())
        self.assertEqual(prima_play.get_redirect_from_remove_link("http://remove_link"),
            'http://play.iprima.cz/prostreno')
        

if __name__ == '__main__':
    unittest.main()
