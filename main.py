import re
import requests
import time


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

def check_connection():
    """Check internet connection before starting the program"""

    print("Connection test starting...")
    try:
        # Only retrieve page header information (speeds up the check)
        requests.head("https://www.duckduckgo.com", allow_redirects=False)

        print(f"Passed!")
        return 1
    except requests.ConnectionError:
        print("Failed!")
        return 0

def multithread_config():
    """Display option to use multithreading and return answer"""

    answer = input("Do you want to enable mutlithreaded downloads (faster, experimental)? [Y/n] ") or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Multithreading enabled")
        return True
    else:
        print("Multithreading disabled")
        return False

def start(url_list, threaded):
    """Create downloader objects from a list of manga urls and start the download for each"""
    t1 = time.perf_counter()
        
    for url in url_list:
            
        m = MangaDownloader(url, threaded=threaded)
        ok = m.initialize()
        if ok:
            m.start_download()
        else:
            print("Something went wrong")
            
    t2 = time.perf_counter()
    print(f"Finished in {int(t2-t1)} seconds")

def main():
    threaded_config = multithread_config()
    url_list = get_input()

    if not url_list:
        return None
    else:
        start(url_list, threaded_config)


if __name__ == '__main__':
    conn_ok = check_connection()

    if conn_ok:
        main()