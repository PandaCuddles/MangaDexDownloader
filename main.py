"""Main module for the MangaDex Downloader program"""
import re
import sys
import time

from concurrent.futures import ThreadPoolExecutor
from typing import NoReturn

# Local modules
import config
from downloader import (display_status, update_status, MangaDownloader)


def get_input(threaded : str, datasaver : str, language : str) -> list:
    """Get list of MangaDex urls from the user or exit the program if 'exit' is typed"""
    config.clear_screen()
    print(f"\n\
                          #############################                              \n\
############################   MangaDex Downloader   ################################\n\
#                         #############################                             #\n\
#                                                                                   #\n\
#    Input list of mangadex manga urls: (press enter after each url)                #\n\
#                                                                                   #\n\
#    Input format example:  https://mangadex.org/title/#####                        #\n\
#                           https://mangadex.org/title/#####/<manga_name>           #\n\
#                           etc...                                                  #\n\
#                                                                                   #\n\
#    Options:                                                                       #\n\
#            Threaded: {threaded:<8}   Datasaver: {datasaver:<8}   Language: {language:<14}    #\n\
#                                                                                   #\n\
#                                                                                   #\n\
#    Type 'exit' and press enter to exit the program                                #\n\
#                                                                                   #\n\
#                                                                                   #\n\
#####################################################################################")

    check = re.compile(r"[^\n]+mangadex.org/title/\d+[^\n]*")

    url_list = []
    temp = input("")

    while temp:
        if temp == "exit":
            print("Exiting...")
            sys.exit(1)

        if check.search(temp):
            url_list.append(temp)
        else:
            print("INVALID URL")
        temp = input("")

    if url_list:
        return url_list


def start(
          url_list : list,
          threaded : bool,
          datasaver : bool,
          language : str,
          language_id : str) -> NoReturn:
    """Create downloader objects from a list of manga urls and start the download for each"""
    time_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=config.MAX_MANGA_THREADS) as executor:


        # Update the total number of downloads before starting the display status function
        # The display status function checks the total downloads vs number downloaded in order
        # to know when to stop
        for _ in range(len(url_list)):
            update_status(to_total=True)

        executor.submit(display_status)

        for url in url_list:
            downloader = MangaDownloader(
                                         url,
                                         threaded=threaded,
                                         datasaver=datasaver,
                                         language=language,
                                         language_id=language_id)
            executor.submit(downloader.initialize)

    time_finish = time.perf_counter()
    print(f"Finished in {int(time_finish-time_start)} seconds")


def main() -> NoReturn:
    """Main function for the MangaDex Download program"""
    print()               # formatting
    threaded_config = config.multithread_option()
    print()               # formatting
    datasaver_config = config.datasaver_option()
    print()
    language_config = config.language_option()
    print("\nLoading...") # formatting
    time.sleep(2.0)       # formatting
    config.clear_screen() # formatting

    while True:
        url_list = get_input(
                             config.ENABLE(threaded_config),
                             config.ENABLE(datasaver_config),
                             language_config[2])
        if url_list:
            start(
                  url_list,
                  threaded_config,
                  datasaver_config,
                  language_config[2],
                  language_config[1])
            break


if __name__ == '__main__':
    config.clear_screen()

    if config.check_connection():
        main()
