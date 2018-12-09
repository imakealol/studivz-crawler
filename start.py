import getpass
from Crawler import Crawler


if __name__ == '__main__':
    defaultPlatform = 'studivz'

    platform = input("Welche Plattform? studivz/meinvz ("+defaultPlatform+"): ") or defaultPlatform
    username = input("E-Mail: ")
    password = getpass.getpass("Passwort: ")

    crawler = Crawler(username, password, platform)

    if crawler.logged_in:
        if input("'Meine Seite' sichern? Y/n (Y) ") != 'n':
            crawler.save_profile()
        if input("'Pinnwand' crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_board()
        if input("'Nachrichten' crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_messages()
        if input("'Freunde' crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_friends()
        if input("Pinnwand der Freunde crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_friends_pinboard()
        if input("'Eigene Fotos' crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_own_albums()
        if input("'Meine Verlinkungen' crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_linked_photos()
        if input("Zugehörige Alben crawlen? Y/n (Y) ") != 'n':
            crawler.crawl_linked_albums()

    crawler.browser.quit()
    print('Finished with %i errors' % (crawler.errors))
