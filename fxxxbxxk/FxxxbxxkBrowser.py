import sys
import logging
import time
import random
import re
import cookielib

import mechanize
from bs4 import BeautifulSoup
from renderer import Renderer

class FacebookPost:

    def __init__(self, content, comment=None, like=None, comment_count=0):
        self.content = content
        self.comment_url = comment
        self.like_url = like
        self.comment_count = comment_count


class FxxxbxxkBrowser:

    def __init__(self):

        self.__story__ = []
        self.__story_pos__ = 0
        self.__done__ = False
        with open('fxxxbxxk.txt') as file:
            self.__story__ = file.readlines()

        self.__timeout__ = 100.0
        self.renderer = Renderer()
        self.__fb_site__ = 'https://m.facebook.com'
        self.__response__ = None
        self.__soup__ = None
        self.__logged_in__ = False
        self.logger = logging.getLogger("mechanize")
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.DEBUG)
        self.browser = mechanize.Browser()
        self.__cj__ = cookielib.LWPCookieJar()
        self.__cj__.filename = 'tempcookies.lwp'
        self.__setup__()

    def __del__(self):
        try:
            self.__cj__.save()
        except AttributeError:
            print 'cookies not saved'

    def __setup__(self):
        print 'setting up browser'
        try:
            self.__cj__.load()
        except Exception:
            print '\n\nno cookies\n\n'
            pass
        #add cooking so facebook sends no javascript
        ck2 = cookielib.Cookie(version=0, name='locale', value='en_US', port=None, port_specified=False, domain='.facebook.com', domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=None, discard=False, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.__cj__.set_cookie(ck2)
        ck1 = cookielib.Cookie(version=0, name='noscript', value='1', port=None, port_specified=False, domain='.facebook.com', domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=None, discard=False, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.__cj__.set_cookie(ck1)

        self.browser.set_cookiejar(self.__cj__)
        # Browser options
        #self.browser.set_debug_http(True)
        #self.browser.set_debug_responses(True)
        self.browser.set_debug_redirects(True)
        self.browser.set_handle_equiv(True)
        self.browser.set_handle_gzip(True)
        self.browser.set_handle_redirect(True)
        self.browser.set_handle_referer(True)
        self.browser.set_handle_robots(False)
        self.browser.set_handle_refresh(False)  # can sometimes hang without this
        self.browser.addheaders = [('User-agent',
                                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'),
                                   ('accept',
                                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8)')
                                   ]
        self.open()

    @staticmethod
    def __control_has__(control, attrs,values=None):
        if isinstance(control, list):
            print 'Checking list of controls'
            for c in control:
                if FxxxbxxkBrowser.__control_has__(c,attrs,values):
                    return True
        else:
            #test conditions
            if values is None: #checking if has attr
                if isinstance(attrs,list):
                    for attr in attrs:
                        if not hasattr(control,attr):
                            return False
                    return True
                else:
                    return hasattr(control,attrs)
            else: #comparing values and attrs
                if isinstance(attrs,list) and isinstance(values,list):
                    for attr, value in zip(attrs,values):
                        try:
                            #print "checking ",attr,'is', value
                            if getattr(control,attr) != value:
                                #print attr, 'is ',getattr(control,attr)
                                return False
                        except AttributeError as err:
                            print err
                            return False
                    return True
                else:
                    try:
                        return getattr(control,attrs) == values
                    except AttributeError:
                        return False

    # ACTION FUNCTIONS

    def open(self, site=None):
        """ Opens url. Takes one arguement, 'site' as a string url """
        if site is None:
            site = self.__fb_site__
        try:
            if self.__logged_in__ :
                self.renderer.start_threaded_noise()
            self.__response__ = self.browser.open(site)
            self.browser._factory.is_html = True
            self.__soup__ = BeautifulSoup(self.__response__.read())
        except mechanize.HTTPError as err:
            print err
            print "remmember to use absolute addresses http:://..."
            print "otherwise mechanize searches locally."
        finally:
            if self.__logged_in__ :
                self.renderer.stop_threaded_noise()

    def login(self, email, password):
        #check if needs to login
        print self.browser.title()
        if "Welcome to" in self.browser.title():
            #find form with Log In submit button
            form_id = 0
            found = False
            for form in self.browser.forms():
                self._print_controls(form)
                if self.__control_has__(form.controls,['type','name'],['submit','login']):
                    found = True
                    break
                form_id += 1
            if not found:
                raise Exception('Controls not found')
            #select return formed
            self.browser.select_form(nr=form_id)
            self.set_control('pass',password)
            self.set_control('email',email)
            self.submit()
            #check response.
            if 'Remember Browser' in self.browser.title():
                self.browser.select_form(nr=0)
                self.submit()
            print "successfully logged in"
            self.__logged_in__ = True
        else:
            print "already logged in"
            self.__logged_in__ = True

    def run(self):
        #self.renderer.start()
        if not self.__logged_in__ :
            raise Exception('Not logged in!')
        #needs some sort of decission makeing
        #does it post to time line or trawl over other posts
        while not self.__done__:
            print 'NEW!'
            self.process_news_feed()
            self.major_sleep()
            self.renderer.download_statement()
            self.renderer.sleep(2.0)
    #self.renderer.end()

    def minor_sleep(self):
        self.renderer.sleep(0.3+(random.random()*0.1))

    def major_sleep(self):
        self.renderer.sleep(1.0+(random.random()*4))

    def process_story(self):
        if self.__story__ and not self.__done__:
            while not self.__story__[self.__story_pos__].isspace():
                self.renderer.writewords(self.__story__[self.__story_pos__])
                self.renderer.sleep(0.5)
                self.__story_pos__ += 1
                if self.__story_pos__ == len(self.__story__):
                    self.__story_pos__ = 0
                    self.__done__ = True
                    break
            self.__story_pos__ += 1
            if self.__story_pos__ == len(self.__story__):
                self.__done__ = True


    def process_news_feed(self):
        if self.browser.title() not in ['Facebook', 'News Feed']:
            self.open(self.__fb_site__)
            print "not at news feed so reopened", self.__fb_site__
        self.browser.clear_history()
        posts = self.__get_posts__()
        for post in posts:
            # decide what to do with post
            self.renderer.draw_post(post.content)
            # do i like post
            if post.like_url is not None:
                #print "could like this?"
                if random.random() > 0.5:
                    self.renderer.like()
                    self.renderer.start_threaded_noise()
                    self.browser.open_novisit(post.like_url)
                    self.renderer.stop_threaded_noise()
                    pass
            #else: already like it - do i need to do something?
            if post.comment_count > 0:
                if random.random() > 0.7:
                    self.renderer.writewords('more!')
                    self.__process_comments__(post.comment_url)
            #sleep for some time
            #self.major_sleep()
            self.process_story()
        #then load more stories? or kill the process and post?
        self.see_more_stories()

    def __process_comments__(self, comment_url):
        self.open(comment_url)
        #show full post and interate through comments
        feed = self.__soup__.find('div', id='objects_container')
        post = self.__extract_post__(feed.find(id='u_0_0'))
        #do something with post
        #print "THIS IS THE MAIN POST:"
        self.renderer.draw_post(post.content)

        like_sentence = feed.find(id=re.compile('like_sentence_\d+'))
        if like_sentence is not None:
            like_sentence = self.__extract_post__(like_sentence).content
            self.renderer.draw_post(like_sentence)

        comments = feed.find(id='ufiCommentList')
        #process each child div
        first = True
        for child in comments.children:
            if child['id'].isdigit():
                if first:
                    first = False
                    self.renderer.writewords('comments')
                else:
                    self.renderer.writewords('then')
                c = self.__extract_post__(child)
                self.renderer.comment()
                self.renderer.draw_post(c.content)
                self.minor_sleep()
                # do i like this?
                if random.random() > 0.7:
                    if c.like_url is not None:
                        self.renderer.like()
                        self.renderer.start_threaded_noise()
                        self.browser.open_novisit(c.like_url)
                        self.renderer.stop_threaded_noise()
                    pass
        self.major_sleep()
        self.back()


    #navigate over posts
    def __get_posts__(self):
        feed = self.__soup__.find('div', id='objects_container')#m_newsfeed_stream')
        #print feed.prettify()
        posts = []
        for post in feed.find_all('div'):
            print post
            if post.has_attr('data-dedupekey'):
                posts.append(self.__extract_post__(post))
        return posts



    def __extract_post__(self,post):
        #iterate over children
        post_str = u''
        for child in post.descendants:
            if child.name == 'div' or child.name == 'br':
                post_str += '\n'
            elif child.name == 'img' and hasattr(child,"height") and int(child["height"])>20 :
                post_str += '[ an image ]'
            if not hasattr(child,'contents'):
                if child.parent.name == 'strong' or child.parent.parent.name == 'strong':
                    post_str += u'\033[1m'+child+u'\033[0m'
                else:
                    post_str += child
        like_links = post.find_all('a',text=re.compile("Like"))
        comment_links = post.find_all('a',text=re.compile("Comment"))
        like_link = None
        comment_link = None
        comment_count = 0
        if like_links is not None and len(like_links) > 0:
            like_link = like_links[-1]['href']
        if comment_links is not None and len(comment_links) > 0:
            comment_link = comment_links[-1]['href']
            count = re.match(r'\d+', comment_links[-1].string)
            try:
                comment_count = count.group(0)
            except BaseException as err:
                #print err
                pass

        post_str = [line for line in post_str.splitlines() if len(line.strip()) > 0]
        return FacebookPost(post_str, comment_link, like_link, comment_count)

    #might not need anymore
    def select_form(self, form_id=0):
        try:
            form_id = int(form_id)
        except ValueError:
            form_id = 0
        #print "set form to", form_id
        self.browser.select_form(nr=form_id)

    #convenience method for setting value of control
    def set_control(self, name, value):
        try:
            control = self.browser.form.find_control(name)
            if not control.readonly:
                control.value = value
            #    print 'now',
            #else:
            #    print '[readonly]',
            #print '{0.name}\'s value = {0.value}'.format(control)
        except AttributeError as err:
            print err
        except mechanize.ControlNotFoundError as err:
            print err
            print "Form has these controls:"
            self._print_controls()

    def submit(self, value=None):
        self.renderer.start_threaded_noise()
        if value is None:
            self.__response__ = self.browser.submit()
        else :
            self.__response__ = self.browser.submit(label=value)
        self.renderer.stop_threaded_noise()
        self.browser._factory.is_html = True
        self.__soup__ = BeautifulSoup(self.__response__.read())

    def see_more_stories(self):
        try:
            link = self.browser.find_link(text="See More Stories")
            self.renderer.start_threaded_noise()
            self.__response__ = self.browser.follow_link(link)
        except mechanize.LinkNotFoundError:
            print 'no more stories found'
            self.__response__ = self.browser.open(self.__fb_site__)
        finally:
            self.renderer.stop_threaded_noise()
        self.browser._factory.is_html = True
        self.__soup__ = BeautifulSoup(self.__response__.read())

    def back(self):
        self.renderer.start_threaded_noise()
        self.__response__ = self.browser.back()
        self.renderer.stop_threaded_noise()
        self.browser._factory.is_html = True
        self.__soup__ = BeautifulSoup(self.__response__.read())

    # FOLLOWING FUNCTIONS PRINT INFORMATION ABOUT CURRENT PAGE

    def print_forms(self):
        """ Prints a list of all the forms and controls available on current page. """
        form_number = 0
        for form in self.browser.forms():
            print '\nForm [{0}] = {1:s}'.format(form_number, form.name)
            form_number += 1
            #for property, value in vars(form).iteritems():
            #       print property, ": ", value
            print '\twith controls:'
            self._print_controls(form)

    def _print_controls(self,form=None):
        if form is None and self.browser.form is not None:
            form = self.browser.form
        elif form is  None and self.browser.form is None:
            print 'Cannot print controls - No form selected.'
            return
        control_number = 0
        for control in form.controls:
            print "\t[{0}] name: {1.name} id: {1.id} type: {1.type} readonly: {1.readonly}".format(control_number, control)
            control_number += 1

    def print_links(self):
        """ Prints a list of all the links on the current page. """
        print 'Links:'
        link_number = 0
        for link in self.browser.links():
            print '\t [{0}] {1.text} >> {1.url}'.format(link_number, link)
            link_number += 1

    def print_html(self):
        """ Print out pretty html of current page."""
        if self.__soup__ != None:
            print self.__soup__.prettify()

    def print_page(self, tags=None):
        """ Prints the string contents of specific tags in order of appearance.
            Takes one arguement 'tags' as comma seporated string eg. h1,div,b...
        """
        if tags is None:
            tags = ['p', 'div', 'a', 'b','i','h1', 'h2', 'h3', 'h4','h5']
            print "printing default tags", tags
        elif isinstance(tags, basestring):
            tags = tags.split(',')
        if self.__soup__ != None:
            tags = self.__soup__.find_all(tags)
            for item in tags:
                if item.string != None:
                    print item.name, ':', item.string
        else:
            print "No response data available. Open new page."