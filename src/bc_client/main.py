import logging
import os
import time

from pynput import keyboard

from src.bc_client import bc_api
from src.bc_client import curses_UI
from src.bc_client import player

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", "~/.config")
CONFIGS = os.path.expanduser(XDG_CONFIG_HOME + '/bc_client')
if not os.path.isdir(CONFIGS):
    os.mkdir(CONFIGS)


class Main:
    def __init__(self):
        self.bandcamp = bc_api.Bandcamp()
        self.wrapper = curses_UI.create_wrapper()
        self.player = player.Player()
        self.favorites = {'Artists': list(), 'Albums': list(), 'Tracks': list()}
        if os.path.isfile(CONFIGS + '/favorites'):
            with open(CONFIGS + '/favorites', 'r') as fav:
                for line in fav:
                    item, params = line.split(': ')
                    if item == 'ARTIST':
                        self.favorites['Artists'].append(bc_api.Band(*eval(params)))
                    elif item == 'ALBUM':
                        self.favorites['Albums'].append(bc_api.Album(*params, loaded=False))
                    elif item == 'TRACK':
                        self.favorites['Tracks'].append(bc_api.Track(*eval(params), loaded=False))
        self.playlist = list()
        self.menu = self.fav_menu()
        self.current = 'Favorites'
        self.wrapper.bind(keyboard.Key.enter, self.select)
        self.wrapper.new_command('favorites', lambda: self.change_menu(self.fav_menu()), 0)
        self.wrapper.new_command('search', self.search, 1)
        self.wrapper.mainloop()

    def change_menu(self, menu):
        self.menu = menu

    def fav_menu(self, category='base'):
        if category == 'base':
            menu = self.wrapper.make_menu([MenuItem([name], name, 'Menu') for name in self.favorites.keys()])
            self.wrapper.update_title('Favorites', '')
        else:
            menu = self.wrapper.make_menu(self.favorites[category])
            self.wrapper.update_title('Favorites', category)
        return menu

    def select(self):
        selected = self.menu.select()
        if selected != ['Nothing']:
            if selected.category == 'Menu':
                self.menu = self.fav_menu(selected.name)
            elif selected.category == 'Artist':
                self.current = bc_api.Webpage(selected.url).object()
                items = [MenuItem(mus[:2], mus[1:], mus[0].capitalize()) for mus in self.current.music]
                self.menu = self.wrapper.make_menu(items)
                self.wrapper.update_title(selected.name, '')
            elif selected.category == 'Album':
                self.current = bc_api.Webpage(selected.url).object()
                items = [MenuItem(
                    [str(i + 1), track.json['name'], track.json['inAlbum']['name'], track.json['byArtist']['name']],
                    track, 'Track') for i, track in enumerate(self.current.tracks)]
                logging.debug(items[0].repr)
                self.menu = self.wrapper.make_menu(items)
                self.wrapper.update_title(self.current.json['name'], self.current.json['byArtist']['name'])
            elif selected.category == 'Track':
                if selected.loaded:
                    playlist = [item.track.mp3 for item in self.menu.content[self.menu.highlighted:]]
                    self.player.play_list(playlist)
                else:
                    self.current = bc_api.Webpage(selected.url).object()
                    self.menu = self.wrapper.make_menu([MenuItem(
                        [self.current.json['name'], self.current.json['inAlbum']['name'],
                         self.current.json['byArtist']['name']],
                        self.current, 'Track')])
                    self.wrapper.update_title(self.current.json['name'],
                                              f"{self.current.json['inAlbum']['name']} - {self.current.json['byArtist']['name']}")
            else:
                selected.func()

    def new_fav(self, fav):
        pass

    def search(self, query):
        logging.debug(query)
        results = self.bandcamp.search(query)
        items = [MenuItem([i.type, i.title, i.subtitle], (i.title, i.url), i.type.lower().capitalize()) for i in
                 results.items]
        if results.is_there_more():
            items.append(MenuItem(['---', 'More', '---'], lambda: self.more_results(results), 'Function'))
        self.menu = self.wrapper.make_menu(items)
        self.wrapper.update_title(f'Search: {query}', '')

    def more_results(self, results):
        results = results.next_page()
        items = self.menu.content[:-1]
        highlighted = self.menu.highlighted
        new_items = [MenuItem([i.type, i.title, i.subtitle], (i.title, i.url), i.type.lower().capitalize()) for i in
                     results.items]
        items.extend(new_items)
        if results.is_there_more():
            items.append(MenuItem(['---', 'More', '---'], lambda: self.more_results(results), 'Function'))
        self.menu = self.wrapper.make_menu(items)
        self.menu.highlight(highlighted)

    def mainloop(self):
        while True:
            if self.player.playing():
                if self.player.total_time() != self.wrapper.time_bar.total_time:
                    self.wrapper.time_bar.set_total_time(int(self.player.total_time() / 1000))
                if self.player.time() != self.wrapper.time_bar.current:
                    self.wrapper.time_bar.update(self.player.time())
            time.sleep(0.5)


class MenuItem:
    def __init__(self, rep, data_or_url, category):
        self.repr = rep
        self.category = category
        self.loaded = False
        if category == 'Track' and type(data_or_url) != str:
            self.track = data_or_url
            self.loaded = True
        elif category == 'Menu':
            self.name = data_or_url
        elif category == 'Function':
            self.func = data_or_url
        else:
            self.name, self.url = data_or_url


main = Main()
