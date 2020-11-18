"""Config module that contains:
                                Configuration functions

                                Configuration constants"""
import re
import time

from os import (name as sys_name, system)
from typing import NoReturn

import requests


MAX_MANGA_THREADS   = 2 # One more for the display function
MAX_CHAPTER_THREADS = 10
MAX_IMAGE_THREADS   = 10
MAX_INITIALIZATION_THREADS = 10

ENABLE = lambda x: "Enabled" if x else "Disabled"

LANGUAGE_LIST = [
                ("English (Default)"     , "gb", "English"       ),
                ("Chinese (simple)"      , "cn", "Chinese (s)"   ),
                ("Chinese (traditional)" , "hk", "Chinese (t)"   ),
                ("French"                , "fr", "French"        ),
                ("Indonesian"            , "id", "Indonesian"    ),
                ("Polish"                , "pl", "Polish"        ),
                ("Portuguese (Brazil)"   , "br", "Portuguese (b)"),
                ("Russian"               , "ru", "Russian"       ),
                ("Spanish (Mexican)"     , "mx", "Spanish (m)"   ),
                ("Spanish (Spain)"       , "es", "Spanish (s)"   ),
                ("Vietnamese"            , "vn", "Vietnamese"    ) ]


def check_connection() -> int:
    """Check internet connection before starting the program"""

    print("Internet connection test starting...")
    try:
        # Only retrieve page header information (speeds up the check)
        requests.head("https://www.duckduckgo.com", allow_redirects=False)

        print("Passed!")
        return 1
    except requests.ConnectionError:
        print("Failed!")
        return 0


def multithread_option() -> bool:
    """Display option to use multithreading and return answer"""

    question = "Do you want to enable mutlithreaded downloads (faster, experimental)? [Y/n] "
    answer = input(question) or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Multithreading enabled")
        return True

    print("Multithreading disabled")
    return False


def datasaver_option() -> bool:
    """Display option to use mangadex datasaver and return answer"""

    question = "Do you want to enable datasaver for downloads (stable, recommended)? [Y/n] "
    answer = input(question) or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Datasaver enabled")
        return True

    print("Datasaver disabled")
    return False


def language_option() -> str:
    """Display option for what language to use for downloads"""

    check_answer = re.compile(r"\d+")

    for enum in enumerate(LANGUAGE_LIST):
        print(f"{enum[0]:<3}: {enum[1][0]}")

    answer = input("\nPlease select your langauge: ")

    if check_answer.search(answer) and int(answer) in range(len(LANGUAGE_LIST)):
        return LANGUAGE_LIST[int(answer)]

    return LANGUAGE_LIST[0]


def clear_screen() -> NoReturn:
    """Clear terminal screen"""
    # Windows screen clear
    if sys_name == 'nt':
        _ = system('cls')

    # Posix screen clear
    else:
        _ = system('clear')


def print_status(
                status_dict  : dict,
                finished     : int,
                started      : int,
                chapters_dl  : int,
                chapters_tot : int,
                options      : list) -> NoReturn:
    """Display download setup status and download status for the manga downloads"""

    clear_screen()
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
#            Threaded: {options[0]:<8}   Datasaver: {options[1]:<8}   Language: {options[2]:<14}    #\n\
#                                                                                   #\n\
#                                                                                   #\n\
#    Type 'exit' and press enter to exit the program                                #\n\
#                                                                                   #\n\
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

    time.sleep(0.5)
