import re
import requests
import time

from concurrent.futures import ThreadPoolExecutor
from os import (name, system)
from typing import NoReturn


# Local modules
import config
from downloader import (display_status, add_to_total, MangaDownloader)


def get_input() -> list:
    print("\n\
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
#    Type 'exit' and press enter to exit the program                                #\n\
#                                                                                   #\n\
#####################################################################################")
    
    check = re.compile("[^\n]+mangadex.org/title/\d+[^\n]*")

    url_list = []
    temp = input("")
    
    while temp:
        if temp == "exit":
            print("Exiting...")
            return None

        if check.search(temp):
            url_list.append(temp)
        else:
            print("INVALID URL")
        temp = input("")
    
    if url_list:
        return url_list
    else:
        print("No input: Exiting...")
        return []


def start(url_list : list, threaded : bool, datasaver : bool) -> NoReturn:
    """Create downloader objects from a list of manga urls and start the download for each"""
    t1 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=config.MAX_MANGA_THREADS) as executor:
        
        
        # Update the total number of downloads before starting the display status function
        # The display status function checks the total downloads vs number downloaded in order 
        # to know when to stop
        for i in range(len(url_list)):
            add_to_total()

        executor.submit(display_status)

        for url in url_list:
            m = MangaDownloader(url, threaded=threaded, datasaver=datasaver)
            executor.submit(m.initialize)

    t2 = time.perf_counter()
    print(f"Finished in {int(t2-t1)} seconds")
    

def main() -> NoReturn:
    print()               # formatting
    threaded_config = config.multithread()
    print()               # formatting
    datasaver_config = config.datasaver()
    print("\nLoading...") # formatting
    time.sleep(2.0)       # formatting
    config.clear_screen() # formatting
    url_list = get_input()

    if not url_list:
        pass
    else:
        start(url_list, threaded_config, datasaver_config)


if __name__ == '__main__':
    config.clear_screen()
    conn_ok = config.check_connection()

    if conn_ok:
        main()