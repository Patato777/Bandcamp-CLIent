import logging
import os
import time

from pynput import keyboard

from src.bc_client import bc_api
from src.bc_client import curses_UI

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", "~/.config")
CONFIGS = os.path.expanduser(XDG_CONFIG_HOME + '/bc_client')
if not os.path.isdir(CONFIGS):
    os.mkdir(CONFIGS)


class Main:
    def __init__(self):
        self.bandcamp = bc_api.Bandcamp()
        self.wrapper = curses_UI.create_wrapper()
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

main = Main()
