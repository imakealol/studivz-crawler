import sys, time, os, re, json, hashlib
from urllib import request
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime


platforms = {
    'studivz': {
        'id': 'studivz',
        'name': 'studiVZ',
        'baseurl': 'https://www.studivz.net',
    },
    'meinvz': {
        'id': 'meinvz',
        'name': 'meinVZ',
        'baseurl': 'https://www.meinvz.net',
    }
}

download_folder = './downloads'
headless_browser = False


class Crawler():
    page = 0
    photo_links = {}
    page_links = {}
    platform = {}
    user_id = ''
    errors = 0
    logged_in = False

    def __init__(self, username, password, platform):
        self.username = username.lower()
        self.password = password
        self.platform = platforms[platform] if hasattr(platforms, platform) else platforms['studivz']

        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        options = webdriver.ChromeOptions()
        if headless_browser:
            options.add_argument('headless')
        self.browser = webdriver.Chrome(chrome_options=options)
        self.browser.set_page_load_timeout(45)

        self.browser.get(self.platform['baseurl'])
        self._login()

    def _login(self):
        try:
            mainMenu = self.browser.find_element_by_css_selector('#Grid-Navigation-Main')
            print("Already Logged In!")
        except:
            self.browser.get(self.platform['baseurl']+'/Login')
            username = self.browser.find_element_by_css_selector("#Login_email").send_keys(self.username)
            password = self.browser.find_element_by_css_selector("#Login_password").send_keys(self.password)
            loginBtn = self.browser.find_element_by_css_selector('.form-buttons input[type="submit"]')
            time.sleep(0.2)
            try:
                loginBtn.send_keys(u'\ue007')
            except:
                pass
            self.browser.get(self.platform['baseurl']+'/Home')
            try:
                self.user_id = self._get_user_id()
                self.logged_in = True

                try:
                    with open(download_folder+"/accounts.json", "r+") as account_file:
                        accounts = json.load(account_file)
                except:
                    accounts = []

                account = {
                    'email': self.username,
                    'password': hashlib.sha256(self.password.encode('utf-8')).hexdigest()
                }
                if not account in accounts:
                    accounts.append(account)
                    save_json(accounts, 'accounts')

                print("Logged In! (ID: {})".format(self.user_id))
            except:
                self.logged_in = False
                self.browser.quit()
                print("Login failed!")

    def _get_user_id(self):
        profile_url = self.browser.find_element_by_css_selector('#Grid-Navigation-Main li a[title="Meine Seite"]').get_attribute('href')
        user_id = profile_url.replace(self.platform['baseurl'], "").replace("/Profile/", "").replace("/tid/102", "")
        return user_id

    def crawl_linked_albums(self):
        self.photo_links = {}
        for soup in soup_all_html_in_dir(download_folder+'/'+self.username+'/html/_Album/_Meine Verlinkungen/'):
            album = soup.select_one('table.photo-metainfo td a[href^="/Photos/Album/"]')
            albumName = safe_filename(album.get_text().strip())
            self.photo_links[albumName] = album['href']
        self._crawl_all_photo_links()

    def crawl_own_albums(self):
        self.photo_links = {}
        self._go_to_own_albums()
        albums = self.browser.find_elements_by_css_selector('ul.photoalbums li')
        for album in albums:
            link = album.find_element_by_css_selector('h4 a')
            self.photo_links[safe_filename(link.text)] = link.get_attribute('href')
        self._crawl_all_photo_links(adding_baseurl=False)

    def crawl_linked_photos(self):
        self._go_to_linked_photos()
        self._save_all_photos('_Meine Verlinkungen')

    def save_profile(self):
        self._go_to_profile()
        self._save_all_pages('_Meine Seite')
        self.scrape_profile()

    def crawl_board(self):
        self._go_to_complete_board()
        self._save_all_pages('_Pinnwand')
        self.scrape_board()

    def crawl_messages(self):
        print('Crawling messages: Inbox')
        self._go_to_messages(self._return_start_page('_Nachrichten/Inbox'))
        self._save_all_pages('_Nachrichten/Inbox', clickOn='a[title="lesen"]')
        print('Crawling messages: Sent')
        self._go_to_sent_messages(self._return_start_page('_Nachrichten/Outbox'))
        self._save_all_pages('_Nachrichten/Outbox', clickOn='a[title="lesen"]')
        self.scrape_messages()

    def crawl_friends(self):
        self._go_to_friends()
        self._save_all_pages('_Freunde')
        self.scrape_friends()

    def crawl_friends_pinboard(self):
        with open(download_folder+'/'+self.username+'/friends.json') as friends_file:
            friends = json.load(friends_file)
            for friend in friends:
                startpage = self._return_start_page('_Freunde/_Pinnwand/'+friend['user_id'])
                self.browser.get(self.platform['baseurl']+'/Pinboard/'+friend['user_id']+'/p/'+startpage)
                self._save_all_pages('_Freunde/_Pinnwand/'+friend['user_id'])

    def _return_start_page(self, dir):
        startpage=1
        dir = download_folder+'/'+self.username+'/html/'+dir+'/'
        if os.path.isdir(dir):
            for file in os.listdir(dir):
                if os.path.isfile(dir+file):
                    filename = int(os.path.splitext(file)[0])
                    startpage = filename if filename > startpage else startpage
        return str(startpage)

    def _go_to_profile(self):
        self.browser.get(self.platform['baseurl']+'/Profile/'+self.user_id+'/tid/102')
        print("URL: Profile")

    def _go_to_complete_board(self, startpage=1):
        self.browser.get(self.platform['baseurl']+'/Pinboard/'+self.user_id+'/p/'+str(startpage))
        print("URL: Complete Board")

    def _go_to_photos(self):
        self.browser.get(self.platform['baseurl']+'/Photos/'+self.user_id+'/tid/104')
        print("URL: Photos")

    def _go_to_messages(self, startpage=1):
        self.browser.get(self.platform['baseurl']+'/Messages/Inbox/p/'+str(startpage))
        print("URL: Messages")

    def _go_to_sent_messages(self, startpage=1):
        self.browser.get(self.platform['baseurl']+'/Messages/Outbox/p/'+str(startpage))
        print("URL: Sent Messages")

    def _go_to_linked_photos(self, startpage=1):
        self.browser.get(self.platform['baseurl']+'/Photos/Tags/'+self.user_id+'/'+self.user_id+'/p/'+str(startpage))
        print("URL: Linked Photos")

    def _go_to_own_albums(self, startpage=1):
        self.browser.get(self.platform['baseurl']+'/Photos/Album/'+self.user_id+'/'+self.user_id+'/p/'+str(startpage))
        print("URL: Own Albums")

    def _go_to_friends(self, startpage=1):
        self.browser.get(self.platform['baseurl']+'/Friends/Friends/'+self.user_id+'/p/'+str(startpage))
        print("URL: Friends")

    def _get_photo_links(self, folder):
        self.photo_links = {}
        photo_links = self.browser.find_elements_by_css_selector('ul.photos li .photo a')
        for link in photo_links:
            url = link.get_attribute('href')
            self.photo_links[folder].append(url)

    def _crawl_all_photo_links(self, adding_baseurl=True):
        for name, link in self.photo_links.items():
            self.browser.get((self.platform['baseurl'] if adding_baseurl else '')+link)
            self._save_all_photos(name)

    def _save_all_pages(self, folder, clickOn=False):
        while True:
            pagenumber = re.search(r'/p/\d+$', self.browser.current_url)
            if pagenumber is not None:
                filename = safe_filename(self.browser.current_url.split('/')[-1])
            else:
                filename = safe_filename(self.browser.current_url)
                filename = filename.replace(safe_filename(self.platform['baseurl']), "")

            if not file_exists(filename, folder, self.username):
                if clickOn:
                    clickableItems = self.browser.find_elements_by_css_selector(clickOn)
                    clickableItems.reverse();
                    for item in clickableItems:
                        try:
                            item.click()
                            time.sleep(1)
                        except:
                            print('Couldn\'t click element ('+folder+', '+filename+')')
                            self.errors += 1
                time.sleep(2)
                self._save_source_code(filename, folder)
            url = self._get_next_page_url()
            if url:
                self.browser.get(url)
            else:
                break

    def _save_all_photos(self, folder):
        path, dirs, files = next(os.walk(get_download_path('html', '_Album/'+folder, self.username)))
        file_count = len(files)
        try:
            photo_count = int(self.browser.find_element_by_css_selector('.Snipplet-Photos-Diashow input[name="photoCount"]').get_attribute('value'))
            print('Album (%s): %i/%i' % (folder, file_count, photo_count))
            if file_count < photo_count:
                print('Saving album: {}'.format(folder))
                self.photo_links[folder] = []
                while True:
                    self._get_photo_links(folder)
                    #break
                    url = self._get_next_page_url()
                    if url:
                        self.browser.get(url)
                    else:
                        break
                photo_links = self.photo_links[folder][file_count:]
                for photo_link in photo_links:
                    self._save_photo(photo_link, '_Album/'+folder)
            else:
                print('Skipping album: {}'.format(folder))
        except:
            print('Unknown error for %s' % (folder))
            self.errors += 1

    def _get_next_page_url(self):
        try:
            url = self.browser.find_element_by_css_selector('.obj-pager').find_element_by_link_text('»').get_attribute('href')
        except:
            try:
                url = self.browser.find_element_by_css_selector('.obj-navigation').find_element_by_link_text('»').get_attribute('href')
            except:
                url = False
        return url

    def _save_photo(self, link, subfolder='', img_selector='#photoDetailBig'):
        if not file_exists(safe_filename(link), subfolder, self.username):
            self.browser.get(link)
            url = self.browser.find_element_by_css_selector(img_selector).get_attribute('src')
            filename = safe_filename(link)
            filename = filename.replace((safe_filename(self.platform['baseurl'])+"PhotosView"), "")
            filename = filename.replace((safe_filename(self.platform['baseurl'])+"PhotosTags"), "")
            filename = filename+'.jpg'

            self._save_source_code(filename, subfolder)

            try:
                request.urlretrieve(url, get_download_path('photos',subfolder, self.username)+filename)
            except:
                 pass

    def _save_source_code(self, filename, subfolder=''):
        file = open(get_download_path('html',subfolder, self.username)+os.path.splitext(filename)[0]+'.html',"w+")
        file.write(self.browser.page_source)
        file.close()

    def scrape_messages(self):
        self.scrape_box('Inbox')
        self.scrape_box('Outbox')

    def scrape_box(self, box='Inbox'):
        output = []
        for soup in soup_all_html_in_dir(download_folder+'/'+self.username+'/html/_Nachrichten/'+box+'/'):
            messages = soup.select('.messages-list-content > div')
            for message in messages:
                user_id = []
                name_link = message.select_one('.messageListContent .fromName')
                time_tag = name_link.small.extract()
                name = name_link.get_text().strip()
                try:
                    user_id.append(name_link.select_one('a')['href'].replace('/Profile/',''))
                except:
                    if(name == 'Gelöschte Person'):
                        user_id.append('')
                    if(name == 'Rundschreiben'):
                        names_tag = message.select_one('.body > div > div:nth-of-type(1)')
                        for user in names_tag.select('a'):
                            user_id.append(user['href'].replace('/Profile/',''))
                        for deleted_user in range(names_tag.get_text().strip().count('Gelöschte Person')):
                            user_id.append('')

                time = datetime.strptime(time_tag.get_text().strip(), '%d.%m.%Y um %H:%M Uhr')
                subject = message.select_one('.messageListContent .subject a').get_text().strip()
                try:
                    text_body = message.select_one('.messageListContent .body .body_text')
                    text = text_body.get_text().strip()
                    html = str(text_body).replace('<div class="body_text">', '')[:-6].strip()
                except:
                    text = ''
                    html = ''

                output.append({
                    'name' : name,
                    'user_id' : user_id,
                    'time' : time.strftime('%Y/%m/%d %T'),
                    'subject' : subject,
                    'text' : text,
                    'html' : html
                })
        save_json(output, 'messages_'+box.lower(), self.username)

    def scrape_board(self):
        output = []
        for soup in soup_all_html_in_dir(download_folder+'/'+self.username+'/html/_Pinnwand/'):
            messages = soup.select('ul.obj-comment-list li')
            for message in messages:
                if not message.has_attr('id'):
                    name = message.select_one('.comment .comment-metainfo .profile').get_text().strip()
                    user_id = message.select_one('.comment .comment-metainfo input[name="ownerId"]')
                    user_id = user_id['value']
                    time = message.select_one('.comment .comment-metainfo .datetime').get_text().strip()
                    time = datetime.strptime(time, 'am %d.%m.%Y um %H:%M Uhr')
                    text_body = message.select_one('.comment .pinboard-entry-text')
                    text = text_body.get_text().strip()
                    html = str(text_body).replace('<div class="pinboard-entry-text">', '').replace('<div class="pinboard-entry-text notparsed">', '')[:-6].strip()

                    if name != 'Lea (VZ-Moderatorin)':
                        output.append({
                            'name' : name,
                            'user_id' : user_id,
                            'time' : time.strftime('%Y/%m/%d %T'),
                            'text' : text,
                            'html' : html
                        })
        save_json(output, 'pinboard', self.username)

    def scrape_profile(self):
        for soup in soup_all_html_in_dir(download_folder+'/'+self.username+'/html/_Meine Seite/'):
            user_id = soup.select_one('#Grid-Navigation-Main li a[title="Meine Seite"]')['href']
            user_id = user_id.replace(self.platform['baseurl'], "").replace("/Profile/", "").replace("/tid/102", "")

            account = soup.select_one('#Mod-Profile-Information-Account')
            general = soup.select_one('#Mod-Profile-Information-General')
            former = soup.select_one('#Mod-Profile-Information-Former')
            contact = soup.select_one('#Mod-Profile-Information-Contact')
            personal = soup.select_one('#Mod-Profile-Information-Personal')
            work = soup.select_one('#Mod-Profile-Information-Work')

            member_since = account.select('dd:nth-of-type(3)')[0].get_text().strip()
            member_since = datetime.strptime(member_since, '%d.%m.%Y')

            last_update = account.select('dd:nth-of-type(4)')[0].get_text().strip()
            last_update = datetime.strptime(last_update, '%d.%m.%Y')

            general.select('dd:nth-of-type(5)')[0].a.extract()
            dob = ' '.join(general.select('dd:nth-of-type(5)')[0].get_text().split())
            dob = datetime.strptime(dob[0:10], '%d.%m.%Y')

            info = {
                'account' : {
                    'user_id' : user_id,
                    'name' : soup.find("meta", attrs={"property": "og:title"})['content'],
                    'image' : soup.select_one("#profileImage")['src'],
                    'member_since' : member_since.strftime('%Y/%m/%d'),
                    'last_update' : last_update.strftime('%Y/%m/%d'),
                },
                'general' : {
                    'university' : ' '.join(general.select('dd:nth-of-type(1)')[0].get_text().split()),
                    'status' : general.select('dd:nth-of-type(2)')[0].get_text().strip(),
                    'course' : general.select('dd:nth-of-type(3)')[0].get_text().strip(),
                    'gender' : general.select('dd:nth-of-type(4)')[0].get_text().strip(),
                    'dob' : dob.strftime('%Y/%m/%d'),
                },
                'former' : {
                    'last_school' : former.select('dd:nth-of-type(1)')[0].get_text().strip(),
                },
                'contact' : {
                    'icq' : contact.select('dd:nth-of-type(1)')[0].get_text().strip(),
                },
                'personal' : {
                    'looking_for' : ' '.join(personal.select('dd:nth-of-type(1)')[0].get_text().split()),
                    'politics' : personal.select('dd:nth-of-type(2)')[0].get_text().strip(),
                    'interests' : personal.select('dd:nth-of-type(3)')[0].get_text().strip(),
                    'memberships' : personal.select('dd:nth-of-type(4)')[0].get_text().strip(),
                    'music' : personal.select('dd:nth-of-type(5)')[0].get_text().strip(),
                    'books' : personal.select('dd:nth-of-type(6)')[0].get_text().strip(),
                    'movies' : personal.select('dd:nth-of-type(7)')[0].get_text().strip(),
                },
                'work' : {
                    'job_type' : work.select('dd:nth-of-type(1)')[0].get_text().strip(),
                    'position' : work.select('dd:nth-of-type(2)')[0].get_text().strip(),
                    'activity' : work.select('dd:nth-of-type(3)')[0].get_text().strip(),
                    'former' : work.select('dd:nth-of-type(4)')[0].get_text().strip(),
                }
            }

            groups = []
            for group in soup.select('#Mod-Groups-Snipplet li'):
                groups.append({
                    'id' : group.select_one('a')['href'].replace('/Groups/Overview/',''),
                    'name' : group.select_one('a').get_text().strip(),
                })

            courses = []
            for course in soup.select('#Mod-Education-Snipplet li'):
                courses.append({
                    'id' : course.select_one('a')['href'].replace('/Education/InMyCourse/',''),
                    'name' : course.select_one('a').get_text().strip(),
                    'semester' : ' '.join(course.select_one('span').get_text().split()),
                })

            output = {
                'info' : info,
                'groups': groups,
                'courses' : courses,
            }

            save_json(output, 'profile', self.username)

    def scrape_friends(self):
        output = []
        for soup in soup_all_html_in_dir(download_folder+'/'+self.username+'/html/_Freunde/'):
            friends = soup.select('.obj-usertable tbody tr')
            for friend in friends:
                if not friend.has_attr('id'):
                    image = friend.select_one('.image img')['src']
                    platform = friend.select_one('.name dd.platform img')['alt'].lower()
                    name = friend.select_one('.name dd.name a').get_text().strip()
                    user_id = friend.select_one('.name dd.name a')['href'].replace('/Profile/', '')
                    last_update = friend.select_one('.name span.lastUpdate').get_text().strip()
                    last_update = datetime.strptime(last_update, '%d.%m.%Y')
                    last_updated = friend.select_one('.name span.lastUpdateTypeName').get_text().strip()

                    friend_object = {
                        'name' : name,
                        'user_id' : user_id,
                        'platform' : platform,
                        'image' : image,
                        'last_update' : last_update.strftime('%Y/%m/%d'),
                        'last_updated' : last_updated
                    }

                    if platform == 'studivz':
                        friend_object['university'] = friend.select_one('.name dd.network a').get_text().strip()
                    else:
                        friend_object['region'] = friend.select_one('.name dd.network a').get_text().strip()

                    output.append(friend_object)

        save_json(output, 'friends', self.username)




def get_download_path(folder, subfolder='', username=''):
    basedir = download_folder+'/'+username+'/'+folder+'/'
    if subfolder != '':
        subfolder = subfolder+'/'
    if not os.path.exists(basedir+subfolder):
        os.makedirs(basedir+subfolder)
    return basedir+subfolder

def safe_filename(string):
    return "".join([c for c in string if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def get_file_content(path):
    file = open(path, "r")
    content = file.read()
    file.close()
    return content

def file_exists(link, folder='', username=''):
    path = get_download_path('html', folder, username)+safe_filename(link)+'.html'
    return os.path.isfile(path)

def save_json(output, filename, username=False):
    if type(output) is list and len(output)>0 and 'time' in output[0]:
        output.sort(key=lambda x: x['time'], reverse=True)
    with open(download_folder+'/'+(username+'/' if username else '')+filename+'.json', 'w+') as file:
        json.dump(output, file, ensure_ascii=False, indent=2, sort_keys=True)

def soup_all_html_in_dir(dir):
    output = []
    if os.path.isdir(dir):
        for file in os.listdir(dir):
            if os.path.isfile(dir+file):
                output.append(BeautifulSoup(get_file_content(dir+file), "html.parser"))
    return output
