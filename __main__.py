#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import platform
import requests
from Lifter import *
from version import __version__
from Settings import Settings
from SaveDownloads import SaveDownloadToFile

class Main:
    if __name__ == '__main__':
        # Run the settings script
        settings = Settings()
        database = SaveDownloadToFile(settings)
        
        if settings.get_setting('checkForUpdates'):
            r = requests.get('https://raw.githubusercontent.com/EpicUnknown/wco-dl/master/version.py').text.replace('_version__ = ', '').replace("'", '')
            if (__version__ != r):
                print('Newer version available, on https://github.com/EpicUnknown/wco-dl', end='\n\n')

        parser = argparse.ArgumentParser(description='wco-dl downloads shows from wcostream.com')

        parser.add_argument('--version', action='store_true', help='Shows version and exits.')

        required_args = parser.add_argument_group('Required Arguments :')
        required_args.add_argument('-i', '--input', nargs=1, help='Inputs the URL to show.')
        parser.add_argument('-hd', '--highdef', help='If you wish to get 720p', action="store_true")
        parser.add_argument('-epr', '--episoderange', nargs=1, help='Specifies the range of episodes to download.',
                            default='All')
        parser.add_argument('-se', '--season', nargs=1, help='Specifies the season to download.',
                            default='All')
        parser.add_argument('-x', '--exclude', nargs=1, help='Specifies the episodes to not download (ie ova).',
                            default=None)
        parser.add_argument('-o', '--output', nargs=1, help='Specifies the directory of which to save the files.')
        parser.add_argument("-v", "--verbose", help="Prints important debugging messages on screen.",
                            action="store_true")
        parser.add_argument('-n', '--newest', help='Get the newest episode in the series.', action='store_true')
        parser.add_argument('-sh', '--show_downloaded_animes', help='This will show all downloaded shows and episodes', action='store_true')
        parser.add_argument('-us', '--update_shows', help='This will update all shows in your database that have new episodes.', action='store_true')
        parser.add_argument('-b', '--batch', help='Batch download, download multiple anime.', nargs=1)
        parser.add_argument('-t', '--threads', help='This will create multiple threads, in other words download multiple episodes at ones.', nargs=1, default=None)
        parser.add_argument("-q", "--quiet", help="Will not show download progress",
                            action="store_true")
        logger = "False"
        quiet = 'False'
        
        args = parser.parse_args()

        if args.quite:
            quite = 'True'

        if args.batch:
            if type(args.threads) == list:
                args.threads = args.threads[0]
            with open(args.batch[0], 'r') as anime_list:
                for anime in anime_list:
                    print(anime.replace('\n', ''))
                    Lifter(url=anime.replace('\n', '').replace('https://wcostream.com', 'https://www.wcostream.com'), resolution=args.highdef, logger=logger, season=args.season,
                    ep_range=args.episoderange, exclude=args.exclude, output=args.output, newest=args.newest,
                    settings=settings, database=database, threads=args.threads, quiet=quiet)
            print('Done')
            exit()

        if args.update_shows: 
            print("Updating all shows, this will take a while.")
            for x in database.return_show_url():
                Lifter(url=x, resolution=args.highdef, logger=logger, season=args.season,
                ep_range=args.episoderange, exclude=args.exclude, output=args.output, newest=args.newest,
                settings=settings, database=database, update=True, quiet=quiet)
            print('Done')
            exit()

        if args.show_downloaded_animes: 
            database.show_all_url()
            exit()

        if args.verbose:
            logging.basicConfig(format='%(levelname)s: %(message)s', filename="Error Log.log", level=logging.DEBUG)
            logging.debug('You have successfully set the Debugging On.')
            logging.debug("Arguments Provided : {0}".format(args))
            logging.debug(
                "Operating System : {0} - {1} - {2}".format(platform.system(), platform.release(), platform.version()))
            logging.debug("Python Version : {0} ({1})".format(platform.python_version(), platform.architecture()[0]))
            logger = "True"

        if args.version:
            print("Current Version : {0}".format(__version__))
            exit()

        if args.highdef:
            args.highdef = '720'
        else:
            args.highdef = '480'
        
        if args.input is None:
            print("Please enter the required argument. Run __main__.py --help")
            exit()
        else:
            if type(args.episoderange) == list:
                if '-' in args.episoderange[0]:
                    args.episoderange = args.episoderange[0].split('-')
                else:
                    args.episoderange = args.episoderange[0]
            if type(args.season) == list:
                args.season = args.season[0]
            if type(args.output) == list:
                args.output = args.output[0]
            if type(args.exclude) == list:
                if ',' in args.exclude[0]:
                    args.exclude = args.exclude[0].split(',')
                else:
                    args.exclude = args.exclude[0]
            if type(args.threads) ==list:
                args.threads = args.threads[0]

            Lifter(url=args.input[0].replace('https://wcostream.com', 'https://www.wcostream.com'), resolution=args.highdef, logger=logger, season=args.season,
                   ep_range=args.episoderange, exclude=args.exclude, output=args.output, newest=args.newest,
                   settings=settings, database=database, threads=args.threads, quiet=quiet)
