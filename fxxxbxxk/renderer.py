# -*- coding: utf-8 -*-

__author__ = 'benjamin'

from blessings import Terminal
import sys, subprocess, threading
import re, itertools
from textwrap import wrap
import random, time, math, os

import symbols
from alphabet import alphabet

alphabet_clean_re = re.compile(r'[^0-9 A-Za-z!?:/.\'",\-]')

ANSI_escape_sequences = re.compile(r"""
    \x1b     # literal ESC
    \[       # literal [
    [;\d]*   # zero or more digits or semicolons
    [A-Za-z] # a letter
    """, re.VERBOSE)

def strip_ANSI_escape_sequences(s):
    return ANSI_escape_sequences.sub("", s)

def extract_ANSI_escape_sequences(s):
    sequences = []
    offset=0
    for match in ANSI_escape_sequences.finditer(s):
        sequences.append( (match.group(),match.start()) )
        offset += match.end()-match.start()
    return sequences

def reinject_ANSI_escape_sequences(str_list, ANSI_list):
    if ANSI_list is None or len(ANSI_list) is 0:
        return str_list
    new_list = []
    count = 0
    ansi_iter = iter(ANSI_list)
    ansi = ansi_iter.next()
    for line in str_list:
        fro = 0
        new_line = ''
        length = len(line)
        next_count = count + length
        while ansi is not None and next_count >= ansi[1]:
            to = length-(next_count - ansi[1])
            new_line += line[fro:to] + ansi[0]
            fro = to
            next_count += len(ansi[0])
            try:
                ansi = ansi_iter.next()
            except StopIteration:
                ansi = None
                break
        count = next_count+1
        new_line += line[fro:]
        new_list.append(new_line)
    return new_list


