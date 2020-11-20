import requests
import math
import locale
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

def incc(id):
    locale.setlocale(locale.LC_ALL, 'pt-BR.UTF-8')
    req = requests.get('https://sindusconpr.com.br/incc-di-fgv-' + str(id) + '-p')

    soup = BeautifulSoup(req.text, 'html.parser')

    div = soup.find('div', class_ = 'post')
    p = div.find_all('p', class_ = '')[-1]
    table = div.find('tbody')

    last_row = table.find_all('tr')[-2]
        
    values = []
    for data in last_row.find_all('span')[0:2]:
        values.append(data.text)


    values[0] = datetime.strptime(values[0], '%B/%Y')
    values[1] = float(values[1].replace(',', '.'))

    return(values)

def import_indice(tipo, arquivo):
    df = pd.read_excel(io=arquivo)
    lista1 = df['Unnamed: 1'].tolist()
    lista2 = df['INCC-M'].tolist()
    indices = []
    for i in lista1:
        if (type(i) == type(10.3) or type(i) == type(10)) and not math.isnan(i):
            indices.append(i)
    meses = []
   
    for i in lista2:
        if type(i) != type(0.1) and type(i) != type(''):
            meses.append(i)
    return([meses, indices])