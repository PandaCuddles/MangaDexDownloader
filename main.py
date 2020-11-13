import re
import requests
import time

from os import name
from os import system

# Local modules
import config
from downloader import MangaDownloader


def get_input():
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
        return None

def clear_screen():
    # Windows screen clear
    if name == 'nt': 
        val = system('cls') 
  
    # Posix screen clear
    else: 
        val = system('clear') 

def start(url_list, threaded, datasaver):
    """Create downloader objects from a list of manga urls and start the download for each"""
    t1 = time.perf_counter()
        
    for url in url_list:
            
        m = MangaDownloader(url, threaded=threaded, datasaver=datasaver)
        ok = m.initialize()
        if ok:
            m.start_download()
        else:
            print("Something went wrong")
            
    t2 = time.perf_counter()
    print(f"Finished in {int(t2-t1)} seconds")

def main():
    print()               # formatting
    threaded_config = config.multithread()
    print()               # formatting
    datasaver_config = config.datasaver()
    print("\nLoading...") # formatting
    time.sleep(2.0)       # formatting
    clear_screen()        # formatting
    url_list = get_input()

    if not url_list:
        return None
    else:
        start(url_list, threaded_config, datasaver_config)


if __name__ == '__main__':
    clear_screen()
    conn_ok = config.check_connection()

    if conn_ok:
        main()