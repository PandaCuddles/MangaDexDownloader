import requests

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

def multithread():
    """Display option to use multithreading and return answer"""

    answer = input("Do you want to enable mutlithreaded downloads (faster, experimental)? [Y/n] ") or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Multithreading enabled")
        return True
    else:
        print("Multithreading disabled")
        return False

def datasaver():
    """Display option to use mangadex datasaver and return answer"""

    answer = input("Do you want to enable datasaver for downloads (stable, recommended)? [Y/n] ") or "y"

    yes = ["y", "ye", "yes", "yess", "yus"]
    if answer.lower() in yes:
        print("Datasaver enabled")
        return True
    else:
        print("Datasaver disabled")
        return False