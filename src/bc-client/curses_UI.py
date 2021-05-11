import curses
import logging
import sys
import time

from pynput import keyboard


class Wrapper:
    color_dict = {'30': curses.COLOR_BLACK, '31': curses.COLOR_RED, '32': curses.COLOR_GREEN,
                  '33': curses.COLOR_YELLOW, '34': curses.COLOR_BLUE, '35': curses.COLOR_MAGENTA,
                  '36': curses.COLOR_CYAN, '37': curses.COLOR_WHITE}

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.start_screen()
        curses.curs_set(0)
        self.stdscr.getch()
        self.binds = {'/': self.getcmd, 'q': self.exit}
        self.stdscr.clear()
        self.cmdwin = self.stdscr.derwin(1, curses.COLS, curses.LINES - 1, 0)
        self.mainwin = self.stdscr.derwin(curses.LINES - 1, curses.COLS, 0, 0)
        self.mainwin.border()
        self.mainwin.addstr(0, 2, 'Volume─┤          ├')
        self.update_vol(80)
        self.title = self.stdscr.derwin(3, curses.COLS - 2, 1, 1)
        try:
            self.title.addstr(2, 0, '─' * (curses.COLS - 2))
        finally:
            logging.debug('Nothing wrong, just an old curses issue')
        self.menuwin = self.mainwin.derwin(curses.LINES - 6, curses.COLS - 2, 4, 1)
        self.time_bar = ProgBar(self.stdscr, curses.LINES - 1)
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        # Just to test, remove when done
        self.time_bar.set_total_time(100)
        self.bind(keyboard.Key.left, lambda: self.time_bar.update(self.time_bar.current - 1))
        self.bind(keyboard.Key.right, lambda: self.time_bar.update(self.time_bar.current + 1))
        self.menu = self.make_menu([['20', 'ALBUM', 'Super Meat Boy! - Digital Special Edition Soundtrack'],
                                    ['21', 'TRACK', 'Dun Dun Dun']] * 20)
        ####
        self.commands = {b'quit': self.exit}
        self.cmderror = False
        logging.debug("Let's start!")
        self.stop = False
        self.mainloop()

    def start_screen(self):
        with open('./resources/play bc button.utf8ans', encoding='utf-8') as file:
            for k, line in enumerate(file):
                y = 0
                for part in line.split('['):
                    if part.startswith('1;'):
                        curses.init_pair(self.color_dict[part[2:4]], self.color_dict[part[2:4]], curses.COLOR_BLACK)
                        self.stdscr.addstr(k, y, part[5:], curses.color_pair(self.color_dict[part[2:4]]))
                        y += len(part[5:])
                    else:
                        beg = 2 if (len(part) > 1 and part[1] == 'm') else 0
                        try:
                            self.stdscr.addstr(k, y, part[beg:])
                        finally:
                            logging.debug('Nothing wrong, just an old curses issue')
                        y += len(part[2:])
        self.stdscr.border()

    def bind(self, key, command):
        self.binds.update({key: command})

    def unbind(self, key):
        try:
            del self.binds[key]
        finally:
            return False

    def new_command(self, command, function):
        self.commands.update({command: function})

    def update_vol(self, vol):
        self.mainwin.addstr(0, 9, f'|          |')
        volbar = round(vol / 10) * ' '
        self.mainwin.addstr(0, 10, volbar, curses.A_STANDOUT)

    def update_title(self, title, subtitle):
        self.title.addstr(0, 0, title.center(curses.COLS - 2))
        self.title.addstr(1, 0, subtitle.center(curses.COLS - 2))

    def make_menu(self, items):
        menu = Menu(items, self.menuwin)
        self.bind(keyboard.Key.up, self.menu.up)
        self.bind(keyboard.Key.down, self.menu.down)
        return menu

    def build(self):
        pass

    def getcmd(self):
        self.listener.stop()
        cmd = self.cmdentry()
        if cmd in self.commands.keys():
            self.commands[cmd]()
            self.cmdwin.clear()
        else:
            self.cmdwin.addstr(0, 0, 'Unknown command', curses.A_STANDOUT)
            self.cmderror = True
        self.cmdwin.refresh()
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def exit(self):
        curses.endwin()
        self.stop = True
        sys.exit()

    def cmdentry(self):
        self.cmdwin.clear()
        self.cmdwin.addstr(0, 0, '/')
        curses.curs_set(2)
        curses.echo()
        cmd = self.cmdwin.getstr(0, 1)
        curses.noecho()
        curses.curs_set(0)
        return cmd

    def on_press(self, key):
        self.stdscr.nodelay(True)
        self.stdscr.getch()
        self.stdscr.getch()
        self.stdscr.nodelay(False)
        if self.cmderror:
            self.cmdwin.clear()
            self.cmderror = False
            self.cmdwin.refresh()
        if hasattr(key, 'char'):
            if key.char in self.binds.keys():
                self.binds[key.char]()
            else:
                logging.debug('Key pressed: ' + key.char)
        elif key in self.binds.keys():
            self.binds[key]()
        else:
            logging.debug('Key pressed: ' + str(key))

    def mainloop(self):
        self.stdscr.refresh()
        while not self.stop:
            time.sleep(1)