class BackgroundDrawingThread(threading.Thread):

    def __init__(self, renderer):
        super(BackgroundDrawingThread, self).__init__()
        self._stop = threading.Event()
        self.renderer = renderer

    def run(self):
        count = 0.2
        self.renderer.sleep(0.2)

        while count < 120:
            if self.stopped():
                break
            if math.fmod(count, 10) < 0.05:
                self.renderer.download_statement()
                self.renderer.sleep(1)
                count += 1
            self.renderer.sleep(0.05)
            count += 0.05
    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class Renderer(object):

    def __init__(self):
        self.__term__ = Terminal()
        self.tty = self.__term__.is_a_tty
        self.width = self.__term__.width or 0
        self.height = self.__term__.height or 0
        self.__noise_rate__ = 0.1
        self.__noise_count__ = 0.0
        self.__noise_exclusion__ = []
        self.__thread__ = None

    def __getattr__(self, item):
        try:
            def __tmp__():
                self.draw_symbol(getattr(symbols,item))
            return __tmp__
        except AttributeError:
            pass

    def start(self):
        if self.tty:
            print self.__term__.enter_fullscreen+self.__term__.civis+'\033]2m'
        #self.__drawframe__()

    def end(self):
        if self.tty:
            print self.__term__.exit_fullscreen + self.__term__.normal + self.__term__.cnorm

    def __random_pos__(self,w,h):
        _w = self.width - w
        _h = self.height - h
        if _w < 0:
            _w = 0
        if _h < 0:
            _h = 0
        x = random.randint(0, _w)
        y = random.randint(0, _h)
        return x, y

    def __get_pos__(self):
        if not self.tty:
            return 0, 0
        proc = subprocess.Popen('echo "\033[6n\c"; read -s -d R foo; echo $foo | cut -d \[ -f 2 1>&2',
                                shell=True,
                                stderr=subprocess.PIPE)
        val = proc.communicate()[1].split(';')
        return int(val[0]), int(val[1])

    def draw(self, str, x=None, y=None, delay=0):

        """draw a sting image wherever
        """
        if not self.tty:
            print strip_ANSI_escape_sequences(str)
            return

        if x is None or y is None:
            pos = self.__get_pos__()
            x = pos[1] if x is None else x
            y = pos[0] if y is None else y

        if y >= self.height or x >= self.width:
            raise Exception('NOT WITHIN BOUNDS')

        lines = str.splitlines()

        left_offset = 0
        top_offset = 0
        bottom_offset = len(lines)
        if x < 0:
            left_offset = x * -1
            x = 0
        if y < 0:
            top_offset = y * -1
            y = 0
        if y + bottom_offset > self.height:
            bottom_offset = self.height-y

        #set exlusion for noise
        draw_width = max([len(strip_ANSI_escape_sequences(line)) for line in lines])
        self.__noise_exclusion__.append([x,y,x+draw_width, y+len(lines)])

        sys.stdout.write('\033[s') # saves curser position
        sys.stdout.write('\033[{1};{0}H'.format(x+1,y+1)) # move to position

        #write only escape codes from lines not printed
        for line in lines[:top_offset]:
            for match in ANSI_escape_sequences.finditer(line):
                sys.stdout.write(match.group())
        #then write all lines until bottom_offset
        for line in lines[top_offset:bottom_offset]:
            fragments = ANSI_escape_sequences.split(line)
            escapes = ANSI_escape_sequences.findall(line)
            length = sum(len(s) for s in fragments)
            if x + length > self.width:
                length = self.width - x
            count = 0
            for text, escape in itertools.izip_longest(fragments, escapes):
                text_length = len(text)
                if text_length > 0:
                    next_count = text_length + count
                    txt = ''
                    if count < left_offset < next_count:
                        offset = left_offset-count
                        txt = text[offset:]
                    elif count <= length < next_count:
                        offset = length-count
                        txt = text[:offset]
                    elif left_offset <= count < length:
                        txt = text
                    if delay > 0:
                        for c in txt:
                            sys.stdout.write(c)
                            sys.stdout.flush()
                            self.sleep(delay)
                    else:
                        sys.stdout.write(txt)

                    count = next_count
                if escape is not None:
                    sys.stdout.write(escape)
            y += 1
            sys.stdout.write('\033[{1};{0}H'.format(x+1, y+1)) # move to position
            #if delay > 0:
            #    sys.stdout.flush()
            #    time.sleep(delay)
        #then write remaining escape codes
        for line in lines[bottom_offset:]:
            for match in ANSI_escape_sequences.finditer(line):
               sys.stdout.write(match.group())
        sys.stdout.write('\033[u') # restores curser position
        sys.stdout.flush()

    def draw_symbol(self, symbol):
        self.__release_exclusion__()
        like = symbol.splitlines()
        h = len(like)
        w = max(map(len,like))
        x, y = self.__random_pos__(w, h)
        self.draw(symbol, x, y)

    def draw_post(self,s,w=70):
        self.__release_exclusion__()
        main_line = u'═'*(w-2)
        top_line =  u'╔'+main_line+u'╗\n'
        bottom_line = u'╚'+main_line+u'╝'
        text_line = u'║' + ' '*(w-2) + u'║\n'
        minor_line = u'╟'+u'─'*(w-2)+u'╢\n'
        if isinstance(s, basestring):
            if s.isspace():
                return
            s = s.splitlines()
        container = []
        content = []
        for block in s:
            wrapped = self.warp_ignore_ANSI(block, w-4)
            container.append(text_line * len(wrapped))
            content.append('\n'.join(wrapped))
        container = u'╔'+main_line+u'╗\n' + minor_line.join(container) + bottom_line
        content = '\n\n'.join(content)
        if len(content.strip()) == 0:
            return
        if self.tty:
            x, y = self.__random_pos__(w,len(container.splitlines()))
            self.animate_symbol(container,4,x,y)
            self.draw(content,x+2,y+1,0.005)
        else:
            print container

    def warp_ignore_ANSI(self, s, w=70):
        seq = extract_ANSI_escape_sequences(s)
        new_str = strip_ANSI_escape_sequences(s)
        text = wrap(new_str,w)
        justify = [w - len(line) for line in text]
        text = reinject_ANSI_escape_sequences(text,seq)
        lines = []
        for line, just in itertools.izip(text,justify):
            lines.append(line + u' '*just)
        return lines

    def writewords(self,word=' ', delay=0.1):
        self.__release_exclusion__()
        word = alphabet_clean_re.sub('',word)
        word = ' ' + word + ' '
        #print self.__term__.clear
        c_lengths = [ len(strip_ANSI_escape_sequences(alphabet[c.lower()].splitlines()[0])) for c in word ]
        word_length = sum(c_lengths)
        h = 1
        if word_length >= self.width:
            tmp = 0
            for l in c_lengths:
                tmp += l
                if tmp >= self.width:
                    h += 1
                    tmp = l

        x, y = self.__random_pos__(word_length,7*h)
        last_letter = ''
        for c, length in zip(word,c_lengths):
            if x + length >= self.width:
                if last_letter.isalpha():
                    self.draw(alphabet['-'],x,y)
                else:
                    self.draw(alphabet[' '],x,y)
                x = 0
                y += 7
                if y >= self.height-7:
                    y = 0
                self.__release_exclusion__()

            self.draw(alphabet[c.lower()],x,y)
            x += length
            self.sleep(delay)
            last_letter = c

    def like(self):
        self.animate_symbol(symbols.like)
        self.writewords('liked')

    def comment(self):
        self.animate_symbol(symbols.comment)

    def download_statement(self):
        download_statement = '\033[1mthe source code for this artwork is available free at: \033[31mhttp://' + \
                             os.environ['IP'] + \
                             '\033[0;38m\nnote: you must be connected to the local wifi network.'
        self.draw_post(download_statement,35)

    def animate_symbol(self, symbol, speed=2, x=None, y=None):
        self.__release_exclusion__()
        lines = symbol.splitlines()
        h = len(lines)
        w = max(map(len,lines))
        xy = self.__random_pos__(w,h)
        if x is None :
            x = xy[0]
        if y is None :
            y = xy[1]
        cx = int(w / 2.0)
        cy = int(h / 2.0)
        count = 0
        mag = math.ceil(max(w/2,h)/2)
        while count <= mag:
            count += speed
            subset = ''
            ly = cy-count
            lx = cx-count*2
            if ly < 0 : ly = 0
            if lx < 0 : lx = 0
            for line in lines[ly:cy+count]:
                subset += line[lx:cx+count*2] +'\n'
            self.draw(subset, x+lx,y+ly)
            self.sleep(0.05)

    def __release_exclusion__(self):
        self.__noise_exclusion__ = []

    def __within_exclusion__(self, x,y):
        within = False
        for bounds in self.__noise_exclusion__:
            if not((x < bounds[0] or x >= bounds[2]) or (y < bounds[1] or y >= bounds[3])):
                within = True
                break
        return within

    def draw_noise(self, c=30):

        points = [ random.randint(0, self.width * self.height) for x in range(c)]

        for v in sorted(points):
            x = v % self.width
            y = int(float(v) / self.width)

            if not self.__within_exclusion__(x,y):

                d = -1
                if y%10 > 5:
                    d = 1
                if x%20 > 10:
                    d *= -1

                i = x + y * d
                txt = u'▓▒░ ░▒'[i%5]
                sys.stdout.write('\033[{1};{0}H'.format(x + 1, y + 1))
                sys.stdout.write(txt)
        sys.stdout.flush()

    def sleep(self,delay=1.0):
        tmp_delay = delay
        self.__noise_count__ += delay
        if self.__noise_count__ >= self.__noise_rate__:
            part, whole = math.modf(self.__noise_count__ / self.__noise_rate__)
            with self.__term__.location(0,0):
                for i in range(int(whole)):
                    self.draw_noise()
                    if tmp_delay > self.__noise_rate__:
                        time.sleep(self.__noise_rate__)
                        tmp_delay -= self.__noise_rate__
            self.__noise_count__ = math.fmod(self.__noise_count__, self.__noise_rate__)
        if tmp_delay > 0:
            time.sleep(tmp_delay)

    def start_threaded_noise(self):
        self.__noise_exclusion__ = []
        if self.__thread__ is None or not self.__thread__.is_alive():
            self.__thread__ = BackgroundDrawingThread( self )
            self.__thread__.setDaemon(True)
            self.__thread__.start()

    def stop_threaded_noise(self):
        if self.__thread__ is not None and self.__thread__.is_alive():
            self.__thread__.stop()
            while self.__thread__.is_alive():
                time.sleep(0.01)
            self.__thread__ = None

