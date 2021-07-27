import json
import re

import requests
from bs4 import BeautifulSoup


class Music:
    pass


class Album(Music):
    def __init__(self, url, json, loaded=True):
        self.loaded = loaded
        self.url = url
        self.json = json
        tracks_common_json = {
            'inAlbum': {'@id': self.json['@id'], '@type': self.json['@type'], 'name': self.json['name']},
            'byArtist': self.json['byArtist'], 'publisher': self.json['publisher'], 'keywords': self.json['keywords']}
        self.tracks = [Track(track['item']['@id'], {**tracks_common_json, **track['item']}, False) for track in
                       self.json['track']['itemListElement']]


class Track(Music):
    def __init__(self, url, json, loaded=True):
        self.loaded = loaded
        self.url = url
        self.json = json
        mp3_l = [dic['value'] for dic in self.json['additionalProperty'] if dic['name'] == 'file_mp3-128']
        if mp3_l:
            self.mp3 = mp3_l[0]
            self.released = True
        else:
            self.mp3 = None
            self.released = False

    def load(self):
        if not self.loaded:
            self.loaded = True
            self.json = Webpage(self.url).object().json


class Band:
    def __init__(self, url, soup):
        self.soup = soup
        self.url = url
        self.root = re.search('^https://[^/]*(?=/|$)', self.url).group()
        music_names = [m.p.text.strip().split('\n')[0].strip() for m in soup.find('ol', id='music-grid').find_all('li')]
        music_urls = [self.root + mus['href'] for mus in soup.find('ol', id='music-grid').find_all('a')]
        music_types = [m['data-item-id'].split('-')[0] for m in soup.find('ol', id='music-grid').find_all('li')]
        self.music = [[*mus] for mus in zip(music_types, music_names, music_urls)]
        self.name = soup.find('meta', attrs={'name': 'title'})['content']


class Search:
    typeconvert = {'song': 'track', 'band': 'artist'}
    root = 'https://bandcamp.com/search'

    def __init__(self, url, query, soup):
        self.url = url
        self.query = query
        self.soup = soup
        self.items = [SearchItem(li) for li in self.soup.find('ul', class_='result-items')('li')]
        self.prev, self.next = None, None

    def select_nth(self, n):
        item = self.items[n]
        web_page = Webpage(item.url)
        wp_type = self.typeconvert[web_page.type] if web_page.type in self.typeconvert else web_page.type
        if wp_type == item.type.lower():
            return web_page.object()
        elif item.type == 'ARTIST':
            return Webpage(web_page.json()['byArtist']['@id'] + '/music').object()
        else:
            return web_page.object()

    def is_there_more(self):
        return self.soup.find('a', class_='next') is not None

    def next_page(self):
        nextp = self.soup.find('a', class_='next')
        if nextp is not None:
            self.next = re.search(r'(?<=page=)\d+(?=&)', nextp.attrs['href']).group()
            return Webpage(self.root, {'q': self.query, 'page': self.next}).object()

    def prev_page(self):
        prev = self.soup.find('a', class_='prev')
        if prev is not None:
            self.prev = re.search(r'(?<=page=)\d+(?=&)', prev.attrs['href'])
            return Webpage(self.root, {'q': self.query, 'page': self.prev}).object()


class SearchItem:
    def __init__(self, soup):
        self.soup = soup
        art = self.soup.img
        if art is not None:
            self.art = art.attrs['src']
        else:
            self.art = None
        self.type = self.soup.find('div', class_='itemtype').text.strip()
        self.title = self.soup.find('div', class_='heading').text.strip()
        self.subtitle = self.soup.find('div', class_='subhead').text.strip()
        self.url = self.soup.find('div', class_='itemurl').text.strip()


class Webpage:
    types = {'album': Album, 'band': Band, 'song': Track, 'search': Search}

    def __init__(self, url, params=None):
        if params is None:
            params = dict()
        self.r = requests.get(url, params=params)
        assert self.r.status_code == 200
        self.html = self.r.text
        self.soup = BeautifulSoup(self.html, 'lxml')
        self.type = self.soup.find('meta', property='og:type').attrs['content'] if self.soup.find('meta',
                                                                                                  property='og:type') is not None else 'search'
        self.obj_class = self.types[self.type] if self.type in self.types else None

    def object(self):
        if self.obj_class.mro()[1] == Music:
            return self.obj_class(self.r.url, self.json())
        elif self.obj_class == Search:
            query = self.soup.find('div', class_='search').input.attrs['value']
            return self.obj_class(self.r.url, query, self.soup)
        elif self.obj_class is not None:
            return self.obj_class(self.r.url, self.soup)

    def json(self):
        json_dict = self.soup.find(type=re.compile('.*json.*')).contents[0]
        return json.loads(json_dict)


class Bandcamp:
    root = 'https://bandcamp.com'

    def search(self, query):
        return Webpage(self.root + '/search', {'q': query}).object()
