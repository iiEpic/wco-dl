import requests
import base64
import re
import os
from cfscrape import create_scraper
from bs4 import BeautifulSoup
from requests import session
from tqdm import tqdm

url = input('Input the URL: ')
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36' \
                 '(KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
header = {
    'User-Agent': user_agent, 'Accept': '*/*', 'Referer': url, 'X-Requested-With': 'XMLHttpRequest'
}
base_url = "https://wcostream.com"
path = os.path.dirname(os.path.realpath(__file__))

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


def get_download_url(embed_url):
    r2 = request_c(embed_url)
    html = r2.text

    # Find the stream URLs.
    if 'getvid?evid' in html:
        # Query-style stream getting.
        sourceURL = re.search('get\("(.*?)"', html, re.DOTALL).group(1)

        # Inline code similar to 'requestHelper()'.
        # The User-Agent for this next request is somehow encoded into the media tokens, so we make sure to use
        # the EXACT SAME value later, when playing the media, or else we get a HTTP 404 / 500 error.
        r3 = request_c(
            base_url + sourceURL,
            extraHeaders={
                'User-Agent': user_agent, 'Accept': '*/*', 'Referer': embed_url,
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
        if not r3.ok:
            raise Exception('Sources XMLHttpRequest request failed')
        jsonData = r3.json()

        # Only two qualities are ever available: 480p ("SD") and 720p ("HD").
        sourceURLs = []
        sdToken = jsonData.get('enc', '')
        hdToken = jsonData.get('hd', '')
        sourceBaseURL = jsonData.get('server', '') + '/getvid?evid='
        if sdToken:
            sourceURLs.append(('480 (SD)', sourceBaseURL + sdToken))  # Order the items as (LABEL, URL).
        if hdToken:
            sourceURLs.append(('720 (HD)', sourceBaseURL + hdToken))
        # Use the same backup stream method as the source: cdn domain + SD stream.
        backupURL = jsonData.get('cdn', '') + '/getvid?evid=' + (sdToken or hdToken)
    else:
        # Alternative video player page, with plain stream links in the JWPlayer javascript.
        sourcesBlock = re.search('sources:\s*?\[(.*?)\]', html, re.DOTALL).group(1)
        streamPattern = re.compile('\{\s*?file:\s*?"(.*?)"(?:,\s*?label:\s*?"(.*?)")?')
        sourceURLs = [
            # Order the items as (LABEL (or empty string), URL).
            (sourceMatch.group(2), sourceMatch.group(1))
            for sourceMatch in streamPattern.finditer(sourcesBlock)
        ]
        # Use the backup link in the 'onError' handler of the 'jw' player.
        backupMatch = streamPattern.search(html[html.find(b'jw.onError'):])
        backupURL = backupMatch.group(1) if backupMatch else ''
    #print("debug:", backupURL)
    #print("debug:", sourceURLs)

    return sourceURLs[0][1]


def download(url):
    sess = session()
    sess = create_scraper(sess)
    dlr = sess.get(url, stream=True, headers=header)  # Downloading the content using python.
    with open(path + "\\temp.mp4", "wb") as handle:
        for data in tqdm(dlr.iter_content(chunk_size=1024)):  # Added chunk size to speed up the downloads
            handle.write(data)
    print("Download has been completed.")  # Viola


page = requests.get(url)
soup = BeautifulSoup(page.text, 'html.parser')

embedURL = soup.find("meta", {"itemprop": "embedURL"})
scriptURL = embedURL.next_element.next_element.text
letters = scriptURL[scriptURL.find("[")+1:scriptURL.find("]")]
endingNumber = int(re.search(' - (\d+)', scriptURL).group(1))


hiddenURL = _decode(letters.split(', '), endingNumber)

download_link = get_download_url(hiddenURL)

download(download_link)