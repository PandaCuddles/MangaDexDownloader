import requests
import time

from os import (name, system)
from typing import NoReturn


MAX_MANGA_THREADS = 2 # One more for the display function
MAX_CHAPTER_THREADS = 10
MAX_IMAGE_THREADS = 10
MAX_INITIALIZATION_THREADS = 10


def check_connection() -> int:
    """Check internet connection before starting the program"""

    print("Internet connection test starting...")
    try:
        # Only retrieve page header information (speeds up the check)
        requests.head("https://www.duckduckgo.com", allow_redirects=False)

        print(f"Passed!")
        return 1
    except requests.ConnectionError:
        print("Failed!")
        return 0

def multithread() -> bool:
    """Display option to use multithreading and return answer"""

    answer = input("Do you want to enable mutlithreaded downloads (faster, experimental)? [Y/n] ") or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Multithreading enabled")
        return True
    else:
        print("Multithreading disabled")
        return False

def datasaver() -> bool:
    """Display option to use mangadex datasaver and return answer"""

    answer = input("Do you want to enable datasaver for downloads (stable, recommended)? [Y/n] ") or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Datasaver enabled")
        return True
    else:
        print("Datasaver disabled")
        return False

def clear_screen() -> NoReturn:
    # Windows screen clear
    if name == 'nt': 
        val = system('cls') 
  
    # Posix screen clear
    else: 
        val = system('clear') 

def print_status(status_dict : dict, finished, started, chapters_dl, chapters_tot) -> NoReturn:
    """Display download setup status and download status for the manga downloads"""

    clear_screen()
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
    print(f"Started: {started} Finished: {finished}")
    if status_dict:
        for name, status in status_dict.items():
            print(f"Downloading {name[:15]:<15}: {status}%")
        if chapters_dl < chapters_tot:
            print(f"Chapter info downloaded: {chapters_dl} of {chapters_tot} (setup stage)")
    else:
        
        # Display download setup status after initial chapter count has been downloaded
        if chapters_dl < chapters_tot:
            print(f"Chapter info downloaded: {chapters_dl} of {chapters_tot} (setup stage)")
        else:
            print("Starting initial setup stage...")
    time.sleep(0.5)