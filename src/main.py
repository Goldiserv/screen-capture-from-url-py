import tkinter as tk
from urllib.parse import urlparse, urljoin
import time
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import screenshot_util
from pathlib import Path
import time

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()
total_urls_visited = 0

root= tk.Tk()

def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if href in internal_urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        urls.add(href)
        internal_urls.add(href)
    return urls

def crawl(url, max_urls=3, load_delay=0.05):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 3.
    """
    global total_urls_visited
    total_urls_visited += 1
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    links = get_all_website_links(url)
    for link in links:
        time.sleep(load_delay)
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)

def createCleanFolderFromUrl(url):
    print(url)
    domain_name = urlparse(url).netloc
    cleanDomainName = domain_name.replace(":","_")
    topLevelPath = Path().resolve()
    Path(f"{topLevelPath}/{cleanDomainName}").mkdir(parents=True, exist_ok=True)
    print(f"created folder at: {topLevelPath}/{cleanDomainName}/")
    return (f"{topLevelPath}/{cleanDomainName}/")

def saveUrls ():
    # args
    url = entry_url.get()
    if not is_valid(url):
        label_invalid_url = tk.Label(root, text='Invalid URL', anchor="e")
        label_invalid_url.config(font=('helvetica', 10))
        canvas1.create_window(450, 290, window=label_invalid_url)
        return
    max_urls = int(entry_max_urls.get())
    load_delay = float(entry_page_delay.get())
    # https://note.nkmk.me/en/list/
    
    crawl(url, max_urls, load_delay)

    print("[+] Total Internal links:", len(internal_urls))
    print("[+] Total External links:", len(external_urls))
    print("[+] Total URLs:", len(external_urls) + len(internal_urls))
    print("[+] Total crawled URLs:", max_urls)

    internal_urls_sorted = sorted(internal_urls)
    external_urls_sorted = sorted(external_urls)

    domain_name = urlparse(url).netloc
    cleanPath = createCleanFolderFromUrl(url)

    # save the internal links to a file
    with open(f"{cleanPath}/internal_links.txt", "w") as f:
        for internal_link in internal_urls_sorted:
            print(internal_link.strip(), file=f)

    # save the external links to a file
    with open(f"{cleanPath}/external_links.txt", "w") as f:
        for external_link in external_urls_sorted:
            print(external_link.strip(), file=f)

def saveScreenshots ():
    url = entry_url.get()
    if not is_valid(url):
        label_invalid_url = tk.Label(root, text='Invalid URL', anchor="e")
        label_invalid_url.config(font=('helvetica', 10))
        canvas1.create_window(450, 290, window=label_invalid_url)
        return

    maxScreenshots = int(entry_max_screenshots.get())
    waitSecPerPage = float(entry_page_load_delay.get())

    # setup screensave
    chrome_options = Options()
    if var_entry_headless_mode.get() == 1:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument("--window-size=1980x1080") # ANYTHING MORE THAN 3200 width may error
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    # save images of internal links
    screenshotCounter = 1
    cleanPath = createCleanFolderFromUrl(url)
    print(f"saving files to {cleanPath}/")

    internalLinksFile = open(f"{cleanPath}/internal_links.txt", "r")
    internalLinksLines = internalLinksFile.readlines()
    
    for internal_link in internalLinksLines:
        internal_link = internal_link.strip()
        driver.get(internal_link)
        driver.maximize_window()
        time.sleep(waitSecPerPage) # give page time to load
        height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1980,height+80)
        screenshot_util.fullpage_screenshot(driver, f"{cleanPath}/{screenshotCounter:04}.png")
        print(f"Printing screenshot {internal_link.strip()} to {cleanPath}/{screenshotCounter:04}.png")
        if screenshotCounter >= maxScreenshots: break
        screenshotCounter += 1

    internalLinksFile.close()
    driver.quit()

canvas1 = tk.Canvas(root, width = 800, height = 350,  relief = 'raised')
canvas1.pack()

label1 = tk.Label(root, text='Save images from URL')
label1.config(font=('helvetica', 14))
canvas1.create_window(200, 25, window=label1)

# url entry
label_url = tk.Label(root, text='Enter URL:', anchor="e")
label_url.config(font=('helvetica', 10))
canvas1.create_window(250, 70, window=label_url)
entry_url = tk.Entry (root) 
canvas1.create_window(450, 70, window=entry_url)

# delay between each page to collect URLs
label_page_delay = tk.Label(root, text='Delay (sec) collect URLs:', anchor="e")
label_page_delay.config(font=('helvetica', 10))
canvas1.create_window(250, 100, window=label_page_delay)
entry_page_delay = tk.Entry (root)
entry_page_delay.insert(0, '0.05')
canvas1.create_window(450, 100, window=entry_page_delay)

# Number of max URLs to crawl, default is 3
label_max_urls = tk.Label(root, text='Number of max URLs to crawl:', anchor="e")
label_max_urls.config(font=('helvetica', 10))
canvas1.create_window(250, 130, window=label_max_urls)
entry_max_urls = tk.Entry (root)
entry_max_urls.insert(0, '3')
canvas1.create_window(450, 130, window=entry_max_urls)

# Max screenshots
label_max_screenshots = tk.Label(root, text='Max screenshots:', anchor="e")
label_max_screenshots.config(font=('helvetica', 10))
canvas1.create_window(250, 160, window=label_max_screenshots)
entry_max_screenshots = tk.Entry (root)
entry_max_screenshots.insert(0, '1')
canvas1.create_window(450, 160, window=entry_max_screenshots)

# wait time (sec) for each page to load
label_page_load_delay = tk.Label(root, text='Wait time (sec) for page load:', anchor="e")
label_page_load_delay.config(font=('helvetica', 10))
canvas1.create_window(250, 190, window=label_page_load_delay)
entry_page_load_delay = tk.Entry (root)
entry_page_load_delay.insert(0, '5')
canvas1.create_window(450, 190, window=entry_page_load_delay)

# headless mode
label_headless_mode = tk.Label(root, text='Headless mode (some sites block headless):', anchor="e")
label_headless_mode.config(font=('helvetica', 10))
canvas1.create_window(250, 220, window=label_headless_mode)
var_entry_headless_mode = tk.IntVar()
entry_headless_mode = tk.Checkbutton(root, text="", variable=var_entry_headless_mode)
canvas1.create_window(430, 220, window=entry_headless_mode)

button1 = tk.Button(text='Save URLs', command=saveUrls, bg='brown', fg='white', font=('helvetica', 9, 'bold'))
canvas1.create_window(450, 260, window=button1)
 
button2 = tk.Button(text='Save screenshots', command=saveScreenshots, bg='brown', fg='white', font=('helvetica', 9, 'bold'))
canvas1.create_window(450, 290, window=button2)

root.mainloop()