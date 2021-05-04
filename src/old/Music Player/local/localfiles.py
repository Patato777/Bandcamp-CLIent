import os,re,mimetypes

class Track :
    def __init__(self,path) :
        self.file = path
        self.name = os.path.basename(self.file)
        #print(re.search(r'.*(?=\.)',self.name).group(),re.search(r'(?<=\.)\w+',self.name).group())
        self.title,self.ext = re.search(r'.*(?=\.)',self.name).group(),re.search(r'(?<=\.)\w+',self.name).group()
        self.artist,self.album = os.path.dirname(self.file).split(os.path.sep)[-2:]
        self.info = {'title':self.title,'artist':self.artist,'album':self.album,'file':self.file}

class Album :
    def __init__(self,path) :
        self.path = path
        self.title = os.path.basename(self.path)
        self.artist = os.path.basename(os.path.dirname(self.path))
        self.info = {'title':self.title,'artist':self.artist}
        self.tracks = [Track(os.path.join(self.path,t)) for t in os.listdir(self.path) if mimetypes.guess_type(t)[0].split('/')[0]=='audio']

class Artist :
    def __init__(self,path) :
        self.path = path
        self.name = os.path.basename(self.path)
        self.albums = [Album(os.path.join(self.path,a)) for a in os.listdir(self.path) if os.path.isdir(os.path.join(self.path,a))]