if __name__ == '__main__':
    renderer = Renderer()
    renderer.start()
    try:
        x=renderer.width-50
        y=renderer.height-50
        while True:

            """
            y += 1
            x+=2
            if y >= renderer.height:
                y = -40
            if x >= renderer.width:
                x =- 30
            #sys.stdout.write('\033[2J')
            #renderer.draw(thumb, x,y)
            #w = random.randint(30,70)
            #renderer.draw_noise()
            #renderer.writewords(' hey ')
            #time.sleep(0.5)
            #renderer.draw_noise()
            #renderer.writewords(' SAVIOUR ')
            #time.sleep(0.5)
            #renderer.draw_noise()
            #renderer.writewords(' NOT THIS story ')
            #time.sleep(0.5)
            #renderer.draw_noise()
            renderer.draw_post(u"this \033[1mbold text goes here.\033[0m\033[39m\n is not maybe this works but I ma not sure ok but.this \033[1mbold text goes\n here.\033[0m is not maybe this works but I ma not sure ok but.this \033[1mbold text goes here.\033[0m is not maybe this works but I ma not sure ok but.")
           # renderer.draw_comment(u"this bold text goes here. is not maybe this works but I ma not sure ok but.")
            #renderer.sleep(5)
            renderer.writewords(' like ')
            renderer.sleep(1)
            renderer.animate_symbol(symbols.like)
            renderer.sleep(1)
            renderer.writewords(' comment ')
            renderer.sleep(1)
            renderer.animate_symbol(symbols.comment)
            renderer.sleep(1)
            #break"""
            renderer.writewords('this is it ok a really simple test of a long sentence.! super simple test of a long sentence')
            renderer.sleep(5)
            break
    except KeyboardInterrupt:
        pass
    renderer.end()