class Menu:
    def __init__(self, items, win):
        self.window = win
        self.items = items
        self.miny, self.minx = self.window.getbegyx()
        self.maxy, self.maxx = self.window.getmaxyx()
        self.lines = len(self.items)
        self.rows = len(self.items[0])
        self.rowwidth = [max([len(i[r]) for i in self.items]) for r in range(self.rows)]
        maxrow = self.rowwidth.index(max(self.rowwidth))
        self.rowwidth[maxrow] -= sum(self.rowwidth) + self.rows - self.maxx
        self.strings = list()
        for line, item in enumerate(self.items):
            totalstring = str()
            for row, elem in enumerate(item):
                if len(elem) > self.rowwidth[row] > 3:
                    string = elem[:self.rowwidth[row] - 1] + '…'
                else:
                    string = elem
                totalstring += string.ljust(self.rowwidth[row] + 1)
            self.strings.append(totalstring)
        self.top, self.end = 0, self.maxy
        self.show(0)
        self.selected = 0
        self.select(0)

    def show(self, begin):
        self.top, self.end = begin, begin + self.maxy
        for line, string in enumerate(self.strings[self.top:self.end]):
            try:
                self.window.addstr(line, 0, string)
            finally:
                logging.debug('Nothing wrong, just an old curses issue')
        self.window.refresh()

    def select(self, item):
        if item in range(self.top, self.end):
            try:
                self.window.addstr(self.selected - self.top, 0, self.strings[self.selected])
            finally:
                logging.debug('Nothing wrong, just an old curses issue')
            try:
                self.window.addstr(item - self.top, 0, self.strings[item], curses.A_STANDOUT)
            finally:
                logging.debug('Nothing wrong, just an old curses issue')
            logging.debug('Still in')
        elif item < self.top:
            self.show(item)
            self.select(item)
        elif item > self.end:
            self.show(item - self.maxy)
            self.select(item)
        elif item == self.end:
            self.show(self.top + 1)
            self.select(item)
        self.selected = item
        self.window.refresh()

    def up(self):
        if self.selected > 0:
            self.select(self.selected - 1)

    def down(self):
        if self.selected < self.lines - 1:
            self.select(self.selected + 1)


class ProgBar:
    def __init__(self, scr, y, char='=>-'):
        self.scr = scr
        self.y = y
        self.char = char
        try:
            self.scr.addstr(self.y, 0, self.char[1] + self.char[2] * (curses.COLS - 1))
        finally:
            logging.debug('Nothing wrong, just an old curses issue')

    def set_total_time(self, total_time):
        self.total_time = total_time
        self.totalt_str = time.strftime("%H:%M:%S", time.gmtime(total_time)) \
            if total_time >= 3600 else time.strftime("%M:%S", time.gmtime(total_time))
        self.time_x = curses.COLS - 2 - 2 * len(self.totalt_str)
        self.bar_length = self.time_x - 2
        self.current = 0
        self.progress = 0
        cur_str = "00:00:00"[-len(self.totalt_str):]
        time_str = '[' + cur_str + '/' + self.totalt_str + ']'
        try:
            self.scr.addstr(self.y, self.time_x - 1, time_str)
        finally:
            logging.debug('Nothing wrong, just an old curses issue')
        self.update(0)

    def update(self, new):
        new = max(0, min(new, self.total_time))
        cur_str = time.strftime("%H:%M:%S", time.gmtime(new))[-len(self.totalt_str):]
        self.scr.addstr(self.y, self.time_x, cur_str)
        progress = int(self.bar_length * new / self.total_time)
        length = abs(progress - self.progress)
        if new > self.current:
            self.scr.addstr(self.y, self.progress, self.char[0] * length + self.char[1])
        elif new < self.current:
            self.scr.addstr(self.y, progress, self.char[1] + self.char[2] * length)
        self.current = new
        self.progress = progress


logging.basicConfig(filename='main.log', level=logging.DEBUG)
logging.debug('--------------')
curses.wrapper(Wrapper)
