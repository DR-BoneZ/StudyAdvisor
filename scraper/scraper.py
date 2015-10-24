import sys
import requests
import urllib
import re
import mysql.connector
from alchemyapi import AlchemyAPI


cur = None
alchemyapi = AlchemyAPI()
concepts_interned = []


def connect(start_term):
    """ Add all urls from urls_interned list to mySQL database """
    try:
        conn = mysql.connector.connect(host='localhost', database='study', user='root', password='password')
        if not (conn.is_connected()):
            print('Could not connect to MySQL database')
            exit()
        global cur
        cur = conn.cursor()
        intern_concept(start_term)
        conn.commit()
    except mysql.connector.Error as e:
        print(e)
        exit()
    else:
        conn.close()

def commit_urls(urls):
    global cur
    for url in urls:
        print(url)
        cur.execute('INSERT INTO sites (url, visits) SELECT \''+url+'\', 1000 FROM DUAL WHERE NOT EXISTS (SELECT url FROM sites WHERE url=\''+url+'\') LIMIT 1;')

def get_alchemy_concepts(url):
    """ TODO """
    response = alchemyapi.concepts('url', url)
    if response['status'] != 'OK': return None
    return response['concepts']

def google_urls(term):
    """ return list of urls returned by google search """
    url = ('https://www.google.com/search?q=%s' % urllib.quote_plus(term))
    print('Scraping from url:  '+url)
    html = requests.get(url).content
    print('Response size: '+str(len(html)))
    regex = re.compile('(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')
    return regex.findall(html)

def intern_concept(concepttext):
    """ main recursive function """
    global concepts_interned
    concepts_interned.append(concepttext)
    urls = google_urls(concepttext)
    commit_urls(urls)
    if(len(urls)!=0):
        print('URLs: urls')
        concepts = get_alchemy_concepts(urls[0])
        for concept in concepts:
            print('Checking concept: '+str(concept['text']))
            if str(concept['text']) not in concepts_interned:
                intern_concept(str(concept['text']))
                break
            else:
                print(str(concept['text'])+' is already in concepts_interned')
    else:
        print('urls is empty')


if __name__ == "__main__":
    """ Main Routine """
    global concepts_interned
    start_term = sys.argv[1]
    connect(start_term)
    print(concepts_interned)

