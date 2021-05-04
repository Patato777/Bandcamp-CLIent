import curses,logging,sys,time
from curses.textpad import Textbox
from curses import panel
from pynput import keyboard

class Wrapper:
    def __init__(self,stdscr) :
        self.stdscr = stdscr
        self.startscreen()
        curses.curs_set(0)
        self.stdscr.getch()
        self.binds = {'/' : self.getcmd, 'q' : self.exit}
        self.build()
        self.commands = {b'quit' : self.exit}
        self.cmderror = False
        logging.debug("Let's start!")
        self.mainloop()

    def startscreen(self) :
        with open('./resources/play button.utf8ans',encoding='utf-8') as file :
            for k,line in enumerate(file) :
                self.stdscr.addstr(k,0,line[:-1])
        self.stdscr.border()

    def bind(self,key,command) :
        self.binds.update({key:command})

    def unbind(self,key) :
        try :
            del self.binds[key]
        except :
            return False

    def new_command(self,command,function) :
        self.commands.update({command:function})

    def update_vol(self,vol) :
        self.mainpan.addstr(0,9,f'|          |')
        volbar = round(vol/10)*' '
        self.mainpan.addstr(0,10,volbar,curses.A_STANDOUT)

    def update_title(self,title,subtitle) :
        self.title.addstr(0,0,title.center(curses.COLS-2))
        self.title.addstr(1,0,subtitle.center(curses.COLS-2))

    def make_menu(self,items) :
        self.menu = Menu(items,self.menuwin)
        self.bind(keyboard.Key.up,self.menu.up)
        self.bind(keyboard.Key.down,self.menu.down)

    def build(self) :
        self.stdscr.clear()
        self.cmdpan = Subpan(self.stdscr,0,curses.LINES-1,curses.COLS,1)
        self.mainpan = Subpan(self.stdscr,0,0,curses.COLS,curses.LINES-1)
        self.mainpan.window.border()
        self.mainpan.addstr(0,2,'Volume─┤          ├')
        self.update_vol(80)
        self.title = Subpan(self.stdscr,1,1,curses.COLS-2,3)
        try :
            self.title.addstr(2,0,'─'*(curses.COLS-2))
        except :
            logging.debug('Nothing wrong, just an old curses issue')
        self.menuwin = self.stdscr.subwin(curses.LINES-6,curses.COLS-2,4,1)
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        self.make_menu([['20','ALBUM','Super Meat Boy! - Digital Special Edition Soundtrack']]*20)
        
    def getcmd(self) :
        self.listener.stop()
        self.cmd = self.cmdentry()
        if self.cmd in self.commands.keys() :
            self.commands[self.cmd]()
            self.cmdpan.hide()
        else :
            self.cmdpan.edit('Unknow command',curses.A_STANDOUT)
            self.cmderror = True
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def exit(self) :
        curses.endwin()
        control = keyboard.Controller()
        control.press(keyboard.Key.ctrl)
        control.press('c')
        sys.exit()

    def cmdentry(self) :
        curses.echo()
        self.cmdpan.show('/')
        curses.curs_set(2)
        cmd = self.cmdpan.window.getstr(0,1)
        curses.curs_set(0)
        curses.noecho()
        return cmd

    def on_press(self,key) :
        self.key = key
        if self.cmderror :
            self.cmdpan.hide()
            self.cmderror = False
        if hasattr(self.key,'char') :
            if self.key.char in self.binds.keys() :
                self.binds[self.key.char]()
            else :
                logging.debug('Key pressed: '+ self.key.char + self.binds.keys())
        elif self.key in self.binds.keys() :
            self.binds[self.key]()
        else :
            logging.debug('Key pressed: '+ str(self.key))

    def mainloop(self) :
        while True :
            self.stdscr.refresh()
            time.sleep(1)
            
class Subpan :
    def __init__(self,scr,x,y,width,height) :
        self.scr = scr
        self.window = self.scr.derwin(height,width,y,x)
        self.panel = panel.new_panel(self.window)
        self.hide()
        self.addstr = self.window.addstr

    def show(self,msg,effect=0) :
        self.panel.top()
        self.edit(msg,effect)
        self.panel.show()
        self.window.refresh()

    def edit(self,msg,effect=0):
        self.window.clear()
        try :
            self.window.addstr(0,0,msg,effect)
        except :
            logging.debug('Nothing wrong, just an old curses issue')
        self.window.refresh()

    def hide(self) :
        self.window.clear()
        self.panel.bottom()
        self.panel.hide()
        self.window.refresh()

class Menu :
    def __init__(self,items,win) :
        self.window = win
        self.items = items
        self.miny,self.minx = self.window.getbegyx()
        self.maxy,self.maxx = self.window.getmaxyx()
        self.lines = len(self.items)
        self.create()

    def create(self) :
        self.rows = len(self.items[0])
        self.rowwidth = [max([len(i[r]) for i in self.items]) for r in range(self.rows)]
        maxrow = self.rowwidth.index(max(self.rowwidth))
        self.rowwidth[maxrow] -= sum(self.rowwidth)+self.rows-self.maxx
        self.strings = list()
        for line,item in enumerate(self.items) :
            totalstring = str()
            for row,elem in enumerate(item) :
                if len(elem) > self.rowwidth[row] and self.rowwidth[row] > 3:
                    string = elem[:self.rowwidth[row]-1]+'…'
                else :
                    string = elem
                totalstring += string.ljust(self.rowwidth[row]+1)
            self.strings.append(totalstring)
        self.show(0)
        self.selected = 0
        self.select(0)

    def show(self,begin) :
        self.top,self.end = begin,begin+self.maxy
        for line,string in enumerate(self.strings[self.top:self.end]) :
            try :
                self.window.addstr(line,0,string)
            except :
                logging.debug('Nothing wrong, just an old curses issue')
        self.window.refresh()

    def select(self,item) :
        if item in range(self.top,self.end) :
            self.window.addstr(self.selected,0,self.strings[self.selected])
            self.window.addstr(item,0,self.strings[item],curses.A_STANDOUT)
        elif item < self.top :
            self.show(item)
            self.select(item)
        elif item > self.end :
            self.show(item-self.maxy)
            self.select(item)
        self.selected = item
        self.window.refresh()
    
    def up(self) :
        if self.selected > 0 :
            self.select(self.selected-1)

    def down(self) :
        if self.selected < self.lines :
            self.select(self.selected+1)

class ProgBar :
    def __init__(self,scr,y,totaltime,char='=>-') :
        self.scr = scr
        self.totaltime = totaltime
        self.y = y
        
logging.basicConfig(filename='main.log',level=logging.DEBUG)
curses.wrapper(Wrapper)
