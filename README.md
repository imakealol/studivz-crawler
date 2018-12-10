# studivz
I was sadly watching studivz fading away ... So I decided to rescue all my memories with a CLI.

This Crawler lets you download all your text-memories as json-files + your photos.
**Text information as json**: "Meine Seite", "Pinnwand", "Nachrichten", "Meine Freunde" + their "Pinnwand"
**Photos**: "Meine Fotos", "Meine Verlinkungen" + related albums

## Installation
**chromedirver**
MacOS: `brew cask install chromedriver`
Others: [Download chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)

**python dependencies**
`pip install -q -r requirements.txt`

## Start CLI
`python start.py`

## Notes
- Python 3.4+
- studiVZ limits user actions to ~4000/day. So be prepared to be blocked after a while and continue crawling the next day.
