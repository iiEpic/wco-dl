import requests
from bs4 import BeautifulSoup
import re
import subprocess
import logging
import os
import argparse

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, filename='wco_dl_wrapper.log', filemode='a',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.info("Logging initialized.")
    print("[INFO] Logging initialized.")

def extract_episode_links(series_url):
    print(f"[INFO] Fetching episode links from: {series_url}")
    logging.info(f"Fetching episode links from: {series_url}")
    try:
        response = requests.get(series_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch series page: {e}")
        print(f"[ERROR] Failed to fetch series page: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    logging.debug(f"Page HTML snippet: {soup.prettify()[:1000]}")
    print(f"[DEBUG] Page HTML snippet: {soup.prettify()[:500]}")
    
    episode_links = set()  # Using a set to ensure unique links
    series_name = series_url.split('/')[-1].replace('-', ' ')  # Extract series name for filtering
    
    # Locate the specific div containing the episode list
    list_container = soup.find("div", id="catlist-listview")
    if not list_container:
        logging.error("[ERROR] Could not find episode list container.")
        print("[ERROR] Could not find episode list container.")
        return []
    
    # Find all <a> tags within the unordered list
    all_links = list_container.find_all('a', href=True)
    print(f"[DEBUG] Total episode links found in list: {len(all_links)}")
    logging.debug(f"Total episode links found in list: {len(all_links)}")

    for a_tag in all_links:
        href = a_tag['href']
        print(f"[DEBUG] Checking link: {href}")
        if series_name.replace(' ', '-').lower() in href:
            full_url = f"https://www.wcostream.tv{href}" if href.startswith('/') else href
            episode_links.add(full_url)  # Add to set to ensure uniqueness
            logging.debug(f"Found episode link: {full_url}")
            print(f"[INFO] Found episode: {full_url}")
    
    logging.info(f"Total unique episodes found: {len(episode_links)}")
    print(f"[INFO] Total unique episodes found: {len(episode_links)}")
    return list(episode_links)  # Convert set back to list for iteration

def download_episode(episode_url, output_dir):
    print(f"[INFO] Attempting to download episode: {episode_url}")
    logging.info(f"Attempting to download episode: {episode_url}")
    command = ['python3', '__main__.py', '-i', episode_url, '--output', output_dir]
    try:
        subprocess.run(command, check=True)
        logging.info(f"Successfully downloaded: {episode_url}")
        print(f"[SUCCESS] Downloaded: {episode_url}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download {episode_url}: {e}")
        print(f"[ERROR] Failed to download {episode_url}: {e}")
        if 'premium' in str(e).lower():
            logging.warning(f"Skipping premium episode: {episode_url}")
            print(f"[WARNING] Skipping premium episode: {episode_url}")
        else:
            logging.error(f"Unexpected error downloading episode: {episode_url}")
            print(f"[ERROR] Unexpected error downloading episode: {episode_url}")

def main(series_url, output_dir):
    setup_logging()
    print("[INFO] Starting the download process.")
    logging.info("Starting the download process.")
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory confirmed: {output_dir}")
    logging.info(f"Output directory confirmed: {output_dir}")
    
    episode_links = extract_episode_links(series_url)
    if not episode_links:
        logging.warning("No episode links found. Exiting.")
        print("[WARNING] No episode links found. Exiting.")
        return
    
    for episode_url in episode_links:
        download_episode(episode_url, output_dir)
    
    logging.info("Download process completed.")
    print("[INFO] Download process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automate wco-dl to download episodes from a series page.')
    parser.add_argument('series_url', type=str, help='URL of the series to download')
    parser.add_argument('--output', '-o', type=str, required=True, help='Specify the output directory')
    args = parser.parse_args()
    
    try:
        main(args.series_url, args.output)
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        print(f"[CRITICAL] Fatal error: {e}")
