#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from cfscrape import create_scraper
from requests import session
from tqdm import tqdm


class Downloader(object):
    def __init__(self, download_url, output, header, show_info):
        sess = session()
        sess = create_scraper(sess)

        self.show_name = show_info[0]
        self.season = re.search(r'(\d+)', show_info[1]).group(1)
        if show_info[2] == "":
            self.episode = '{0}'.format(re.search(r'(\d+)', show_info[3]).group(1).zfill(2))
        else:
            self.episode = '{0}'.format(re.search(r'(\d+)', show_info[2]).group(1).zfill(2))
        self.desc = show_info[3]
        self.header = header
        self.output = output

        self.file_name = "{0}-S{1}E{2}-{3}".format(self.show_name, self.season, self.episode, self.desc)
        self.file_path = self.output + os.sep + "{0}.mp4".format(self.file_name)

        print('[wco-dl] - Downloading {0}'.format(self.file_name))
        while True:
            dlr = sess.get(download_url, stream=True, headers=self.header)  # Downloading the content using python.
            with open(self.file_path, "wb") as handle:
                for data in tqdm(dlr.iter_content(chunk_size=1024)):  # Added chunk size to speed up the downloads
                    handle.write(data)

            if os.path.getsize(self.file_path) == 0:
                print("[wco-dl] - Download for {0} did not complete, please try again.\n".format(self.file_name))
                # Upon failure of download append the episode name, file_name, to a text file in the same directory
                # After finishing download all the shows the program will see if that text file exists and attempt
                # to re-download the missing files
                break
            else:
                print("[wco-dl] - Download for {0} completed.\n".format(self.file_name))
                break
