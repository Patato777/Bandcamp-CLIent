import requests,os,demjson,importlib,selenium.webdriver,time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.support import expected_conditions as EC

with open('../resources/config','r') as config :
    conf = eval(config.read())
    MUSICPATH = conf['MUSICPATH']
    BROWSER = conf['BROWSER']
    COUNTRY = conf['COUNTRY']
    ZIP = conf['ZIP']
    EMAIL = conf['EMAIL']

Browser = getattr(selenium.webdriver,BROWSER)
Options = eval('selenium.webdriver.%s.options.Options'%(BROWSER.lower()))

def zulu(tracks,path) :
    if not os.path.exists(path) :
        os.mkdir(path)
    os.chdir(path)
    for track in tracks :
        save(track.info["file"]["mp3-128"],track.info["title"]+'.mp3')
        
def albzulu(album) :
    path = os.path.join(MUSICPATH, album.info["artist"],album.info["current"]["title"])
    zulu(album.tracks,path)
    
def trzulu(track) :
    path = os.path.join(MUSICPATH, track.info["artist"])
    zulu([track],path)
    
def openbrowser(url) :
    options = Options()
    options.headless = True
    browser = Browser(options=options)
    browser.get(url)
    return browser

def free_download(url,encoding) :
    browser = openbrowser(url)
    #print('Got that page')
    browser.find_element_by_class_name('item-format').click()
    fselect = browser.find_element_by_xpath("//ul[@class='formats']\
                                            //span[contains(\
                                                            translate(text(),\
                                                                     'ABCDEFGHIJKLMNOPQRSTUVWXYZ',\
                                                                     'abcdefghijklmnopqrstuvwxyz'),\
                                                            '%s')]"%(encoding))
    fselect.click()
    #print('Encoding selected')
    dlbtn = WebDriverWait(browser,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.item-button')))
    #print('Got the URL of the file')
    info = demjson.decode(browser.find_element_by_css_selector('body div').get_attribute('data-blob'))['download_items'][0]
    path = os.path.join(MUSICPATH,info["artist"])
    if not os.path.exists(path) :
        os.mkdir(path)
    os.chdir(path)
    #print('To download')
    if info["type"] == 'album' :
        ext = '.zip'
    else :
        ext = '.'+encoding.split()[0]
    browser.quit()
    save(dlbtn.get_attribute('href'),info['title']+'.zip')
    #TODO: unzip
    
def mail_download(tralbum) :
    #mail = tralbum.info['current']['title'].replace(' ','-')+'@ahem.email'
    browser = openbrowser(tralbum.info['url'])
    browser.find_element_by_css_selector('button.download-link').click()
    browser.find_element_by_css_selector('input#userPrice').send_keys('0')
    browser.find_element_by_css_selector('div.payment-nag-continue > a').click()
    browser.find_element_by_css_selector('input#fan_email_address').send_keys(EMAIL)
    Select(browser.find_element_by_css_selector('select#fan_email_country')).select_by_value(COUNTRY)
    browser.find_element_by_css_selector('input#fan_email_postalcode').send_keys(ZIP)
    browser.find_element_by_css_selector('div#downloadButtons_email').click()
    browser.quit()
    #get_email(mail)

#def get_email(mail) :
#    tokenjson = requests.post('https://www.ahem.email/api/auth/token').json()
#    if tokenjson['success'] :
#        token = tokenjson['token']
#    else :
#        raise requests.ConnectionError(tokenjson['message'])
#    header = {'Authorization': 'Bearer '+token}
#    time.sleep(10)
#    mailbox = requests.get(f'https://www.ahem.email/api/mailbox/{mail}/email',headers=header).json()
#    email = requests.get(f'https://www.ahem.email/api/mailbox/{mail}/email/{mailbox[0]["emailId"]}',headers=header)
#    requests.delete(email.url)
#    emailjson = email.json()
    
def save(url,name) :
    file = requests.get(url)
    file.raise_for_status()
    #print('Downloading...',url)
    with open((name),'wb') as f:
        f.write(file.content)
