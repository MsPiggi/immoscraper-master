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
import pandas as pd



# In[2]:


# urlquery from Achim Tack. Thank you!
# https://github.com/ATack/GoogleTrafficParser/blob/master/google_traffic_parser.py
def urlquery(url):
    # function cycles randomly through different user agents and time intervals to simulate more natural queries
    try:
        sleeptime = float(random.randint(1,5))/5
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


# In[3]:


def immoscout24parser(url):
    
    ''' Parser holt aus Immoscout24.de Suchergebnisseiten die Immobilien '''
    
    try:
        soup = BeautifulSoup(urlquery(url), 'html.parser')
        scripts = soup.findAll('script')
        for script in scripts:
            #print (script.text.strip())
            if 'IS24.resultList' in script.text.strip():
                s = script.string.split('\n')
                for line in s:
                    #print('\n\n\'%s\'' % line)
                    #bricht den String langsam runter, bis nur noch die gewünschte json da ist
                    if line.strip().startswith('resultListModel'):
                        resultListModel = line.strip('resultListModel: ')
                        immo_json = json.loads(resultListModel[:-1])
                        #print(immo_json)
                        searchResponseModel = immo_json[u'searchResponseModel']
                        #print (searchResponseModel)
                        resultlist_json = searchResponseModel[u'resultlist.resultlist']
                        #print(resultlist_json)
                        return resultlist_json

    except Exception as e:
        print("Fehler in immoscout24 parser: %s" % e)

# In[]:
def immoscout24anzeigenparser(url):
    
    ''' Parser holt aus den Immobielen Seiten die letzen inforamtionen '''
    
    try:
     soup2 = BeautifulSoup(urlquery(url), 'html.parser')
     immo_element = soup2.find(class_='viewport')
     #print(immo_element)
     return immo_element
    
    except:
        print("Fehler im immoscout24anzeigenpaser parser")





# ## Main Loop
# 
# Geht Wohnungen und Häuser, jeweils zum Kauf und Miete durch und sammelt die Daten

# In[4]:


def parser_main (k, w, b, s):

    page = 0
    immos = {}
    date_count = datetime.strftime(datetime.now(), '%Y.%m.%d')

    while True:
        
        #Dient nur dem Test und soll den cirle schneller unterbrechen
        # anzahl = 0    
        # if anzahl==1:
        #     break
        
        
        page+=1
        url = 'http://www.immobilienscout24.de/Suche/S-T/P-%s/%s-%s/%s/%s?pagerReporting=true' % (page, k, w, b, s)
        
        # Because of some timeout or immoscout24.de errors,
        # we try until it works \o/
        resultlist_json = None
        while resultlist_json is None:
            try:
                resultlist_json = immoscout24parser(url)
                #print(resultlist_json)
                numberOfPages = int(resultlist_json[u'paging'][u'numberOfPages'])
                pageNumber = int(resultlist_json[u'paging'][u'pageNumber'])
            except:
                pass

        if page>numberOfPages:
            break

        # Get the data
        for resultlistEntry in resultlist_json['resultlistEntries'][0][u'resultlistEntry']:
            
            #Dient nur dem Test und soll den cirle schneller unterbrechen
            # if anzahl==1:
            #     break    


            
            if page>numberOfPages:
                break
            
            #print(resultlistEntry)
            try: #BUG!!!!!
                realEstate_json = resultlistEntry[u'resultlist.realEstate']
                #print(realEstate_json)
            except:
                break
            
            realEstate = {}

            realEstate[u'pulldate'] = date_count
            realEstate['publishDate'] = resultlistEntry[u'@publishDate']
            realEstate[u'Miete/Kauf'] = w
            realEstate[u'Haus/Wohnung'] = k

            realEstate['address'] = realEstate_json['address']['description']['text']
            realEstate['city'] = realEstate_json['address']['city']
            realEstate['postcode'] = realEstate_json['address']['postcode']
            realEstate['quarter'] = realEstate_json['address']['quarter']
            try:
                realEstate['lat'] = realEstate_json['address'][u'wgs84Coordinate']['latitude']
                realEstate['lon'] = realEstate_json['address'][u'wgs84Coordinate']['longitude']
            except:
                realEstate['lat'] = None
                realEstate['lon'] = None
                
            realEstate['title'] = realEstate_json['title']

            realEstate['numberOfRooms'] = realEstate_json['numberOfRooms']
            realEstate['livingSpace'] = realEstate_json['livingSpace']
            try:
                realEstate['contactDetails'] = realEstate_json['contactDetails']['company']
            except:
                realEstate['contactDetails'] = None

            if w == 'Kauf':
                realEstate['courtage'] = realEstate_json['courtage']['hasCourtage']

            

            if k=='Wohnung':
                realEstate['balcony'] = realEstate_json['balcony']
                realEstate['builtInKitchen'] = realEstate_json['builtInKitchen']
                realEstate['garden'] = realEstate_json['garden']
                realEstate['price'] = realEstate_json['price']['value']
                realEstate['privateOffer'] = realEstate_json['privateOffer']
            elif k=='Haus':
                realEstate['isBarrierFree'] = realEstate_json['isBarrierFree']
                realEstate['cellar'] = realEstate_json['cellar']
                realEstate['plotArea'] = realEstate_json['plotArea']
                realEstate['price'] = realEstate_json['price']['value']
                realEstate['privateOffer'] = realEstate_json['privateOffer']
                try:
                    realEstate['energyPerformanceCertificate'] = realEstate_json['energyPerformanceCertificate']
                except:
                    realEstate['energyPerformanceCertificate'] = None
           
            realEstate['floorplan'] = realEstate_json['floorplan']
            realEstate['from'] = realEstate_json['companyWideCustomerId']
            realEstate['ID'] = realEstate_json[u'@id']
            realEstate['url'] = u'https://www.immobilienscout24.de/expose/%s' % realEstate['ID']

            
            #hier wird die Url aufgegriffen und die Seite der eigentlichen Immobile aufgemacht
            realEstat_Info = immoscout24anzeigenparser( realEstate['url'])
            

            
            
            try:
                realEstate['Provision'] = realEstat_Info.find("dd", class_="is24qa-provision grid-item two-fifths").text.strip()
            except:
                realEstate['Provision'] = None

            try:
                realEstate['Hausgeld'] = realEstat_Info.find("dd", class_="is24qa-hausgeld grid-item three-fifths").text.strip()
            except:
                realEstate['Hausgeld'] = None

            try:
                realEstate['Baujahr'] = realEstat_Info.find("dd", class_="is24qa-baujahr grid-item three-fifths").text.strip()
            except:
                realEstate['Baujahr'] = None

            try:
                realEstate['Objektzustand'] = realEstat_Info.find("dd", class_="is24qa-objektzustand grid-item three-fifths").text.strip()
            except:
                realEstate['Objektzustand'] = None

            #benötigt text
            reg = ("modernisiert", "renoviert", "erneuert")
            realEstate['Renovierung in Beschr.'] = None
            for x in reg:
                renovierungsfinder = re.search(x, "Texte")
                if renovierungsfinder != None: 
                    realEstate['Renovierung in Beschr.'] = "True"
                    break

            
             
            realEstate['Bundesland'] = b
            immos[realEstate['ID']] = realEstate
            # anzahl += 1






        print('Scrape Page %i/%i (%i Immobilien %s %s in %s gefunden)' % (page, numberOfPages, len(immos), k, w, b))

    print("Scraped %i Immos" % len(immos))
    create_excel(immos, w, k)
    immos.clear()



