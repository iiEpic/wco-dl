#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import requests
import base64
import urllib3
from bs4 import BeautifulSoup
from Downloader import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Lifter(object):

    def __init__(self, url, resolution, logger, ep_range, output):
        # Define our variables
        self.url = url
        self.resolution = resolution
        self.logger = logger
        self.ep_range = ep_range

        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 ' \
                          '(KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        self.header = {
            'User-Agent': self.user_agent, 'Accept': '*/*', 'Referer': url, 'X-Requested-With': 'XMLHttpRequest'
        }
        self.base_url = "https://wcostream.com"
        self.path = os.path.dirname(os.path.realpath(__file__))

        def find_download_link():
            page = requests.get(self.url)
            soup = BeautifulSoup(page.text, 'html.parser')

            self.script_url = soup.find("meta", {"itemprop": "embedURL"}).next_element.next_element.text
            self.letters = self.script_url[self.script_url.find("[") + 1:self.script_url.find("]")]
            self.ending_number = int(re.search(' - ([0-9]+)', self.script_url).group(1))
            self.hidden_url = self._decode(self.letters.split(', '), self.ending_number)
            return self.get_download_url(self.hidden_url)[0]

        # Check if the URL is valid
        valid_link, extra = self.is_valid()
        if valid_link:
            # Check to see if we are downloading a single episode or multiple
            if extra[0] == "anime":
                # We are downloading multiple episodes
                print("downloading show")
            else:
                # We are downloading a single episode
                print('downloading single')
                self.download_url = find_download_link()
                self.show_info = self.info_extractor(extra)
                if output is not None:
                    self.output = output
                else:
                    self.output = self.path_creator(self.show_info[0])
                Downloader(download_url=self.download_url, output=self.output, header=self.header,
                           show_info=self.show_info)
        else:
            # Not a valid wcostream link
            print(extra)
            exit()

    @staticmethod
    def path_creator(anime_name):
        output_directory = os.path.abspath("Output" + os.sep + str(anime_name) + "/")
        if not os.path.exists("Output"):
            os.makedirs("Output")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        return output_directory

    def request_c(self, url, extraHeaders=None):
        myheaders = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }
        if extraHeaders:
            myheaders.update(extraHeaders)

        cookie = None
        response = requests.get(url, headers=myheaders, verify=False, cookies=cookie, timeout=10)

        return response

    def _decode(self, array, ending):
        iframe = ''
        for item in array:
            decoded = base64.b64decode(item).decode('utf8')
            numbers = re.sub('[^0-9]+', '', decoded)
            # print(chr(int(numbers) - ending))
            iframe += chr(int(numbers) - ending)
        html = BeautifulSoup(iframe, 'html.parser')
        return self.base_url + html.find("iframe")['src']

    def download_single(self):
        pass

    def download_show(self):
        pass

    @staticmethod
    def info_extractor(url):
        try:
            if "season" in url:
                show_name, season, episode, desc = re.findall(r'([a-zA-Z0-9].+)\s(season\s\d+\s?)(episode\s\d+\s)?(.+)',
                                                              url.replace('-', ' '))[0]
            else:
                show_name, episode, desc = re.findall(r'([a-zA-Z0-9].+)\s(episode\s\d+\s?)(.+)', url.replace(
                    '-', ' '))[0]
                season = "season 1"
        except:
            show_name = url
            season = "season 1"
            episode = "episode 0"
            desc = ""
        return show_name.title().strip(), season.title().strip(), episode.title().strip(), desc.title().strip()

    def is_valid(self):
        website = re.findall('https://(www.)?wcostream.com/(anime)?/?([a-zA-Z].+$)?', self.url)
        if website:
            if website[0][1] == "anime":
                return True, (website[0][1], website[0][2])
            return True, website[0][2]
        return False, '[wco-dl] Not correct wcostream website.'

    def get_download_url(self, embed_url):
        page = self.request_c(embed_url)
        html = page.text

        # Find the stream URLs.
        if 'getvid?evid' in html:
            # Query-style stream getting.
            source_url = re.search(r'get\("(.*?)"', html, re.DOTALL).group(1)

            page2 = self.request_c(
                self.base_url + source_url,
                extraHeaders={
                    'User-Agent': self.user_agent, 'Accept': '*/*', 'Referer': embed_url,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            if not page2.ok:
                raise Exception('Sources XMLHttpRequest request failed')
            json_data = page2.json()

            # Only two qualities are ever available: 480p ("SD") and 720p ("HD").
            source_urls = []
            sd_token = json_data.get('enc', '')
            hd_token = json_data.get('hd', '')
            source_base_url = json_data.get('server', '') + '/getvid?evid='
            if sd_token:
                source_urls.append(('480 (SD)', source_base_url + sd_token))  # Order the items as (LABEL, URL).
            if hd_token:
                source_urls.append(('720 (HD)', source_base_url + hd_token))
            # Use the same backup stream method as the source: cdn domain + SD stream.
            backup_url = json_data.get('cdn', '') + '/getvid?evid=' + (sd_token or hd_token)
        else:
            # Alternative video player page, with plain stream links in the JWPlayer javascript.
            sources_block = re.search(r'sources:\s*?\[(.*?)\]', html, re.DOTALL).group(1)
            stream_pattern = re.compile(r'\{\s*?file:\s*?"(.*?)"(?:,\s*?label:\s*?"(.*?)")?')
            source_urls = [
                # Order the items as (LABEL (or empty string), URL).
                (sourceMatch.group(2), sourceMatch.group(1))
                for sourceMatch in stream_pattern.finditer(sources_block)
            ]
            # Use the backup link in the 'onError' handler of the 'jw' player.
            backup_match = stream_pattern.search(html[html.find(b'jw.onError'):])
            backup_url = backup_match.group(1) if backup_match else ''
        # print("debug:", backupURL)
        # print("debug:", sourceURLs)

        return source_urls[0][1], backup_url
