import mutagen.id3
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

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