import os

from pynput import keyboard
from src.bc_client import bc_api
from src.bc_client import curses_UI

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", "~/.config")
CONFIGS = os.path.expanduser(XDG_CONFIG_HOME + '/bc_client')
if not os.path.isdir(CONFIGS):
    os.mkdir(CONFIGS)


class Main:
    def __init__(self):
        self.bandcamp = bc_api.Bandcamp
        self.wrapper = curses_UI.create_wrapper()
        if os.path.isfile(CONFIGS + '/favorites'):
            with open(CONFIGS + '/favorites', 'r') as fav:
                self.favorites = eval(fav.read())
        else:
            self.favorites = {'Artists': list(), 'Albums': list(), 'Tracks': list()}
        self.menu = self.fav_menu()
        self.wrapper.mainloop()

    def fav_menu(self, category='base'):
        if category == 'base':
            menu = self.wrapper.make_menu([['Artists'], ['Albums'], ['Tracks']])
            self.wrapper.update_title('Favorites', '')
            self.wrapper.bind(keyboard.Key.enter, lambda: self.fav_menu(menu.select()[0]))
        else:
            menu = self.wrapper.make_menu(self.favorites[category])
            self.wrapper.update_title('Favorites', category)
        return menu

main = Main()
