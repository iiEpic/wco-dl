#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from cfscrape import create_scraper
from requests import session
from tqdm import tqdm


class Downloader(object):
    def __init__(self, download_url, output, header, show_info):
        sess = session()
        sess = create_scraper(sess)

        self.show_name = show_info[0]
        self.season = show_info[1]
        if show_info[2] == "":
            self.episode = show_info[3]
        else:
            self.episode = show_info[2]
        self.desc = show_info[3]
        self.header = header
        self.output = output

        self.file_name = "{0}-{1}-{2}".format(self.show_name, self.season, self.episode)
        self.file_path = self.output + os.sep + "{0}.mp4".format(self.file_name)

        print('[wco-dl] - Downloading {0}'.format(self.file_name))
        while True:
            dlr = sess.get(download_url, stream=True, headers=self.header)  # Downloading the content using python.
            with open(self.file_path, "wb") as handle:
                for data in tqdm(dlr.iter_content(chunk_size=1024)):  # Added chunk size to speed up the downloads
                    handle.write(data)

            if os.path.getsize(self.file_path) == 0:
                print("[wco-dl] Download for {0} did not complete, please try again.\n".format(self.file_name))
                break
            else:
                print("[wco-dl] Download for {0} completed.\n".format(self.file_name))
                break