# ## Datenaufbereitung & Cleaning
# 
# Die gesammelten Daten werden in ein sauberes Datenformat konvertiert, welches z.B. auch mit Excel gelesen werden kann. Weiterhin werden die Ergebnisse pseudonymisiert, d.h. die Anbieter bekommen eindeutige Nummern statt Klarnamen.

# In[7]:

def create_excel(immos, w, k):
    from openpyxl import load_workbook
    
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d')

    df = pd.DataFrame(immos).T
    df.index.name = 'ID'

    df.livingSpace[df.livingSpace==0] = None
    df['EUR/qm'] = df.price / df.livingSpace
    df.sort_values(by='EUR/qm', inplace=True)

    try:
        # new dataframe with same columns
        p1 = r"C:\Users\grh\OneDrive\Immobilien\04_Wohnungen\Power Bi\Data"
        p2 =  r"\%s-%s.xlsx" %(k, w)
        path = p1+p2

        writer = pd.ExcelWriter(path, engine='openpyxl')

        # try to open an existing workbook
        writer.book = load_workbook(path)
        # copy existing sheets
        writer.sheets = dict((ws.title, ws) for ws in writer.book.worksheets)
        # read existing file
        reader = pd.read_excel(path)
        # print(reader)
        # write out the new sheet
        df.to_excel(writer,"Sheet1", index=True,header=False,startrow=len(reader)+1)
        writer.save()
        writer.close()
        print("Excel wurde erstellt")
    except:
        print("Es gab bei der Excelerstellung einen Fehler. Vermutlich existiert sie gerade nicht")
   
   
    # df.livingSpace[df.livingSpace==0] = None
    # df['EUR/qm'] = df.price / df.livingSpace
    # df.sort_values(by='EUR/qm', inplace=True)

    # #len(df) glaube der macht nichts
    # df.head()


    # # ## Alles Dumpen


    # f = open('%s-%s-%s-%s-%s.csv' % (timestamp, b, s, k, w), 'w', encoding= 'utf-8')
    # f.write('# %s %s from immoscout24.de on %s\n' % (k,w,timestamp))
    # df[(df['Haus/Wohnung']==k) & (df['Miete/Kauf']==w)].to_csv(f, encoding='utf-8')
    # f.close()

    # print("Excel wird erstellt")
    # df.to_excel('%s-%s-%s-%s-%s.xlsx' % (timestamp, b, s, k, w))
    # print("Excel wurde erstellt")








# In[8]:

#Hauptcode, der alle anderen antriggert
searchlists = [] 
searchlists.append(['Bremen', 'Bremen', 'Wohnung','Kauf'])
searchlists.append(['Bremen', 'Bremen', 'Haus','Kauf'])
# searchlists.append(['Hamburg', 'Hamburg', 'Wohnung','Kauf'])
# searchlists.append(['Hamburg', 'Hamburg', 'Haus','Kauf'])
# searchlists.append(['Niedersachsen', 'Braunschweig', 'Wohnung','Kauf'])
# searchlists.append(['Niedersachsen', 'Braunschweig', 'Haus','Kauf'])
# searchlists.append(['Schleswig-Holstein', 'Flensburg', 'Wohnung','Kauf'])
# searchlists.append(['Schleswig-Holstein', 'Flensburg', 'Haus','Kauf'])

for i in searchlists:
       
    # See immoscout24.de URL in Browser!
    b = i[0] # Bundesland
    s = i[1] # Stadt
    k = i[2] # Wohnung oder Haus
    w = i[3] # Miete oder Kauf
    print('Suche %s / %s in %s' % (k, w, s))
    parser_main(k, w, b, s)
    


# Fragen? [@Balzer82](https://twitter.com/Balzer82)
