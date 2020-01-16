#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__author__ = "_iEpic"
__email__ = "iepicunknown@gmail.com"
"""

# TODO: Add functionality of Anime-dl (Arguments, resolutions(480 or 720))
# TODO: Add different files/folders for different classes
# TODO: Make shit look prettier
# TODO: *** download_shows function ***

import requests
import urllib3
import base64
import re
import os
from cfscrape import create_scraper
from bs4 import BeautifulSoup
from requests import session
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = input('Input the URL: ')
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36' \
                 '(KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
header = {
    'User-Agent': user_agent, 'Accept': '*/*', 'Referer': url, 'X-Requested-With': 'XMLHttpRequest'
}
base_url = "https://wcostream.com"
path = os.path.dirname(os.path.realpath(__file__))


def info_extractor(link_url):
    try:
        episode_no = re.search('episode-[0-9]+', link_url).group(0).replace('episode-', '')
    except:
        episode_no = '0'

    if 'season' in link_url:
        show_name = re.search('.com(.*)season', link_url).group(0).replace('.com/', '').replace('-season', '').replace(
            '-', ' ').title()
        season_no = re.search('season-[0-9]+', link_url).group(0).replace('season-', '')
    elif 'special' in link_url:
        show_name = re.search('.com(.*)special', link_url).group(0).replace('.com/', '').replace('-', ' ').title()
        season_no = '0'
    elif 'ova' in link_url:
        show_name = re.search('.com(.*)ova', link_url).group(0).replace('.com/', '').replace('-ova', '').replace(
            '-', ' ').title()
        episode_no = 0
        season_no = 0
        return "{0} OVA".format(show_name)
    else:
        show_name = re.search('.com(.*)episode', link_url).group(0).replace('.com/', '').replace(
            '-episode', '').replace('-', ' ').title()
        season_no = '1'
    return "{0} S{1}E{2}".format(show_name, season_no, episode_no)


def request_c(url, extraHeaders=None):
    myheaders = {
        'User-Agent': user_agent,
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


def _decode(array, ending):
    iframe = ''
    for item in array:
        decoded = base64.b64decode(item).decode('utf8')
        numbers = re.sub('[^0-9]+', '', decoded)
        # print(chr(int(numbers) - ending))
        iframe += chr(int(numbers) - ending)
    html = BeautifulSoup(iframe, 'html.parser')
    return base_url + html.find("iframe")['src']


def download_shows(playlist_url):
    # TODO: Begin this section!
    # TODO: Scrub the link to ensure its /anime/(Name of Anime) so it has multiple shows
    # This will currently get all show file names
    page = requests.get(playlist_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    episode_list = soup.findAll('div', {'id': 'catlist-listview'})[0]

    episode_links = episode_list.findAll('a')

    for link in episode_links:
        file_name = info_extractor(link['href'])
        print(file_name)
    pass


def get_download_url(embed_url):
    page = request_c(embed_url)
    html = page.text

    # Find the stream URLs.
    if 'getvid?evid' in html:
        # Query-style stream getting.
        source_url = re.search('get\("(.*?)"', html, re.DOTALL).group(1)

        page2 = request_c(
            base_url + source_url,
            extraHeaders={
                'User-Agent': user_agent, 'Accept': '*/*', 'Referer': embed_url,
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
        sources_block = re.search('sources:\s*?\[(.*?)\]', html, re.DOTALL).group(1)
        stream_pattern = re.compile('\{\s*?file:\s*?"(.*?)"(?:,\s*?label:\s*?"(.*?)")?')
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


def download(download_url, page_url):
    sess = session()
    sess = create_scraper(sess)

    file_name = info_extractor(page_url)
    print('[wco-dl] - Downloading {0}'.format(file_name))
    dlr = sess.get(download_url, stream=True, headers=header)  # Downloading the content using python.
    with open(path + "\\{0}.mp4".format(file_name), "wb") as handle:
        for data in tqdm(dlr.iter_content(chunk_size=1024)):  # Added chunk size to speed up the downloads
            handle.write(data)
    print("[wco-dl] Download for {0} completed.".format(file_name))


page = requests.get(url)
soup = BeautifulSoup(page.text, 'html.parser')

embedURL = soup.find("meta", {"itemprop": "embedURL"})
scriptURL = embedURL.next_element.next_element.text
letters = scriptURL[scriptURL.find("[")+1:scriptURL.find("]")]
endingNumber = int(re.search(' - ([0-9]+)', scriptURL).group(1))

hiddenURL = _decode(letters.split(', '), endingNumber)

download_link = get_download_url(hiddenURL)[0]

download(download_link, url)
