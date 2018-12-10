# studivz-crawler
I was sadly watching studiVZ fading away ... the social network of my early student days.  
Therefore I decided to save all my memories with a CLI.

studivz-crawler downloads all your text-memories as json-files + your photos as jpg.  
**Text information as json**: "Meine Seite", "Pinnwand", "Nachrichten", "Meine Freunde" + their "Pinnwand"  
**Photos**: "Meine Fotos", "Meine Verlinkungen" + related albums  

## Installation
**chromedriver**  
MacOS: `brew cask install chromedriver`  
Others: [Download chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)

**python dependencies**  
`pip install -q -r requirements.txt`

## Start CLI
`python start.py`

## Notes
- Python 3.4+
- studiVZ limits user actions to ~4000/day. So be prepared to be blocked after a while and continue crawling the next day.
