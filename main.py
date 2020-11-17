import re
import requests
import time

from concurrent.futures import ThreadPoolExecutor
from os import (name, system)
from typing import NoReturn


# Local modules
import config
from downloader import (display_status, update_status, MangaDownloader)


def get_input(threaded : str, datasaver : str, language : str) -> list:
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
    
    check = re.compile("[^\n]+mangadex.org/title/\d+[^\n]*")

    url_list = []
    temp = input("")
    
    while temp:
        if temp == "exit":
            print("Exiting...")
            exit(1)

        if check.search(temp):
            url_list.append(temp)
        else:
            print("INVALID URL")
        temp = input("")
    
    if url_list:
        return url_list
    else:
        return []


def start(url_list : list, threaded : bool, datasaver : bool, language : str, language_id : str) -> NoReturn:
    """Create downloader objects from a list of manga urls and start the download for each"""
    t1 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=config.MAX_MANGA_THREADS) as executor:
        
        
        # Update the total number of downloads before starting the display status function
        # The display status function checks the total downloads vs number downloaded in order 
        # to know when to stop
        for i in range(len(url_list)):
            update_status(to_total=True)

        executor.submit(display_status)

        for url in url_list:
            m = MangaDownloader(url, threaded=threaded, datasaver=datasaver, language=language, language_id=language_id)
            executor.submit(m.initialize)

    t2 = time.perf_counter()
    print(f"Finished in {int(t2-t1)} seconds")
    

def main() -> NoReturn:
    print()               # formatting
    threaded_config = config.multithread()
    print()               # formatting
    datasaver_config = config.datasaver()
    print()
    language_config = config.language()
    print("\nLoading...") # formatting
    time.sleep(2.0)       # formatting
    config.clear_screen() # formatting

    while True:
        url_list = get_input(config.ENABLE(threaded_config), config.ENABLE(datasaver_config), language_config[2])
        if url_list:
            start(url_list, threaded_config, datasaver_config, language_config[2], language_config[1])
            break


if __name__ == '__main__':
    config.clear_screen()
    conn_ok = config.check_connection()

    if conn_ok:
        main()