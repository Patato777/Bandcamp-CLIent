import curses
import logging
import os
import time

from pynput import keyboard

dirname = os.path.dirname(__file__)


class Wrapper:
    color_dict = {'30': curses.COLOR_BLACK, '31': curses.COLOR_RED, '32': curses.COLOR_GREEN,
                  '33': curses.COLOR_YELLOW, '34': curses.COLOR_BLUE, '35': curses.COLOR_MAGENTA,
                  '36': curses.COLOR_CYAN, '37': curses.COLOR_WHITE}

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.start_screen()
        curses.curs_set(0)
        self.stdscr.getch()
        self.binds = {'/': self.getcmd}
        self.stdscr.clear()
        self.cmdwin = self.stdscr.derwin(1, curses.COLS, curses.LINES - 1, 0)
        self.mainwin = self.stdscr.derwin(curses.LINES - 2, curses.COLS, 0, 0)
        self.mainwin.border()
        self.mainwin.addstr(0, 2, 'Volume─┤          ├')
        self.update_vol(100)
        self.title = self.stdscr.derwin(3, curses.COLS - 2, 1, 1)
        try:
            self.title.addstr(2, 0, '─' * (curses.COLS - 2))
        except curses.error:
            logging.debug('Nothing wrong, just an old curses issue')
        self.menuwin = self.mainwin.derwin(curses.LINES - 7, curses.COLS - 2, 4, 1)
        self.time_bar = ProgBar(self.stdscr, curses.LINES - 2)
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        self.commands = dict()
        self.cmderror = False
        logging.debug("Let's start!")

    def start_screen(self):
        with open(dirname + '/resources/play bc button.utf8ans', encoding='utf-8') as file:
            for k, line in enumerate(file):
                y = 0
                for part in line.split('['):
                    if part.startswith('1;'):
                        curses.init_pair(self.color_dict[part[2:4]], self.color_dict[part[2:4]], curses.COLOR_BLACK)
                        try:
                            self.stdscr.addstr(k, y, part[5:], curses.color_pair(self.color_dict[part[2:4]]))
                        except curses.error:
                            logging.debug('Nothing wrong, just an old curses issue (line 61)')
                        y += len(part[5:])
                    else:
                        beg = 2 if (len(part) > 1 and part[1] == 'm') else 0
                        try:
                            self.stdscr.addstr(k, y, part[beg:])
                        except curses.error:
                            logging.debug('Nothing wrong, just an old curses issue (line 68)')
                            logging.debug(
                                f'COLS: {curses.COLS}, LINES: {curses.LINES}, part: {part}, line: {k}, beg: {beg}')
                        y += len(part[2:])
        self.stdscr.border()

    def bind(self, key, command):
        self.binds.update({key: command})

    def unbind(self, key):
        try:
            del self.binds[key]
        except KeyError:
            return False

    def new_command(self, command, function, arity):
        self.commands.update({command: (function, arity)})

    def update_vol(self, vol):
        self.mainwin.addstr(0, 9, f'|          |')
        volbar = round(vol / 10) * ' '
        self.mainwin.addstr(0, 10, volbar, curses.A_STANDOUT)

    def update_title(self, title, subtitle):
        self.title.addstr(0, 0, title.center(curses.COLS - 2))
        logging.debug(title)
        self.title.addstr(1, 0, subtitle.center(curses.COLS - 2))
        self.title.refresh()
        logging.debug(subtitle)

    def make_menu(self, items):
        self.menuwin.clear()
        menu = Menu(items, self.menuwin)
        self.bind(keyboard.Key.up, menu.up)
        self.bind(keyboard.Key.down, menu.down)
        return menu

    def getcmd(self):
        self.listener.stop()
        cmd, *args = self.cmdentry().split(' ')
        if cmd in self.commands.keys() and self.commands[cmd][1] == len(args):
            self.commands[cmd][0](*args)
            self.cmdwin.clear()
        else:
            self.cmdwin.addstr(0, 0, 'Unknown command', curses.A_STANDOUT)
            self.cmderror = True
        self.cmdwin.refresh()
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def cmdentry(self):
        self.cmdwin.clear()
        self.cmdwin.addstr(0, 0, '/')
        curses.curs_set(2)
        curses.echo()
        cmd = self.cmdwin.getstr(0, 1)
        curses.noecho()
        curses.curs_set(0)
        logging.debug(cmd.decode())
        return cmd.decode()

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


class Menu:
    def __init__(self, content, win):
        self.window = win
        self.content = content
        self.miny, self.minx = self.window.getbegyx()
        self.maxy, self.maxx = self.window.getmaxyx()
        items = [c.repr for c in content] if content != list() else [['Nothing']]
        self.lines = len(self.content)
        self.rows = len(items[0])
        self.rowwidth = [max([len(i[r]) for i in items]) for r in range(self.rows)]
        maxrow = self.rowwidth.index(max(self.rowwidth))
        self.rowwidth[maxrow] -= sum(self.rowwidth) + self.rows - self.maxx
        self.strings = list()
        for line, item in enumerate(items):
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
        self.highlighted = 0
        self.highlight(0)

    def show(self, begin):
        self.top, self.end = begin, begin + self.maxy
        for line, string in enumerate(self.strings[self.top:self.end]):
            try:
                self.window.addstr(line, 0, string)
            except curses.error:
                logging.debug('Nothing wrong, just an old curses issue')
        self.window.refresh()

    def highlight(self, item):
        if item in range(self.top, self.end):
            try:
                self.window.addstr(self.highlighted - self.top, 0, self.strings[self.highlighted])
            except curses.error:
                logging.debug('Nothing wrong, just an old curses issue')
            try:
                self.window.addstr(item - self.top, 0, self.strings[item], curses.A_STANDOUT)
            except curses.error:
                logging.debug('Nothing wrong, just an old curses issue')
            logging.debug('Still in')
        elif item < self.top:
            self.show(item)
            self.highlight(item)
        elif item > self.end:
            self.show(item - self.maxy)
            self.highlight(item)
        elif item == self.end:
            self.show(self.top + 1)
            self.highlight(item)
        self.highlighted = item
        self.window.refresh()

    def select(self):
        if self.content:
            return self.content[self.highlighted]

    def up(self):
        if self.highlighted > 0:
            self.highlight(self.highlighted - 1)

    def down(self):
        if self.highlighted < self.lines - 1:
            self.highlight(self.highlighted + 1)


class ProgBar:
    def __init__(self, scr, y, char='=>-'):
        self.scr = scr
        self.y = y
        self.char = char
        self.total_time = 0
        try:
            self.scr.addstr(self.y, 0, self.char[1] + self.char[2] * (curses.COLS - 1))
        except curses.error:
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
        except curses.error:
            logging.debug('Nothing wrong, just an old curses issue')
        logging.debug(self.total_time)
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


def stop():
    curses.endwin()


logging.basicConfig(filename='main.log', level=logging.DEBUG)
logging.debug(f'-------{time.asctime()}-------')


def create_wrapper():
    return curses.wrapper(Wrapper)
