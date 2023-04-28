#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from platform import mac_ver, machine
import re
import sys
import requests
import base64
import urllib3
from bs4 import BeautifulSoup
from Downloader import *
from Process import ProcessParallel

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# TODO: Make it track missed episodes and retry when done

class Lifter(object):

    def __init__(self, url, resolution, logger, season, ep_range, exclude, output, newest, settings, database, quiet,update=False, threads=None):
        # Define our variables
        self.url = url
        self.resolution = resolution
        self.logger = logger
        self.season = season
        self.ep_range = ep_range
        self.exclude = exclude
        self.newest = newest
        self.settings = settings
        self.database = database
        self.update = update
        self.threads = threads
        self.original_thread = self.threads
        self.quiet = quiet
        
        if output is None:
            self.output = ""
        else:
            if output == ".":
                self.output = os.getcwd()
            else:
                self.output = output

        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 ' \
                          '(KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        self.header = {
            'User-Agent': self.user_agent, 'Accept': '*/*', 'Referer': url, 'X-Requested-With': 'XMLHttpRequest'
        }
        self.base_url = "https://wcostream.net"
        self.path = os.path.dirname(os.path.realpath(__file__))

        # Check if the URL is valid
        valid_link, extra = self.is_valid(self.url)

        if valid_link:
            # Check to see if we are downloading a single episode or multiple
            self.database.add_new_anime_to_database(self.url)
            if extra[0] == "anime/":
                # We are downloading multiple episodes
                print("Downloading show")
                self.download_show(url)
            else:
                # We are downloading a single episode
                print('Downloading single')
                self.download_single(url, extra)
        else:
            # Not a valid wcostream link
            print(extra)
            sys.exit()

    def check_output(self, anime_name):
        output_directory = os.path.abspath("Output" + os.sep + str(anime_name) + os.sep)
        if self.output != "":
            output_directory = self.output.translate(str.maketrans({'\\': os.sep, '/': os.sep}))
        if not os.path.exists(self.output):
            if not os.path.exists("Output"):
                os.makedirs("Output")
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
        else:
            output_directory = self.output.translate(str.maketrans({'\\': os.sep, '/': os.sep}))
        return output_directory

    def request_c(self, url, extraHeaders=None):
        myheaders = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,image/webp,*""" /*;q=0.8',
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

    def find_download_link(self, url):
        page = self.request_c(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        script_url = repr(soup.find("meta", {"itemprop": "embedURL"}).next_element.next_element)
        letters = script_url[script_url.find("[") + 1:script_url.find("]")]
        ending_number = int(re.search(' - ([0-9]+)', script_url).group(1))
        hidden_url = self._decode(letters.split(', '), ending_number)
        return self.get_download_url(hidden_url)

    def find_hidden_url(self, url): 
        page = self.request_c(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        script_url = repr(soup.find("meta", {"itemprop": "embedURL"}).next_element.next_element)
        letters = script_url[script_url.find("[") + 1:script_url.find("]")]
        ending_number = int(re.search(' - ([0-9]+)', script_url).group(1))
        hidden_url = self._decode(letters.split(', '), ending_number)
        return hidden_url

    def _decode(self, array, ending):
        iframe = ''
        for item in array:
            decoded = base64.b64decode(item).decode('utf8')
            numbers = re.sub('[^0-9]+', '', decoded)
            # print(chr(int(numbers) - ending))
            iframe += chr(int(numbers) - ending)
        html = BeautifulSoup(iframe, 'html.parser')
        return html.find("iframe")['src']

    def download_single(self, url, extra):
        download_url, source_url = self.find_download_link(url)
        hidden_url = self.find_hidden_url(url)
        if self.resolution == '480':
            download_url = download_url[0][1]
        else:
            try:
                download_url = source_url[1][1]
            except Exception:
                download_url = download_url[0][1] 
        show_info = self.info_extractor(extra)
        output = self.check_output(show_info[0])

        Downloader(logger=self.logger, download_url=download_url, backup_url=source_url, hidden_url=hidden_url,output=output, header=self.header, user_agent=self.user_agent,
                   show_info=show_info, settings=self.settings, quiet=self.quiet)

    def test(self, i, ii):
        print(i, ii)

    def download_show(self, url):
        page = self.request_c(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        ep_range = self.ep_range
        links = []
        for link in soup.findAll('a', {'class': 'sonra'}):
            if link['href'] not in links:
                links.append(link['href'])
    
        if self.exclude is not None:
            excluded = [i for e in self.exclude for i in links if re.search(e, i)]
            links = [item for item in links if item not in excluded]

        season = "season-" + self.season

        if self.update == True:
            links = links[0:1]

        if len(ep_range) == 1:
            ep_range = '{0}-{0}'.format(ep_range)

        if ep_range == 'l5' or ep_range == 'L5':  # L5 (Last five)
            links = links[:5]
            ep_range = 'All'
            season = 'season-All'

        if self.newest:  # True or False
            links = links[0:1]
            ep_range = 'All'
            season = 'season-All'

        if season != "season-All" and ep_range != "All":
            episodes = ["episode-{0}".format(n) for n in
                        range(int(ep_range[0]), int(ep_range[1]) + 1)]
            if season == 'season-1':
                matching = [s for s in links if 'season' not in s or season in s]
            else:
                matching = [s for s in links if season in s]
            matching = [s for s in matching for i in episodes if i == re.search(r'episode-[0-9]+', s).group(0)]
        elif season != "season-All":
            if season == 'season-1':
                matching = [s for s in links if 'season' not in s or season in s]
            else:
                matching = [s for s in links if season in s]
        elif ep_range != 'All':
            episodes = ["episode-{0}".format(n) for n in
                        range(int(ep_range[0]), int(ep_range[1]) + 1)]
            matching = [s for s in links for i in episodes if re.search("{0}-".format(i), s)]
        else:
            matching = links

        if len(matching) < 1:
            matching.reverse()
        if (self.threads != None and self.threads != 0):
            if (len(matching) == 1):
                for item in matching:
                    source_url, backup_url = self.find_download_link(item)
                    hidden_url = self.find_hidden_url(item)
                    if self.resolution == '480' or len(source_url[0]) > 2:
                        download_url = source_url[0][1]
                    else:
                        try:
                            download_url = source_url[1][1]
                        except Exception:
                            download_url = source_url[0][1] 
                    show_info = self.info_extractor(item)
                    output = self.check_output(show_info[0])

                    Downloader(logger=self.logger, download_url=download_url, backup_url=backup_url, hidden_url=hidden_url ,output=output, header=self.header, user_agent=self.user_agent,
                            show_info=show_info, settings=self.settings, quiet=self.quiet)
            else:
                count = 0
                while (True):
                    processes_count = 0
                    processes = []
                    processes_url = []
                    processes_extra = []
                    
                    if (int(self.threads) > len(matching)):
                        print('To many threads, setting threads to deafult amount.')
                        self.threads = 3
                    
                    procs = ProcessParallel(print('Threads started', end='\n\n'))
                    for x in range(int(self.threads)):
                        try:
                            item = matching[count]
                            _, extra = self.is_valid(item)
                            processes.append(self.download_single)
                            processes_url.append(item)
                            processes_extra.append(extra)
                            count += 1
                        except Exception as e:
                            if self.logger == 'True':
                                print('Error: {0}'.format(e))
                            pass
                    for x in processes:
                        procs.append_process(x, url=processes_url[processes_count], extra=processes_extra[processes_count])
                        processes_count+=1

                    if ('' in processes_extra):
                        self.threads = None
                        self.download_show(url)
                        break
                        
                    procs.fork_processes()
                    procs.start_all()
                    procs.join_all()
                    processes_url.clear()
                    processes_extra.clear()
                    processes.clear()
                    self.threads = self.original_thread
                    if (count >= len(matching)):
                        break
        else:
            for item in matching:
                source_url, backup_url = self.find_download_link(item)
                hidden_url = self.find_hidden_url(item)
                if self.resolution == '480' or len(source_url[0]) > 2:
                    download_url = source_url[0][1]
                else:
                    try:
                        download_url = source_url[1][1]
                    except Exception:
                        download_url = source_url[0][1] 
                show_info = self.info_extractor(item)
                output = self.check_output(show_info[0])

                Downloader(logger=self.logger, download_url=download_url, backup_url=backup_url, hidden_url=hidden_url ,output=output, header=self.header, user_agent=self.user_agent,
                        show_info=show_info, settings=self.settings, quiet=self.quiet)
            if (self.original_thread != None and self.original_thread != 0): 
                self.threads = self.original_thread

    @staticmethod
    def info_extractor(url):
        url = re.sub('https://www.wcostream.net/', '', url)
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
            season = "Season 1"
            episode = "Episode 0"
            desc = ""
        return show_name.title().strip(), season.title().strip(), episode.title().strip(), desc.title().strip(), url

    def is_valid(self, url):
        website = re.findall('https://(www.)?wcostream.net/(anime/)?([a-zA-Z].+$)?', url)
        if website:
            if website[0][1] == "anime/":
                return True, (website[0][1], website[0][2])
            return True, website[0][2]
        return False, '[wco-dl] Not correct wcostream website.'

    def get_download_url(self, embed_url):
        page = requests.get(embed_url, headers=self.header)
        html = page.text

        # Find the stream URLs.
        if 'getvid?evid' in html:
            # Query-style stream getting.
            source_url = re.search(r'getJSON\("(.*?)"', html, re.DOTALL).group(1)

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
        # print("debug:", source_urls)
        # print("debug:", backup_url)

        return source_urls, backup_url
