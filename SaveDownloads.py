try:
    import cPickle as pickle
except ImportError:
    import pickle
from typing import Set
from Settings import Settings
import os

class SaveDownloadToFile: 
    def __init__(self, settings: Settings):
        self.animes = {}
        self.database_path = settings.get_setting('downloadsDatabaseLocation')
        self.total_number_of_animes_downloaded = 0

        if (os.path.exists(self.database_path)):
            with open(self.database_path, 'rb') as file: 
                self.animes = pickle.load(file)
                self.total_number_of_animes_downloaded = len(self.animes)
                print('Downloads Loaded.', end='\n\n')
            
    def add_new_anime_to_database(self, anime_url): 
        isIn = False
        self.total_number_of_animes_downloaded = len(self.animes)
        for x in self.return_show_url():
            if anime_url == x:
                isIn = True
        if isIn:
            pass
        else:
            self.animes['anime{0}'.format(str(self.total_number_of_animes_downloaded+1))] = anime_url
            self.save_database()
        
    def save_database(self):
        with open(self.database_path, 'wb') as file:
            pickle.dump(self.animes, file, protocol=pickle.HIGHEST_PROTOCOL)
            
    def show_all_url(self):
        for x in range(self.total_number_of_animes_downloaded):
            if ('/anime/' in str(self.animes['anime{0}'.format(str(x+1))])):
                print('Show url: {0}'.format(str(self.animes['anime{0}'.format(str(x+1))])), 'Show name: {0}'.format(str(self.animes['anime{0}'.format(str(x+1))]).rsplit('/', 1)[-1].replace('-', ' ').title()))
            else:
                print('Episode url: {0}'.format(str(self.animes['anime{0}'.format(str(x+1))])), 'Episode name: {0}'.format(str(self.animes['anime{0}'.format(str(x+1))]).rsplit('/', 1)[-1].replace('-', ' ').title()))
    
    def return_show_url(self):
        for x in range(self.total_number_of_animes_downloaded):
            if ("/anime/" in str(self.animes['anime{0}'.format(str(x+1))])):
                yield str(self.animes['anime{0}'.format(str(x+1))])



