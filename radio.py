import urllib2

class Radio:
    def __init__(self, pls, folder, save):
        self.pls = pls
        self.folder = folder
        self.save = save
        self.metadata_handler = None
        self.title_handler = None
        self.current_song = None
    
    def __parse_pls(self):
        pls = open(self.pls, 'r')
        lines = pls.readlines()
        if not lines: raise Exception('Empty pls')
        self.servers = [line.split('=')[1].rstrip() for line in lines if line[0:4] == 'File']
        
    def __init_stream(self, i=0):
        if i == len(self.servers): raise Exception('No valid server or no connectivity')
        stream_url = self.servers[i]
        headers = {'Icy-MetaData':1}
        req = urllib2.Request(stream_url, None, headers)
        try:
            self.stream = urllib2.urlopen(req)
        except urllib2.URLError:
            self.__init_stream(i+1)
            
    def __parse_header(self):
        self.header = dict()
        line = self.stream.readline()
        while True:
            line = self.stream.readline()
            if line == '\r\n': break;
            if 'content-type' in line: 
                key = 'content-type'
                value = line.split('content-type:')[1].split('\n')[0].strip()
            else:
                key = line.split('icy-')[1].split(':')[0]
                value = line.split('icy-'+key+':')[1].split('\n')[0].strip()
            self.header[key] = value
        
    def __parse_metadata(self, data):
        title = data.split('StreamTitle=\'')[1].split('\';')[0]
        return title.replace('/', '\/')
        
    def read_stream(self):
        self.__parse_pls()
        self.__init_stream()
        self.__parse_header()
        
        f = None
        
        while True:
            try:
                data = self.stream.read(int(self.header['metaint']))
                if f: f.write(data)
            
                length = ord(self.stream.read(1)) * 16
                if length == 0: continue
                if f: f.close()
                if f and self.metadata_handler: 
                    self.metadata_handler(filename, name, self.header['genre'])
                    
                self.current_song = self.__parse_metadata(self.stream.read(length))
                
                if self.title_handler: self.title_handler(self.current_song)
                
                filename = self.folder+self.current_song+'.mp3'
                if self.save: f = open(filename, 'ab')
            except Exception:
                self.read_stream()
            
    def set_metadata_handler(self, handler):
        self.metadata_handler = handler
    
    def set_title_handler(self, handler):
        self.title_handler = handler


if __name__ == '__main__':
    
    def print_title(title):
        print title
    
    r = Radio('listen.pls', '', False)
    r.set_title_handler(print_title)
    r.read_stream()