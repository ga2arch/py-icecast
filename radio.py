import urllib2
import gevent
from gevent.server import StreamServer
import mutagen.id3
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

radios_recording = dict()

class Cmds:
    def __init__(self, fileobj):
        self.fileobj = fileobj
    
    def call(self, cmd, args):
        getattr(self, cmd)(args)
    
    def write(self, data):
        self.fileobj.write(data)
        self.fileobj.flush()
        
    def startrecord(self, args):
        '''
        startrecord <pls_url> <folder>
        '''
        
        pls_url, folder = args.split(' ')
        resp = urllib2.urlopen(pls_url)
        g = Radio(resp, folder, True).start()
        radios_recording[pls_url] = g
        self.write('Recording ....\n')
        
    def stoprecord(self, args):
        '''
        stoprecord <pls_url>
        '''
        
        if pls_url in radios_recording: 
            radios_recording[pls_url].kill()
            del radios_recording[pls_url]
            self.write('Stopped !')
     
    def current(self, args):
         '''
         currentsong <pls_url>
         '''
         self.write(radios_recording[pls_url].current_song_name)
         
     
        
def parse_cmd(line, socket):
    Cmd(cmd, args, socket)
    
def cmd_handler(socket, address):
    fileobj = socket.makefile()
    fileobj.write('OK PYRR 0.1\n')
    fileobj.flush()
    cmds = Cmds(fileobj)
    
    while True:
        line = fileobj.readline()
        cmd, args = line.split(' ', 1)
        cmds.call(cmd, args)
    

class Radio(gevent.Greenlet):
    def __init__(self, pls, folder, save, username=None, password=None):
        gevent.Greenlet.__init__(self)
        self.pls = pls
        self.folder = folder
        self.save = save
        self.username = username
        self.password = password
        self.handler = None
    
    def write(self, data):
        self.fileobj.write(data)
        self.fileobj.flush()
    
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
        

class ID3Handler:
    def __init__(self, filename, name, genre):
        self.write_id3tag(filename, name, genre)
        
    def parse_name(self, name):
        title = name
        author = ''

        if '-' in name:
            author, title = name.split(' - ')
        if 'by' in name:
            title, author = name.split(' by ')

        return (title, author)

    def write_id3tag(self, filename, name, genre):
        title, author = parse_name(name)
        mp3 = MP3(filename)
        mp3.add_tags(ID3=EasyID3)
        mp3['title'] = title
        mp3['artist'] = author
        mp3['genre'] = genre
        mp3.save()

if __name__ == '__main__':
    server = StreamServer(('0.0.0.0', 6000), cmd_handler)
    print 'Starting server on port 6000'
    server.serve_forever()   