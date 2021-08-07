#!/usr/bin/env python#!/usr/bin/python
# coding: utf-8

# # Immoscout24.de Scraper
# 
# Ein Script zum dumpen (in `.csv` schreiben) von Immobilien, welche auf [immoscout24.de](http://immoscout24.de) angeboten werden

# In[1]:


from bs4 import BeautifulSoup
import json
import urllib.request as urllib2
import random
from random import choice
import time
from datetime import datetime
import re 


# In[2]:


# urlquery from Achim Tack. Thank you!
# https://github.com/ATack/GoogleTrafficParser/blob/master/google_traffic_parser.py
def urlquery(url):
    # function cycles randomly through different user agents and time intervals to simulate more natural queries
    try:
        sleeptime = float(random.randint(5,10))/5
        time.sleep(sleeptime)

        agents = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17',
        'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
        'Opera/12.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.02',
        'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Mozilla/3.0',
        'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3',
        'Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3',
        'Opera/9.00 (Windows NT 5.1; U; en)']

        agent = choice(agents)
        opener = urllib2.build_opener()

        opener.addheaders = [('User-agent', agent)]
        html = opener.open(url).read()
        time.sleep(sleeptime)
        
        return html

    except Exception as e:
        print('Something went wrong with Crawling:\n%s' % e)



# In[5]:
def switch_wohnungsgroesse(groesse):
    switcher = {
        '0 - 40m²': 40,
        "40 - 60m²": 60,
        "60 - 80m²": 80,
        "80 - 100m²": 100,
        "100 - 120m²": 120,
        "mehr als 120m²": 121,
        }
    return switcher.get(groesse, 0)

def switch_tablepic(groesse):
    switcher = {
        '0 - 40m²': True,
        "40 - 60m²": True,
        "60 - 80m²": True,
        "80 - 100m²": True,
        "100 - 120m²": True,
        "mehr als 120m²": True,
        }
    return switcher.get(groesse, False)

def switch_table_linepic(groesse):
    switcher = {
        '0 - 40m²': True,
        "40 - 60m²": True,
        "60 - 80m²": True,
        "80 - 100m²": True,
        "100 - 120m²": True,
        "mehr als 120m²": True,
        }
    return switcher.get(groesse, False)



# In[]:


mietSpiegel = {}


# See immoscout24.de URL in Browser!
b = 'Flensburg' # Bundesland
s = 'Flensburg' # Stadt

date_count = datetime.strftime(datetime.now(), '%Y.%m.%d')

page = 0
print('Suche Mietspiegel in %s / %s' % (b, s) )

url = 'https://www.miete-aktuell.de/mietspiegel/%s/%s/' % (b, s)
soup = BeautifulSoup(urlquery(url), 'html.parser')
#def only_cities(href):
#    return re.compile("/%s/%s/" %(b,s)).search(href)
suchtext = re.compile(r'Ortsteile:',re.IGNORECASE)
foundtext = soup.find('h2',text=suchtext)
ortsteile_table = foundtext.findNext('table')
ortsteile_rows = ortsteile_table.findAll('a', href=re.compile("/%s/%s/." %(b,s)), title=True) 

index = 1
for ortsteil in ortsteile_rows: 
    
    print('Der Mietspiegel für %s wrid ermittelt' % (ortsteil.text.strip()))
    city_crawler_url = 'https://www.miete-aktuell.de%s' % (ortsteil['href'])
    city_soup = BeautifulSoup(urlquery(city_crawler_url), 'html.parser')
    
    
    #Findet PLZs
    suchtext = re.compile(r'Mietpreisentwicklung ',re.IGNORECASE)
    foundtext = city_soup.find('h2',text=suchtext) # Find the first <p> tag with the search text
    plz_table = foundtext.findNext('table').findNext('table')
    plz_rows = plz_table.findAll('tr')
    plz_col = plz_rows[4].findAll('td')
    plz_input = plz_col[1].text.split(",")
    

    #Gräbt sich durch die Tabelle der Kaltmiete und nebenkosten
    suchtext = re.compile(r'Mietpreise nach ',re.IGNORECASE)
    foundtext = city_soup.find('h2',text=suchtext) # Find the first <p> tag with the search text
    
    kaltmiete_table = foundtext.findNext('table')
    kaltmiete_rows = kaltmiete_table.findAll('tr')
    
    nebenkosten_table = kaltmiete_table.findNext('table')
    nebenkosten_rows = nebenkosten_table.findAll('tr')
    
    for plz in plz_input[:-1]:
        print(plz)
        
        for idx, tr in enumerate(kaltmiete_rows):
            cols = tr.findAll('td')
            if switch_tablepic(cols[0].text):
                mietSpiegelInfo = {}
                mietSpiegelInfo["index"] = index
                mietSpiegelInfo["plz"] = plz.strip()
                mietSpiegelInfo["bezugsdatum"] = date_count
                mietSpiegelInfo["bundesland"] = b
                mietSpiegelInfo['stadt'] = s
                mietSpiegelInfo["stadtteil"] = ortsteil.text.strip() #strip soll leerzeichen entfernen
                mietSpiegelInfo["livingspace"] = switch_wohnungsgroesse(cols[0].text) 
                mietSpiegelInfo["kaltmiete euro/qm"] = cols[2].text
                n_cols = nebenkosten_rows[idx].findAll('td')
                mietSpiegelInfo["nebenkosten euro/qm"] = n_cols[2].text
                #warm = cols[2].text.split()
                #mietSpiegelInfo["warmmiete euro/qm"] = n_cols[2].text
                
                index +=1
                mietSpiegel[mietSpiegelInfo["index"]] = mietSpiegelInfo
            

        

   
           


    
# In[6]:


print("Scraped %i Immos" % len(mietSpiegel))


# ## Datenaufbereitung & Cleaning
# 
# Die gesammelten Daten werden in ein sauberes Datenformat konvertiert, welches z.B. auch mit Excel gelesen werden kann. Weiterhin werden die Ergebnisse pseudonymisiert, d.h. die Anbieter bekommen eindeutige Nummern statt Klarnamen.

# In[7]:

import pandas as pd
from datetime import datetime
timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d')

df = pd.DataFrame(mietSpiegel).T
df.index.name = 'id'

#len(df) glaube der macht nichts
df.head()


# ## Alles Dumpen

# In[14]:

f = open('%s-%s-%s-Mietspiegel.csv' % (timestamp, b, s), 'w', encoding= 'utf-8')
f.write('# %s %s from Mietspiegel on %s\n' % (b,s,timestamp))
#df[(df['Haus/Wohnung']==k) & (df['Miete/Kauf']==w)].to_csv(f, encoding='utf-8')
f.close()


# In[15]:

print("Excel wird erstellt")
df.to_excel('%s-%s-%s-Mietspiegel.xlsx' % (timestamp, b, s,))
print("Excel wurde erstellt")

# Fragen? [@Balzer82](https://twitter.com/Balzer82)'''
