import json
import re

import time

from concurrent.futures import ThreadPoolExecutor
from os import (mkdir, path)

from urllib3.util.retry import Retry
from threading import Lock
from typing import NoReturn
from requests.adapters import HTTPAdapter

import requests


import config

find_id        = re.compile(r"\/\d+\/*")


mutex = Lock()
m_tot = Lock() # For updating the total number of downloads
m_fin= Lock() # For updating the number of finished downloads
m_setup = Lock() # For updating how much chapter info has been downloaded during setup

STATUS_DICT = {} # Contains list of all currently downloading manga

MANGA_STARTED = 0
MANGA_FINISHED = 0

CHAPTER_INFO_TOTAL = 0
CHAPTER_INFO_DL     = 0

OPTIONS = []


def update_status(
                  to_total       : bool = None,
                  to_finished    : bool = None,
                  name           : str = None,
                  status         : int = None,
                  setup_progress : bool = None) -> NoReturn:
    """Used to update the different program stats that are displayed while downloading:

    The started and finished global variables are used to tell the display status thread
    when to exit and return to the main thread, as well as to display the total number of
    finished downloads

    to_total:
            Used to keep track of the total number of manga being downloaded

    to_finished:
            Updates the total number of finished downloads

    name, status:
            Adds current download info to a dictionary of finished and/or
            currently downloading manga
            (used for displaying the download status of all the finished
            and/or currently downloading manga)

    setup_progress:
            Updates the amount of chapter info that has been downloaded
            during each manga's download setup
    """
    if to_total:
        m_tot.acquire()
        global MANGA_STARTED
        MANGA_STARTED += 1
        m_tot.release()

    if to_finished:
        m_fin.acquire()
        global MANGA_FINISHED
        MANGA_FINISHED += 1
        m_fin.release()

    if name and status:
        mutex.acquire()
        global STATUS_DICT
        STATUS_DICT[name] = status
        mutex.release()

    if setup_progress:
        m_setup.acquire()
        global CHAPTER_INFO_DL
        CHAPTER_INFO_DL += 1
        m_setup.release()


def display_status() -> NoReturn:
    global STATUS_DICT
    global MANGA_STARTED
    global MANGA_FINISHED
    global CHAPTER_INFO_TOTAL
    global CHAPTER_INFO_DL
    global OPTIONS

    while MANGA_FINISHED < MANGA_STARTED:
        config.print_status(
                            STATUS_DICT,
                            MANGA_FINISHED,
                            MANGA_STARTED,
                            CHAPTER_INFO_DL,
                            CHAPTER_INFO_TOTAL,
                            options=OPTIONS)

    config.print_status(
                        STATUS_DICT,
                        MANGA_FINISHED,
                        MANGA_STARTED,
                        CHAPTER_INFO_DL,
                        CHAPTER_INFO_TOTAL,
                        options=OPTIONS)


