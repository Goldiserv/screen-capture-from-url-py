import tkinter as tk
from tkinter import ttk
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
import webbrowser

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
                printMsg(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        printMsg(f"{GREEN}[*] Internal link: {href}{RESET}")
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
    printMsg(f"{YELLOW}[*] Crawling: {url}{RESET}")
    links = get_all_website_links(url)
    for link in links:
        time.sleep(load_delay)
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)

def createCleanFolderFromUrl(url):
    printMsg(url)
    domain_name = urlparse(url).netloc
    cleanDomainName = domain_name.replace(":","_")
    topLevelPath = Path().resolve()
    Path(f"{topLevelPath}/{cleanDomainName}").mkdir(parents=True, exist_ok=True)
    printMsg(f"created folder at: {topLevelPath}/{cleanDomainName}/")
    return (f"{topLevelPath}/{cleanDomainName}/")

def printMsg(*args):
    text2.insert(tk.END, "".join(map(str,args)) + "\n")
    text2.see(tk.END)
    print("".join(map(str,args)))

def saveUrls ():
    # args
    url = entry_url.get()
    if not is_valid(url):
        printMsg("Invalid URL. URLs must begin with http or https")
        return
    max_urls = int(entry_max_urls.get())
    load_delay = float(entry_page_delay.get())
    # https://note.nkmk.me/en/list/
    
    crawl(url, max_urls, load_delay)

    printMsg("[+] Total Internal links:", len(internal_urls))
    printMsg("[+] Total External links:", len(external_urls))
    printMsg("[+] Total URLs:", len(external_urls) + len(internal_urls))
    printMsg("[+] Total crawled URLs:", max_urls)

    internal_urls_sorted = sorted(internal_urls)
    external_urls_sorted = sorted(external_urls)

    cleanPath = createCleanFolderFromUrl(url)

    # save the internal links to a file
    with open(f"{cleanPath}/internal_links.txt", "w") as f:
        for internal_link in internal_urls_sorted:
            printMsg(internal_link.strip(), file=f)

    # save the external links to a file
    with open(f"{cleanPath}/external_links.txt", "w") as f:
        for external_link in external_urls_sorted:
            printMsg(external_link.strip(), file=f)

def saveScreenshots ():
    url = entry_url.get()
    if not is_valid(url):
        printMsg("Invalid URL. URLs must begin with http or https")
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
    printMsg(f"saving files to {cleanPath}/")

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
        printMsg(f"Printing screenshot {internal_link.strip()} to {cleanPath}/{screenshotCounter:04}.png")
        if screenshotCounter >= maxScreenshots: break
        screenshotCounter += 1

    internalLinksFile.close()
    driver.quit()

labelCurrentY = 1
def addUiInput(labelText, inputWidth=10):
    global labelCurrentY
    label = tk.Label(root, text=labelText, font=('helvetica', 10), bd=1, justify="right")
    label.grid(row=labelCurrentY, column=1, padx=(40, 10), pady=5)
    entryField = tk.Entry (root, width=inputWidth, justify="left")
    entryField.grid(row=labelCurrentY, column=2, padx=(10, 10))
    labelCurrentY += 1
    return entryField

def addUiCheckbox(labelText, varCheckbox):
    global labelCurrentY
    label = tk.Label(root, text=labelText, font=('helvetica', 10), bd=1, justify="right")
    label.grid(row=labelCurrentY, column=1, padx=(40, 10), pady=5)
    entryField = tk.Checkbutton(root, text="", variable=varCheckbox, justify="left")
    entryField.grid(row=labelCurrentY, column=2, padx=(10, 10))
    labelCurrentY += 1
    return entryField

root= tk.Tk()
root.title('Screen capture all links in URL app')
root.geometry('750x600')

# Title 1
label1 = tk.Label(root, text='Save all sub-page links to a file', font=('helvetica', 14))
label1.grid(row=labelCurrentY, column=1, padx=(10, 10), pady=5)
labelCurrentY += 1

# url entry
entry_url = addUiInput('Enter URL:', 30)

# delay between each page to collect URLs
entry_page_delay = addUiInput('Delay (sec) collect URLs:')
entry_page_delay.insert(0, '0.05') # set default

# Number of max URLs to crawl, default is 3
entry_max_urls = addUiInput('Number of max URLs to crawl:')
entry_max_urls.insert(0, '3') # set default

# control button 1
buttonSaveUrls = tk.Button(text='Save URLs', command=saveUrls, bg='brown', fg='white', font=('helvetica', 9, 'bold'))
buttonSaveUrls.grid(row=labelCurrentY, column=2, padx=(10, 10), pady=5)
labelCurrentY += 1

sep = ttk.Separator(root,orient='horizontal').grid(row=labelCurrentY, columnspan=3, sticky="ew",pady=5)
labelCurrentY += 1

label2 = tk.Label(root, text='Save screenshots from file generated', font=('helvetica', 14))
label2.grid(row=labelCurrentY, column=1, padx=(10, 10), pady=5)
labelCurrentY += 1

# Max screenshots
entry_max_screenshots = addUiInput('Max screenshots (enter 999 if not testing):')
entry_max_screenshots.insert(0, '1')

# wait time (sec) for each page to load
entry_page_load_delay = addUiInput('Wait seconds for page load before screenshot:')
entry_page_load_delay.insert(0, '5')

# headless mode
var_entry_headless_mode = tk.IntVar()
entry_headless_mode = addUiCheckbox('Headless mode (some sites block headless):', var_entry_headless_mode)

# control button 2
buttonSaveScreenshots = tk.Button(text='Save screenshots', command=saveScreenshots, bg='brown', fg='white', font=('helvetica', 9, 'bold'))
buttonSaveScreenshots.grid(row=labelCurrentY, column=2, padx=(10, 10), pady=5)
labelCurrentY += 1

# Title Msgbox
label1 = tk.Label(root, text='Messages', font=('helvetica', 12), justify="left")
label1.grid(row=labelCurrentY, column=1, padx=(10, 10), pady=5, sticky="E")
labelCurrentY += 1
text2 = tk.Text(root, height=8)
scroll = tk.Scrollbar(root, command=text2.yview)
text2['yscrollcommand'] = scroll.set
text2.grid(rowspan=1, columnspan=3, padx=(10, 10), pady=5)
scroll.grid(row=labelCurrentY, rowspan=1, column=4, sticky='nsew')
labelCurrentY += 1

def clearMsgs():
    text2.delete(1.0, tk.END)

# clear msg button 1
buttonClearMsgs = tk.Button(text='Clear messages', command=clearMsgs, bg='brown', fg='white', font=('helvetica', 9, 'bold'))
buttonClearMsgs.grid(row=labelCurrentY, column=2, padx=(10, 10), pady=5)
labelCurrentY += 1

def callback(url):
    webbrowser.open_new(url)
    
# Footer
labelFooter = tk.Label(root, text='Licence and support for screen-capture-from-url-py v1.01', fg="blue", cursor="hand2", font=('helvetica', 10), justify="left")
labelFooter.grid(row=labelCurrentY, column=1, padx=(10, 10), pady=5, sticky="E")
labelFooter.bind("<Button-1>", lambda e: callback("https://github.com/Goldiserv/screen-capture-from-url-py"))
labelCurrentY += 1

root.mainloop()