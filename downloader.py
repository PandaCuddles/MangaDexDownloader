import json

import re
import requests

from concurrent.futures import ThreadPoolExecutor
from os import mkdir
from os import path
from requests.exceptions import ConnectionError
from threading import Lock




find_id        = re.compile("\/\d+\/*")


class MangaDownloader():
    """Download manager for downloading a manga from MangaDex"""
    def __init__(self, url, language="English", threaded=True):
        self.mutex_initialize = Lock()
        self.mutex_total = Lock()
        self.mutex_downloaded = Lock()

        self.MAX_CHAPTER_THREADS = 10
        self.MAX_INITIALIZATION_THREADS = 10

        self.threaded = threaded

        self.language_list = {
                              "English" : "gb",
                              "French"  : "fr",
                             }

        self.name = None
        self.url = url
        self.language = self.language_list[language]
        self.chapters = {}
        self.total_images = 0
        self.downloaded_images = 0

    def initialize(self):
        """Get chapter ids and img urls for each chapter"""

        print("Initializing...")

        # Get list of chapter ids
        chapter_list = self.chapter_info()
        print(f"Retrieved chapter info for: {self.name}")

        if not chapter_list:
            raise Exception(f"Failed to initialize '{self.name}'")
        
        # Download the info for each chapter in a separate thread (threading: faster, but possibly less stable)
        if self.threaded:
            with ThreadPoolExecutor(max_workers=self.MAX_CHAPTER_THREADS) as executor:
                for chapter in chapter_list:
                    executor.submit(self.image_urls, chapter)

        # Download the info for each chapter one by one (no threading: slower, but possibly more stable)
        else:
            for chapter in chapter_list:
                self.image_urls(chapter)
        print(f"Retrieve image urls for: {self.name}")
        print(f"Total images to download: {self.total_images}")

        #with open(f"{self.name}.json", "w") as outfile:
        #    json.dump(self.chapters, outfile)

        return 1

    def update_chapters(self, chapter_num, chapter_info):
        self.mutex_initialize.acquire()
        self.chapters[chapter_num] = chapter_info
        self.mutex_initialize.release()

    def update_total(self, update):
        self.mutex_total.acquire()
        self.total_images += update
        self.mutex_total.release()
    
    def update_completed(self, update):
        self.mutex_downloaded.acquire()
        self.downloaded_images =+ update
        self.mutex_downloaded.release()

    def chapter_info(self):
        """Use the MangaDex api to retrieve all the chapter information for a manga"""
        
        m_id = find_id.search(self.url)[0].replace("/", "")
        
        manga_api_v2 = f"https://mangadex.org/api/v2/manga/{m_id}/chapters"
        
        manga = requests.get(manga_api_v2)

        if manga and manga.status_code == 200:
            manga = json.loads(manga.text)
        else:
            raise Exception(f"Failed to initialize '{self.name}'")
        
        # Start chapter extraction from mangadex manga api dictionary
        chapters     = []
        chapter_list = manga["data"]["chapters"]

        # Loop through each chapter and check chapter language
        for chapter in chapter_list:

            # Search for all chapters with specified language
            if chapter["language"] == self.language:

                chapter_id  = chapter["id"]

                chapters.append(chapter_id)

        
        title = manga["data"]["chapters"][0]["mangaTitle"]

        # Make title safe for creating a folder name
        for c in "!@#$%^&*(),.<>/?'\"[]{};:-":
            title = title.replace(c, "")
        title = title.lower().replace(" ", "_")
        
        self.name = title

        return chapters


    def image_urls(self, chapter_id):
        """Use the MangaDex api v2 to retrieve the list of image urls for each chapter"""

        chapter_api_v2 = f"https://mangadex.org/api/v2/chapter/{chapter_id}"
        
        chapter = requests.get(chapter_api_v2)

        if chapter and chapter.status_code == 200:
            chapter = json.loads(chapter.text)
        else:
            raise Exception(f"Failed to initialize '{self.name}'")
        
        server_url     = chapter["data"]["server"]
        link_hash      = chapter["data"]["hash"]
        chapter_num    = chapter["data"]["chapter"]
        chapter_images  = chapter["data"]["pages"]

        chapter_info = {
            "server":server_url, 
            "hash":link_hash, 
            "images":chapter_images,
            }

        # Thread safe function, allowing multithreaded initialization
        self.update_chapters(chapter_num, chapter_info)

        self.update_total(len(chapter_images))

    def threaded_chapter(self, chapter_folder, curr_chapter, base_url):
        """Downloads each image in a chapter"""
        if not path.isdir(chapter_folder):
                    mkdir(chapter_folder)

        with requests.Session() as s:
            for image in curr_chapter["images"]:
                image_url = f"{base_url}{image}"
                image_file = f"{chapter_folder}{image}"

                response = s.get(image_url)

                if response and response.status_code == 200:
                    with open(image_file, "wb") as img_file:
                        img_file.write(response.content)


    def threaded_download(self):
        """Downloads each chapter in its own thread"""

        if not path.isdir(self.name):
            mkdir(self.name)

        with ThreadPoolExecutor(max_workers=self.MAX_CHAPTER_THREADS) as executor:
            for chapter in self.chapters.keys():

                chapter_folder = f"{self.name}/{chapter}/"
                curr_chapter = self.chapters[chapter]
                base_url = f"{curr_chapter['server']}{curr_chapter['hash']}/"

                executor.submit(self.threaded_chapter, chapter_folder, curr_chapter, base_url)


    def regular_download(self):
        """Downloads each chapter and image in a single thread"""
        if not path.isdir(self.name):
            mkdir(self.name)

        for chapter in self.chapters.keys():

            chapter_folder = f"{self.name}/{chapter}/"
            curr_chapter = self.chapters[chapter]
            base_url = f"{curr_chapter['server']}{curr_chapter['hash']}/"

            if not path.isdir(chapter_folder):
                    mkdir(chapter_folder)

            with requests.Session() as s:
                for image in curr_chapter["images"]:
                    image_url = f"{base_url}{image}"
                    image_file = f"{chapter_folder}{image}"

                    response = s.get(image_url)

                    if response and response.status_code == 200:
                        with open(image_file, "wb") as img_file:
                            img_file.write(response.content)

    def start_download(self):
        print("Download starting...")
        if self.threaded:
            self.threaded_download()
        else:
            self.regular_download()
        print(f"Downloaded: {self.name}")
