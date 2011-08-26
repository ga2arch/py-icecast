import urllib2


class Radio:
    def __init__(self, pls, folder, save):
        Greenlet.__init__(self)
        self.pls = pls
        self.folder = folder
        self.save = save
        self.handler = None
    
    def __parse_pls(self):
        lines = self.pls.readlines()
        self.servers = [line.split('=')[1].rstrip() for line in lines if line[0:4] == 'File']
        
    def __init_stream(self, i=0):
        if i > len(self.servers): raise Exception('No valid server found')
        stream_url = self.servers[i]
        headers = {'Icy-MetaData':1}
        req = urllib2.Request(stream_url, None, headers)
        try:
            self.stream = urllib2.urlopen(req)
        except Exception:
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
        return title
        
    def _run(self):
        self.__parse_pls()
        self.__init_stream()
        self.__parse_header()
        
        f = None
        
        while True:
            data = self.stream.read(int(self.header['metaint']))
            if f: f.write(data)
            
            length = ord(self.stream.read(1)) * 16
            if length == 0: continue
            if f: f.close()
            if f and self.handler: 
                try:
                    self.handler(filename, name, self.header['genre'])
                except Exception:
                    pass
                    
            self.current_song_name = self.__parse_metadata(self.stream.read(length))
            self.current_song_name.replace('/', '\/')
            
            filename = self.folder+self.current_song_name+'.mp3'
            if self.save: f = open(filename, 'ab')
            
            
    def set_id3tag_handler(self, handler):
        self.handler = handler

if __name__ == '__main__':
    pass