class MangaDownloader():
    """Download manager for downloading a manga from MangaDex"""

    def __init__(self,
                 url         : str,
                 threaded    : bool = True,
                 datasaver   : bool = True,
                 language    : str = "English",
                 language_id : str = "gb"):

        self.name = None
        self.url  = url

        self.language    = language
        self.language_id = language_id
        self.threaded    = threaded
        self.datasaver   = datasaver

        self.chapters = {}
        self.total_images = 0
        self.downloaded_images = 0

        self.mutex_initialize = Lock()
        self.mutex_total = Lock()
        self.mutex_downloaded = Lock()

        self.options_set()


    def options_set(self):
        """Set global variables to program options for use in the status display"""

        global OPTIONS
        OPTIONS.append(config.ENABLE(self.threaded))
        OPTIONS.append(config.ENABLE(self.datasaver))
        OPTIONS.append(self.language)



    def update_chapters(self, chapter_num : str, chapter_info : dict) -> NoReturn:
        """Provides a threadsafe way to update the dictionary of chapter information"""

        self.mutex_initialize.acquire()
        self.chapters[chapter_num] = chapter_info
        self.mutex_initialize.release()


    def update_total(self, update : int) -> NoReturn:
        """Provides a threadsafe way to update the total number of images in the manga"""

        self.mutex_total.acquire()
        self.total_images += update
        self.mutex_total.release()


    def update_completed(self, update : int) -> NoReturn:
        """Provides a threadsafe way to update the number of completed image downloads"""

        self.mutex_downloaded.acquire()
        self.downloaded_images += update
        self.mutex_downloaded.release()


    def initialize(self) -> int:
        """Get chapter ids and img urls for each chapter"""

        # Get list of chapter ids
        chapter_list = self.chapter_info()

        if not chapter_list:
            print(f"Failed to initialize      : '{self.name}'")
            return 0

        # Download the info for each chapter in a separate thread
        # (threading: faster, but possibly less stable)
        if self.threaded:
            with ThreadPoolExecutor(max_workers=config.MAX_CHAPTER_THREADS) as executor:
                for chapter in chapter_list:
                    executor.submit(self.image_urls, chapter)

        # Download the info for each chapter one by one
        # (no threading: much slower, but possibly more stable)
        else:
            for chapter in chapter_list:
                self.image_urls(chapter)

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Have a status updater running while the manga is downloading
            executor.submit(self.status)

            # Start download after initialization
            executor.submit(self.start_download)

        # Update number of finished downloads
        update_status(to_finished=True)

        # Reset the download setup info before starting next manga download
        global CHAPTER_INFO_TOTAL
        global CHAPTER_INFO_DL
        CHAPTER_INFO_TOTAL = 0
        CHAPTER_INFO_DL = 0

        return 1


    def start_download(self) -> NoReturn:
        """Starts the manga download in either threaded mode or regular mode """
        if self.threaded:
            self.threaded_download()
        else:
            self.regular_download()


    def chapter_info(self) -> list:
        """Use the MangaDex api to retrieve all the chapter information for a manga"""

        m_id = find_id.search(self.url)[0].replace("/", "")
        manga_api_v2 = f"https://mangadex.org/api/v2/manga/{m_id}/chapters"
        response = requests.get(manga_api_v2, headers={"Connection":"close"})

        if response and response.status_code == 200:
            manga = json.loads(response.text)
        else:
            raise Exception(f"Failed to initialize '{self.name}'")

        # Start chapter extraction from mangadex manga api dictionary
        chapter_list = manga["data"]["chapters"]

        # Loop through each chapter and check chapter language
        # Add chapters with specified language to dictionary
        chapters     = []
        for chapter in chapter_list:
            if chapter["language"] == self.language_id:
                chapters.append(chapter)

        # Replaces empty chapter numbers with '0'
        for i in range(len(chapters)):
            if chapters[i]["chapter"] == "":
                chapters[i]["chapter"] = "0"


        # Goes through a process of filtering out duplicates and
        # leaving the chapters with the most views
        filtered_dict = {}

        for x in chapters:
            x_chapter = x["chapter"]
            x_views = x["views"]

            if not x_chapter in filtered_dict.keys():
                filtered_dict[x_chapter] = x

            elif filtered_dict[x_chapter]["views"] < x_views:
                filtered_dict[x_chapter] = x

        # Create a new list with the ids of the filtered chapters
        chapters_filtered = []
        for val in filtered_dict.values():
            chapters_filtered.append(val["id"])

        title = manga["data"]["chapters"][0]["mangaTitle"]

        # Make title safe for creating a folder name
        for c in "!@#$%^&*(),.<>/?'\"[]{};:-":
            title = title.replace(c, "")

        title = title.lower().replace(" ", "_")

        self.name = title

        # Update number of chapters needed to get image urls for
        # (needed for download setup status display)
        global CHAPTER_INFO_TOTAL
        CHAPTER_INFO_TOTAL= len(chapters_filtered)

        return chapters_filtered


    def image_urls(self, chapter_id : int) -> NoReturn:
        """Use the MangaDex api v2 to retrieve the list of image urls for each chapter"""

        chapter_api_v2 = f"https://mangadex.org/api/v2/chapter/{chapter_id}"

        # Datasaver provides links to compressed versions of the original images
        # (reduces bandwidth usage and storage space)
        if self.datasaver:
            chapter_api_v2 += "?saver=true"

        # Sets up retry configuration to prevent connection refusals from too many requests at once
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.get(
                                chapter_api_v2,
                                headers={"Connection":"close"}
                                )

        #response = requests.get(chapter_api_v2, headers={"Connection":"close"})

        if response and response.status_code == 200:
            chapter = json.loads(response.text)
        else:
            raise Exception(f"Failed to initialize '{self.name}'")

        server_url      = chapter["data"]["server"]
        link_hash       = chapter["data"]["hash"]
        chapter_images  = chapter["data"]["pages"]

        chapter_num = f"Chapter_{chapter['data']['chapter'].replace('.', '_')}"

        # Udates total number of images the manga contains (needed for displaying percent completion of the download)
        self.update_total(len(chapter_images))

        chapter_info = {
                        "server":server_url,
                        "hash":link_hash,
                        "images":chapter_images,
                        "num":chapter_num,
                        }

        # Updates number of chapters that have had img urls downloaded for (for download setup status display)
        update_status(setup_progress=True)

        # Thread safe function, allowing multithreaded initialization
        self.update_chapters(chapter_num, chapter_info)


    def threaded_image(self, image_file : str, image_url : str) -> NoReturn:
        """Downloads an image into a specified file"""

        # Sets up retry configuration to prevent connection refusals from too many requests at once
        with requests.Session() as session:
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            response = session.get(
                                    image_url,
                                    headers={"Connection":"close"}
                                   )

            if response and response.status_code == 200:
                with open(image_file, "wb") as img_file:
                    img_file.write(response.content)
                self.update_completed(1)


    def threaded_chapter(self, chapter_folder : str, curr_chapter : dict, base_url : str) -> NoReturn:
        """Sends each image in a chapter into a separate thread to be downloaded"""

        # Creates the chapter directory for the current chapter being downloaded
        if not path.isdir(chapter_folder):
            mkdir(chapter_folder)

        # Downloads each image in a separate thread (Default: 10 threads running at a time)
        with ThreadPoolExecutor(max_workers=config.MAX_IMAGE_THREADS) as executor:
            for image in curr_chapter["images"]:
                image_url = f"{base_url}{image}"

                # Name the image accordingly (based on 1, 2, 3, etc.)
                image_file = f"{chapter_folder}{curr_chapter['images'].index(image)+1}{image[-4:]}"
                executor.submit(self.threaded_image, image_file, image_url)


    def threaded_download(self) -> NoReturn:
        """Downloads each chapter in its own thread"""

        if not path.isdir(self.name):
            mkdir(self.name)

        with ThreadPoolExecutor(max_workers=config.MAX_CHAPTER_THREADS) as executor:
            for chapter in self.chapters.keys():

                chapter_folder = f"{self.name}/{chapter}/"
                curr_chapter = self.chapters[chapter]
                base_url = f"{curr_chapter['server']}{curr_chapter['hash']}/"
                executor.submit(self.threaded_chapter, chapter_folder, curr_chapter, base_url)


    def regular_download(self) -> NoReturn:
        """Downloads each chapter and image in a single thread"""

        if not path.isdir(self.name):
            mkdir(self.name)

        for chapter in self.chapters.keys():

            chapter_folder = f"{self.name}/{chapter}/"
            curr_chapter = self.chapters[chapter]
            base_url = f"{curr_chapter['server']}{curr_chapter['hash']}/"

            if not path.isdir(chapter_folder):
                    mkdir(chapter_folder)

            for image in curr_chapter["images"]:

                image_url = f"{base_url}{image}"
                image_file = f"{chapter_folder}{image}"
                response = requests.get(image_url, headers={"Connection":"close"})

                if response and response.status_code == 200:
                    with open(image_file, "wb") as img_file:
                        img_file.write(response.content)
                else:
                    print(f"Error downloading chapter: {curr_chapter['num']} Image: {image}")


    def percent_done(self) -> int:
        """ Returns percentage of the number of downloaded images vs the total images to download"""
        percent = (self.downloaded_images/self.total_images) * 100
        return int(percent)


    def status(self) -> NoReturn:
        """Updates the percent downloaded status for the current manga"""

        curr_status= self.percent_done()
        while(curr_status < 100):

            update_status(name=self.name, status=curr_status)
            time.sleep(0.5)

            curr_status = self.percent_done()

        update_status(name=self.name, status=curr_status)
