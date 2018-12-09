# studivz
I was sadly watching studivz fading away ... So I decided to rescue all my memories with a CLI.

## Possibilities
This Crawler lets you download all your text-memories as json-files + your photos.

### Text as json
- "Meine Seite"
- "Pinnwand"
- "Nachrichten"
- "Meine Freunde"
  - Their "Pinnwand"
### Photos
- "Meine Fotos"
- "Meine Verlinkungen"
  - Related albums

## 1. Installing chromedriver
MacOS: `brew cask install chromedriver`
Others: https://sites.google.com/a/chromium.org/chromedriver/downloads

## 2. Installung dependencies
`pip install -q -r requirements.txt`

## 3. Start CLI
`python start.py`




### TODO (german):
- 2.+ Kommentar-Seite zu einzelnen Fotos speichern
- json-Dateien zu Alben (Foto-ID + Foto-Infos + Kommentare)
- json-Dateien zu Verlinkungen (Foto-ID + Foto-Infos + Kommentare)
- Profile von Freunden crawlen um eigene Pinnwand-Einträge zu erhalten

- scrape_profile currently only tested with studivz (meinvz to be done)
