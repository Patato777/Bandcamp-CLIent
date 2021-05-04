import requests,demjson,re,bcdownload
from bs4 import BeautifulSoup

#requests.get, but with raise_for_status.
def getpage(url,params=None) :
        req = requests.get(url,params = params)
        req.raise_for_status()
        return req

#The class of bandcamp artists and labels
class Artist :
    def __init__(self,url) :
        self.url = url + '/music' #To get directly to the discography page, may fail if there is not any
        self.baseurl = url 
        self.getinfo() #Scrap the page

    def getinfo(self) :
        self.page = getpage(self.url)
        self.soup = BeautifulSoup(self.page.text,'lxml')
        #print(self.url)#debug
        self.name = self.soup.select_one('p#band-name-location span.title').text
        if self.soup.find(property="og:type")['content'] == 'band' :
                albumslist = self.soup.select_one('ol.music-grid')('a') #Get the list of published albums on the page
                self.albums = [{'title':alb.text.strip(),'URL':self.baseurl+alb.attrs['href']} for alb in albumslist]#Often fail for labels since most artists have their own page
        
    #Create Album objects from the list of the discography page
    def getalbum(self,index) : 
        return Album(self.albums[index]['URL'])

#The class of things that can be played
class Playable :
    def getinfo (self) :
        self.page = getpage(self.url)
        self.soup = BeautifulSoup(self.page.text,'lxml')
        #Here are the informations on the album/track, including mp3 files
        self.infoscript = self.soup.find(type='text/javascript',string=re.compile('data-tralbum')).string
        #More precisely in the TralbumData var
        regex = re.compile(r"(?<=data-tralbum=\s).*?}(?=;)",re.DOTALL)
        jsdic = regex.search(self.infoscript).group().replace('" + "', '')
        self.info = demjson.decode(jsdic)
        #The data on the band is the BandData one, I just need its name and URL
        bandinfo = re.search(r'(?<=data-band).*?}',self.infoscript,re.DOTALL).group()
        bandregex = re.compile(r'(?<=name:\s").*?(?=",)',re.DOTALL)
        name = bandregex.search(bandinfo).group()
        self.band = {'name' : name,'url' : re.search(r'.*?\.com',self.url).group()}

    #Create an Artist object from the URL
    def getband(self) :
        self.band = Artist(self.band['url'])

#The class of albums
class Album (Playable):
    def __init__(self,info) :
        self.url = info
        self.getinfo()#Scrap the page
        self.bcinfo = self.info
        self.info = self.bcinfo['current']#In fact I only need what is in "current"
        self.gettracks()#Create Track objects from the info in TralbumData

    #Create Track objects from the data in trackinfo
    def gettracks(self) :
        #The url isn't directly written, it has to be built from the base URL and the track one
        for info in self.bcinfo['trackinfo'] :
            info.update({'url':self.band['url']+info['title_link']})
        self.tracks = [Track(info,self) for info in self.bcinfo['trackinfo']]

    #To download the album
    def download(self) :
        if self.info['minimum_price'] == 0 :
            if self.info["freeDownloadPage"] :
                bcdownload.free_download(self.info["freeDownloadPage"],'mp3-320')
            else :
                bcdownload.mail_download(self)
        else :
            bcdownload.albzulu(self)

#The class of tracks 
class Track (Playable) :
    def __init__(self,info,album) :
        self.info = info
        self.album = album

    #Create an Album object from the URL
    def getalbum(self) :
        self.album = Album(self.album['url'])

    def download(self) :
        bcdownload.trzulu(self)

#The class to search on bandcamp
class Search :
    def __init__(self,search) :
        self.search = search
        self.url = 'https://bandcamp.com/search'
        self.getresults()

    def getresults(self) :
        self.page = getpage(self.url,{'q':self.search})
        soup = BeautifulSoup(self.page.text,'lxml')
        results = soup.find('ul',class_='result-items')('li')
        #List of results : their type, name and URL
        self.results = [{'type':res(class_='itemtype')[0].string.strip(),\
                             'name':res(class_='heading')[0].a.string.strip(),\
                             'url':res(class_='itemurl')[0].a.string.strip()}\
                            for res in results]

#The class of bandcamp normal users
class Fan :
    def __init__(self,username) :
        self.url = f'https://bandcamp.com/{username}'
        self.getinfo()

    def getinfo(self) :
        self.page = getpage(self.url)
        self.soup = BeautifulSoup(self.page.text,'lxml')
        #All information is in the first div of the body
        self.datadic = demjson.decode(self.soup.body.div.attrs['data-blob'])
        self.name,self.username = self.datadic['fan_data']['name'],self.datadic['fan_data']['username']
        self.info = self.datadic['item_cache']
        #Information is listed in dictionnaries with arbitrary keys... Turns them into lists of values
        for key in self.info :
            self.info[key] = list(self.info[key].values())
        #Bands URL aren't fully written, they have to be built
        for band in self.info['following_bands'] :
            band['url'] = 'http://'+band['url_hints']['subdomain']+'.bandcamp.com'
        self.albums = [item for item in self.info['collection']]

    #Create Album objects from the URLs
    def getalbums(self) :
        self.albums = [self.getalbum(k) for k in range(len(self.albums))]

    def getalbum(self,index) :
        return Album(self.albums[index]['item_url'])

    #Create Band objects from the URLs
    def getbands(self) :
        self.bands = [self.getband(k) for k in range(len(self.info['following_bands']))]
        
    def getband(self,index) :
        return Artist(self.info['following_bands'][index]['url'])
