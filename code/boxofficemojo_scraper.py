from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import dateutil.parser as parser
import string

headers = {'User-Agent':
           'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
           'AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/39.0.2171.95 Safari/537.36'}
# -- get data from one movie
# resp = requests.get('http://www.the-numbers.com/movie/71-(2014)#tab=summary',
#                     headers=headers)

# resp = requests.get('http://www.boxofficemojo.com/')


# -- get all movie data
def all_movie_data(list_letter=['num'] + list(string.lowercase[0:26]),
                   page_limit=99):
    links = get_movie_links(list_letter=list_letter, page_limit=page_limit)
    print 'got links of', list_letter, ', ', len(links), 'movies in total'
    list_ds = []
    for l in links:
        m = MovieInfo(l)
        list_ds.append(m.ds)
    return pd.DataFrame(list_ds)


def get_movie_links(list_letter=['num'] + list(string.lowercase[0:26]),
                    page_limit=99):
    """ collect movie links from boxofficemojo.com
        args: list_letter = ['a', 'b', 'c', ..., 'num'], if not supplied,
              all movie links will be returned
        returns: links
    """
    links = []
    for letter in list_letter:
        page = 1
        links_old = None
        while True:
            if page > page_limit:
                break
            url = ('http://www.boxofficemojo.com/movies/alphabetical.htm?'
                   'letter={}&page={}&p=.htm'.format(letter, page))
            print "processing {}".format(url)
            r = requests.get(url)
            if r.status_code != 200:
                print 'status_code:', r.status_code
                print r.content
                raise Exception('connection to {} failed'.format(url))

            soup = BeautifulSoup(r.content)
            tables = soup.find_all('table')
            if len(tables) < 5:
                break
            movie_table = tables[3]
            movies = movie_table.find_all('a', href=re.compile('/movies/'))
            if not movies:
                break
            links_new = [m.attrs['href'] for m in movies]
            if links_new == links_old:
                break
            links.extend(links_new)
            links_old = links_new
            page += 1
    return links


# -- process individual movie webpage to return related information

class MovieInfo(object):
    def __init__(self, link):
        url_dom = 'http://www.boxofficemojo.com'
        if re.search(url_dom, link):
            self.link = link
        else:
            self.link = url_dom + link

        self.content = None
        self.dic = {}
        self.soup = None
        self.ds = pd.Series()

        # -- initial process
        self.get_soup()
        if self.soup:
            self.process_all_gets()
        else:
            print '{} did not return contents'.format(self.link)

    def process_all_gets(self):
        self.dic_assign_funct = {
            'Domestic:': self._money_to_int,
            'Foreign:': self._money_to_int,
            'Release Date': self._txt_to_date,
            'Close': self._txt_to_date,
            'In Release': lambda x: x,
            'Budget': lambda x: x,
            'Runtime': lambda x: x,
            'Distributor': lambda x: x,
            'MPAA': lambda x: x,
            'Widest': lambda x: x,
            'Genre:': lambda x: x,
        }
        self.dic['abslink'] = self.link
        self.get_movie_title()
        for k in self.dic_assign_funct.iterkeys():
            self.processDic(k)

        # convert to data series
        self.ds = pd.Series(self.dic)

    def get_soup(self):
        resp = requests.get(self.link)
        if resp.status_code == 200:
            self.content = resp.content
        if self.content:
            self.soup = BeautifulSoup(self.content)
        return self.soup

    def adjust(self):
        """ apply ajust value """
        pass

    def get_movie_title(self):
        title = self.soup.find('title').text
        self.dic['Title'] = title.split('(')[0].strip()

    def _get_movie_value(self, movie_key, proc_funct=lambda x: x):
        sib_txt = self._get_sib_text(movie_key)
        if sib_txt:
            return proc_funct(sib_txt)

    def _money_to_int(self, txt):
        try:
            return int(txt.replace('$', '').replace(',', ''))
        except ValueError:
            return txt

    def _txt_to_date(self, txt):
        try:
            return parser.parse(txt.strip())
        except ValueError:
            return txt

    def processDic(self, movie_key):
        self.dic[movie_key] = self._get_movie_value(
                                    movie_key,
                                    self.dic_assign_funct[movie_key])

    def _get_sib_text(self, movie_key):
        ptrn = re.compile(movie_key)
        obj = self.soup.find(text=ptrn)
        if obj:
            try:
                return obj.findNextSibling().text
            except AttributeError:  # NonType has no attr text
                try:
                    return self._get_uncle_text(movie_key, obj=obj)
                except AttributeError:  # NonType has no attr text
                    try:
                        return self._get_grand_uncle_text(movie_key, obj=obj)
                    except AttributeError:
                        return None

    def _get_grand_uncle_text(self, movie_key, obj=None):
        if not obj:
            ptrn = re.compile(movie_key)
            obj = self.soup.find(text=ptrn)
        if obj:
            return obj.findParent().findParent().findNextSibling().text

    def _get_uncle_text(self, movie_key, obj=None):
        if not obj:
            ptrn = re.compile(movie_key)
            obj = self.soup.find(text=ptrn)
        if obj:
            return obj.findParent().findNextSibling().text


link = 'http://www.boxofficemojo.com/movies/?id=ateam.htm'
