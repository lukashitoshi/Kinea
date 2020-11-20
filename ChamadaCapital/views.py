from flask import Flask, render_template, request, redirect, make_response
from datetime import datetime
from ChamadaCapital import app, enumerables, get_incc, generate_pdf
from werkzeug.utils import secure_filename
from num2words import num2words
from dateutil.relativedelta import relativedelta
import win32com
import urllib
import os
import pandas
import requests
import pyodbc
import uuid
import locale
# from ChamadaCapital.get_incc import import_indice

# ----- auxiliares ----- #

def number_to_long_number(number_p):
    if number_p.find(',')!=-1:
        number_p = number_p.split(',')
        number_p1 = int(number_p[0].replace('.',''))
        number_p2 = int(number_p[1])
    else:
        number_p1 = int(number_p.replace('.',''))
        number_p2 = 0    

    if number_p1 == 1:
        aux1 = ' real'
    else:
        aux1 = ' reais'

    if number_p2 == 1:
        aux2 = ' centavo'
    else:
        aux2 = ' centavos'

    text1 = ''
    if number_p1 > 0:
        text1 = num2words(number_p1,lang='pt_BR') + str(aux1)
    else:
        text1 = ''

    if number_p2 > 0:
        text2 = num2words(number_p2,lang='pt_BR') + str(aux2) 
    else: 
        text2 = ''

    if (number_p1 > 0 and number_p2 > 0):
        result = text1 + ' e ' + text2
    else:
        result = text1 + text2

    return result

# ----- configuracoes ----- #

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
app.config["UPLOAD_ESTRUTURA"] = r'C:/Users/lukas/Documents/PythonScripts/Kinea/ChamadaCapital/static/estruturainvestimento'
ALLOWED_EXTENSIONS = {'pdf'}

server = r'DESKTOP-MPFIS8L\SQLEXPRESS'
database = 'Kinea'

cnxn = pyodbc.connect(
    r'Driver={SQL Server};'
    r'Server=' + server + r';'
    r'DATABASE=' + database + r';'
    r'Trusted_Connections=yes;'
    )
    
cursor = cnxn.cursor()


# ----- indice ----- #

@app.route('/email/<uuid:id>')
def email(id):
    cursor.execute('SELECT TextoEmail FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + str(id) + '\'')
    for row in cursor:
        for col in row:
            texto = col[1:(len(col) - 7)].replace('\\r', '').split(r'\n')

    return render_template('Carta/email.html', data=datetime.today(), texto=texto)

@app.route('/')
def index():
    # lista = import_indice(0, "C:/Users/lukas/Downloads/7e66-incc-m-serie-historica.xlsx")
    # for i in range(len(lista[0])):
    #     insert_query = '''INSERT INTO Indices (IndiceId, TipoCorrecao, Valor, DataReferencia)
    #         VALUES (?, ?, ?, ?);'''
    #     data = lista[0][i]
    #     valor = lista[1][i]
    #     valuesTuple = (uuid.uuid4(), 1, valor, data)
    #     cursor.execute(insert_query, valuesTuple)
    # cnxn.commit()

    cursor.execute(
        '''SELECT * FROM ChamadasAcionistas AS CA
        JOIN Acionistas AS AC ON AC.AcionistaId = CA.AcionistaId
        JOIN Investimentos AS IV ON AC.InvestimentoId = IV.InvestimentoId''')
    chamadas = []
    for row in cursor:
        chamada = []
        for col in row:
            chamada.append(col)
        chamada[2] = locale.currency(chamada[2], symbol=None, grouping=True)
        chamadas.append(chamada)
    # for i in chamadas:
    #     for j in range(len(i)):
    #         print("%s: %s" %(j, i[j]))

    return render_template('/indice.html', chamadas=chamadas, enumerables=enumerables)

# ----- investidores ----- #
    
@app.route('/investidores')
def investidores():

        cursor.execute('SELECT * FROM Investidores ORDER BY Nome')
        investidores = []

        for row in cursor:
            investidor = []

            for col in row:
                investidor.append(col)

            investidores.append(investidor)


        return render_template('/Investidores/indice.html', investidores=investidores, enumerables=enumerables)

@app.route('/investidor/criar', methods=['GET', 'POST'])
def criar_investidor():
    if request.method == 'POST':
        insert_query = '''INSERT INTO Investidores (InvestidorId, Nome, Banco, Agencia, ContaCorrente, CpfCnpj, TipoPessoa)
                        VALUES (?, ?, ?, ?, ?, ?, ?);'''

        nome = request.form['Nome']
        banco = request.form['Banco']
        agencia = request.form['Agencia']
        contaCorrente = request.form['ContaCorrente']
        tipoPessoa = request.form['TipoPessoa']
        cpfCnpj = request.form['CpfCnpj']
        id = uuid.uuid4()

        valuesTuple = (id , nome, banco, agencia, contaCorrente, cpfCnpj, tipoPessoa)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/investidor/' + str(id))
        
    else:
        return render_template('/Investidores/criar.html', enumerables=enumerables)
        
@app.route('/investidor/<uuid:id>')
def investidor(id):
    cursor.execute('SELECT * FROM Investidores WHERE InvestidorId = \'' + str(id) + '\'')
    investidor = []
    for row in cursor:
        for col in row:
            investidor.append(col)

    cursor.execute('''SELECT IA.InvestidorAcionistaId, IA.AcionistaId, AC.InvestimentoId, AC.Nome,
        IA.ValorComprometidoEquity, IA.ValorComprometidoPermuta, IA.SaldoCorrigido, IA.ValorIntegralizado
        FROM InvestidoresAcionistas AS IA JOIN Acionistas AS AC ON IA.AcionistaId = AC.AcionistaId 
        WHERE IA.InvestidorId = \'''' + str(id) + '\'')

    acionistas = []
    for row in cursor:
        acionista = []
        for col in row:
            acionista.append(col)
        acionistas.append(acionista)

    for i in range(len(acionistas)):
        cursor.execute('SELECT Nome FROM Investimentos WHERE InvestimentoId = \'' + acionistas[i][2] + '\'')
        for row in cursor:
            acionistas[i].append(row[0])
        cursor.execute('''SELECT ValorComprometidoEquity, ValorComprometidoPermuta 
            FROM InvestidoresAcionistas WHERE AcionistaId = \'''' + str(acionistas[i][1]) + '\'')
        vce, vcp = 0, 0
        for row in cursor:
            vce += row[0]
            vcp += row[1]

        if vce != 0:
            acionistas[i].append(float(acionistas[i][4]) / float(vce) * 100)
        else:
            acionistas[i].append(0.)
        
        if vcp != 0:
            acionistas[i].append(float(acionistas[i][5]) / float(vcp) * 100)
        else:
            acionistas[i].append(0.)

        acionistas[i][4] = locale.currency(acionistas[i][4], grouping=True, symbol=None)
        acionistas[i][5] = locale.currency(acionistas[i][5], grouping=True, symbol=None)
        acionistas[i][6] = locale.currency(acionistas[i][6], grouping=True, symbol=None)
        acionistas[i][7] = locale.currency(acionistas[i][7], grouping=True, symbol=None)

    cursor.execute('''SELECT IB.InvestidorBankerId, BA.BankerId, BA.Nome 
        FROM InvestidoresBankers AS IB JOIN Bankers AS BA ON IB.BankerId = BA.BankerId
        WHERE IB.InvestidorId = \'''' + str(id) + '\'')
    
    bankers = []
    for row in cursor:
        banker = []
        for col in row:
            banker.append(col)
        bankers.append(banker)

    cursor.execute('SELECT * FROM Conexoes WHERE InvestidorId = \'' + str(id) + '\';')
    conexoes = []
    for row in cursor:
        conexao = []
        for col in row:
            conexao.append(col)
        conexoes.append(conexao)

    cursor.execute('''SELECT PA.PagamentoId, PA.Valor, PA.DataPagamento, IV.Nome, AC.Nome 
        FROM Pagamentos AS PA
        JOIN ChamadasAcionistas AS CA ON PA.ChamadaAcionistaId = CA.ChamadaAcionistaId
        JOIN Acionistas AS AC ON AC.AcionistaId = CA.AcionistaId
        JOIN Investimentos AS IV ON IV.InvestimentoId = AC.InvestimentoId
        WHERE InvestidorId = \'''' + str(id) + '\';')
    pagamentos = []
    for row in cursor:
        pagamento = []
        for col in row:
            pagamento.append(col)
        pagamento[1] = locale.currency(pagamento[1], grouping=True, symbol=None)
        pagamentos.append(pagamento)
            

    return render_template(
        '/Investidores/detalhes.html', 
        investidor=investidor, 
        enumerables=enumerables,
        bankers=bankers, 
        acionistas=acionistas,
        pagamentos=pagamentos,
        conexoes=conexoes)

@app.route('/investidor/excluir/<uuid:id>')
def excluir_investidor(id):
    cursor.execute('DELETE FROM Conexoes WHERE InvestidorId = \'' + str(id) + '\'')
    cursor.execute('DELETE FROM Investidores WHERE InvestidorId = \'' + str(id) + '\'')
    cnxn.commit()
    
    return redirect('/investidores')

@app.route('/investidor/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_investidor(id):
    if request.method == 'POST':

        update_query = '''UPDATE Investidores
            SET Nome = ?, Banco = ?, Agencia = ?, ContaCorrente = ?, TipoPessoa = ?, CpfCnpj = ?
            WHERE InvestidorId = ?''' 

        nome = request.form['Nome']
        banco = request.form['Banco']
        agencia = request.form['Agencia']
        contaCorrente = request.form['ContaCorrente']
        tipoPessoa = request.form['TipoPessoa']
        cpfCnpj = request.form['CpfCnpj']
        valuesTuple = (nome, banco, agencia, contaCorrente, tipoPessoa, cpfCnpj, id)
        
        cursor.execute(update_query, valuesTuple)
        cursor.commit()


        return redirect('/investidor/' + str(id))
    
    cursor.execute('SELECT * FROM Investidores WHERE InvestidorId = \'' + str(id) + '\'')

    investidor = []
    for row in cursor:
        for col in row:
            investidor.append(col)
    
    return render_template('/Investidores/editar.html', investidor=investidor, enumerables=enumerables)

# ----- investimento ----- #

@app.route('/investimentos')
def investimentos():
    cursor.execute('SELECT * FROM Investimentos')
    investimentos = []

    for row in cursor:
        investimento = []

        for col in row:
            investimento.append(col)

        investimentos.append(investimento)


    return render_template('/Investimentos/indice.html', investimentos=investimentos, enumerables=enumerables)

@app.route('/criarinvestimento', methods=['GET', 'POST'])
def criar_investimento():
    if request.method == 'POST':
        insert_query = '''INSERT INTO Investimentos 
            (InvestimentoId, Nome, Cnpj, RazaoSocial, TipoCorrecao, 
            Incorporadora, DataInicial, DataTermino)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);'''

        investimentoId = uuid.uuid4()
        nome = request.form['Nome']       
        cnpj = request.form['Cnpj']
        razaoSocial = request.form['RazaoSocial']
        incorporadora = request.form['Incorporadora']
        tipoCorrecao = request.form['TipoCorrecao']
        dataInicial = request.form['DataInicial']
        dataTermino = request.form['DataTermino']
        valuesTuple = (
            investimentoId, nome, cnpj, razaoSocial, tipoCorrecao,
            incorporadora, dataInicial, dataTermino)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/investimento/' + str(investimentoId))
        
    else:
        return render_template('/Investimentos/criar.html', enumerables=enumerables)

@app.route('/investimento/<uuid:id>')
def investimento(id):
    cursor.execute('SELECT * FROM Investimentos WHERE InvestimentoId = \'' + str(id) + '\'')
    investimento = []
    for row in cursor:
        for col in row:
            investimento.append(col)

    cursor.execute('SELECT * FROM Acionistas WHERE InvestimentoId =\'' + str(id) + '\' AND AcionistaPaiId IS NULL')
    acionistas = []
    for row in cursor:
        acionista = []
        for col in row:
            acionista.append(col)
        acionistas.append(acionista)

    cursor.execute('SELECT * FROM ChamadasInvestimentos WHERE InvestimentoId = \'' + str(id) + '\' ORDER BY DataChamada')
    chamadas = []
    for row in cursor:
        chamada = []
        for col in row:
            chamada.append(col)
        chamada[0] = locale.currency(chamada[0], grouping=True, symbol=None)
        chamadas.append(chamada)

    cursor.execute('SELECT * FROM Unidades WHERE InvestimentoId = \'' + str(id) + '\' ORDER BY UnidadeNumero')
    unidades = []
    for row in cursor:
        unidade = []
        for col in row:
            unidade.append(col)
        unidade[4] = locale.currency(unidade[4], grouping=True, symbol=None)
        unidade[5] = locale.currency(unidade[5], grouping=True, symbol=None)
        unidades.append(unidade)

    return render_template(
        '/Investimentos/detalhes.html', 
        investimento=investimento,
        acionistas=acionistas, 
        chamadas=chamadas, 
        unidades=unidades,
        enumerables=enumerables)

@app.route('/investimento/excluir/<uuid:id>')
def excluir_investimento(id):
    cursor.execute('DELETE FROM Investimentos WHERE InvestimentoId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/investimentos')

@app.route('/investimento/uploadestrutura/<uuid:id>', methods = ['GET', 'POST'])
def upload_estrutura(id):
    if request.method == 'POST':
        f = request.files['Estrutura']
        f.save(os.path.join(app.config["UPLOAD_ESTRUTURA"], f.filename))
        cursor.execute('UPDATE Investimentos SET NomeArquivoEstrutura = \'' + 
            f.filename + '\' WHERE InvestimentoId = \'' + str(id) + '\'')
        cursor.commit()
        return redirect('/investimento/' + str(id))
    return 'algo deu errado!'

@app.route('/investimento/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_investimento(id):
    if request.method == 'POST':
        update_query = '''UPDATE Investimentos
            SET Nome = ?, Cnpj = ?, RazaoSocial = ?, TipoCorrecao = ?, DataInicial = ?, DataTermino = ?, Incorporadora = ?
            WHERE InvestimentoId = ?''' 

        nome = request.form['Nome']
        cnpj = request.form['Cnpj']
        razaoSocial = request.form['RazaoSocial']
        tipoCorrecao = request.form['TipoCorrecao']
        dataInicial = request.form['DataInicial']
        dataTermino = request.form['DataTermino']
        incorporadora = request.form['Incorporadora']
        valuesTuple = (nome, cnpj, razaoSocial, tipoCorrecao, dataInicial, dataTermino, incorporadora, id)
        
        cursor.execute(update_query, valuesTuple)
        cursor.commit()


        return redirect('/investimento/' + str(id))
        
    else:
        cursor.execute('SELECT * FROM Investimentos WHERE InvestimentoId = \'' + str(id) + '\'')

        investimento = []
        for row in cursor:
            for col in row:
                investimento.append(col)

        return render_template('/Investimentos/editar.html', enumerables=enumerables, investimento=investimento)

# ----- acionista ----- #

@app.route('/criaracionista/<uuid:id>', methods=['GET', 'POST'])
def criar_acionista(id):
    if request.method == 'POST':
        acionistaPai = request.args['acionista']
        insert_query = '''INSERT INTO Acionistas 
            (AcionistaId, InvestimentoId, Nome, Banco, 
            Agencia, ContaCorrente, Cnpj, AcionistaPaiId,
            ItensContrato, ClausulasContrato)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''

        acionistaId = uuid.uuid4()
        investimentoId = id       
        nome = request.form['Nome']
        banco = request.form['Banco']
        agencia = request.form['Agencia']
        contaCorrente = request.form['ContaCorrente']
        cnpj = request.form['Cnpj']
        itens = request.form['ItensContrato']
        clausulas = request.form['ClausulasContrato']

        if acionistaPai == '':
            acionistaPaiId = None
        else:
            acionistaPaiId = request.args['acionista']

        valuesTuple = (
            acionistaId, investimentoId, nome, banco, agencia,
            contaCorrente, cnpj, acionistaPaiId, itens, clausulas)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        
        return redirect('/acionista/' + str(acionistaId))
        
    else:
        acionista = request.args['acionista']
        return render_template('/Acionistas/criar.html', id=id, enumerables=enumerables, acionista=acionista)

@app.route('/acionista/<uuid:id>')
def acionista(id):
    cursor.execute('''SELECT * FROM Acionistas AS AC
        JOIN Investimentos AS IV ON AC.InvestimentoId = IV.InvestimentoId
        WHERE AcionistaId = \'''' + str(id) + '\'')
    acionista = []
    for row in cursor:
        for col in row:
            acionista.append(col)

    cursor.execute('''SELECT IA.InvestidorAcionistaId, IA.InvestidorId, IV.Nome, IV.CpfCnpj,
        IA.ValorComprometidoEquity, IA.ValorComprometidoPermuta, IA.SaldoCorrigido, IA.ValorIntegralizado
        FROM InvestidoresAcionistas AS IA
        JOIN Investidores AS IV ON IA.InvestidorId = IV.InvestidorId 
        WHERE IA.AcionistaId = \'''' + str(id) + '\'')

    vce, vcp, sc, vi = 0, 0, 0, 0
    investidores = []
    for row in cursor:
        investidor = []
        for col in row:
            investidor.append(col)
        vce += investidor[4]
        vcp += investidor[5]
        sc += investidor[6]
        vi += investidor[7]

        investidores.append(investidor)
    
    for i in range(len(investidores)):
        if vce != 0:
            investidores[i].append(float(investidores[i][4]) / float(vce) * 100)
        else:
            investidores[i].append(0.)

        if vcp != 0:
            investidores[i].append(float(investidores[i][5]) / float(vcp) * 100)
        else:
            investidores[i].append(0.)

        investidores[i][4] = locale.currency(investidores[i][4], grouping=True, symbol=None)
        investidores[i][5] = locale.currency(investidores[i][5], grouping=True, symbol=None)
        investidores[i][6] = locale.currency(investidores[i][6], grouping=True, symbol=None)
        investidores[i][7] = locale.currency(investidores[i][7], grouping=True, symbol=None)

    cursor.execute('SELECT * FROM Acionistas WHERE AcionistaPaiId = \'' + str(id) + '\'')
    acionistas = []
    for row in cursor:
        ac = []
        for col in row:
            ac.append(col)
        acionistas.append(ac)

    cursor.execute('SELECT * FROM ChamadasAcionistas WHERE AcionistaId = \'' + str(id) + '\'')
    chamadas = []
    for row in cursor:
        chamada = []
        for col in row:
            chamada.append(col)
        chamada[2] = locale.currency(chamada[2], grouping=True, symbol=None)
        chamadas.append(chamada)

    acionista.append(locale.currency(vce, grouping=True, symbol=None))
    acionista.append(locale.currency(vcp, grouping=True, symbol=None))
    acionista.append(locale.currency(vcp + vce, grouping=True, symbol=None))
    acionista.append(locale.currency(sc, grouping=True, symbol=None))
    acionista.append(locale.currency(vi, grouping=True, symbol=None))



    return render_template(
        '/Acionistas/detalhes.html', 
        investidores=investidores, 
        acionistas=acionistas,
        acionista=acionista,
        chamadas=chamadas,
        enumerables=enumerables)

@app.route('/acionista/excluir/<uuid:id>')
def excluir_acionista(id):
    cursor.execute('SELECT InvestimentoId, AcionistaPaiId FROM Acionistas WHERE AcionistaId = \'' + str(id) + '\'')
    ids = []
    for row in cursor:
        idDescarte = []
        for col in row:
            idDescarte.append(col)
        ids.append(idDescarte)

    cursor.execute('DELETE FROM Acionistas WHERE AcionistaId = \'' + str(id) + '\'')
    cnxn.commit()
    
    if ids[0][1] == None:
        return redirect('/investimento/' + str(ids[0][0]))
    else:
        return redirect('/acionista/' + str(ids[0][1]))

@app.route('/acionista/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_acionista(id):
    if request.method == 'POST':
        update_query = '''UPDATE Acionistas 
            SET Nome = ?, Banco = ?, Agencia = ?, ContaCorrente = ?, 
            Cnpj = ?, ItensContrato = ?, ClausulasContrato = ?
            WHERE AcionistaId = ?'''

        nome = request.form['Nome']
        banco = request.form['Banco']
        agencia = request.form['Agencia']
        contaCorrente = request.form['ContaCorrente']
        cnpj = request.form['Cnpj']
        itens = request.form['ItensContrato']
        clausulas = request.form['ClausulasContrato']

        valuesTuple = (
            nome, banco, agencia,
            contaCorrente, cnpj, itens, clausulas, id)

        cursor.execute(update_query, valuesTuple)
        cnxn.commit()

        
        return redirect('/acionista/' + str(id))
        
    else:
        cursor.execute('SELECT * FROM Acionistas WHERE AcionistaId = \'' + str(id) + '\'')
        acionista = []
        for row in cursor:
            for col in row:
                acionista.append(col)
        return render_template('/Acionistas/editar.html', acionista=acionista)
    
# ----- investidoracionista ----- #

@app.route('/adicionarinvestidoracionista/<uuid:id>', methods=['GET', 'POST'])
def adicionar_investidor_acionista(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO InvestidoresAcionistas 
            (InvestidorAcionistaId, InvestidorId, AcionistaId,
            ValorComprometidoEquity, ValorComprometidoPermuta, SaldoCorrigido, ValorIntegralizado, DataContrato, DataSaldoCorrigido)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?);'''

        investidorId = request.form['InvestidorId']
        valorComprometidoEquity = request.form['ValorComprometidoEquity'].replace('.', '').replace(',', '.')
        valorComprometidoPermuta = request.form['ValorComprometidoPermuta'].replace('.', '').replace(',', '.')
        dataContrato = request.form['DataContrato']

        cursor.execute('SELECT * FROM Acionistas WHERE AcionistaId = \'' + str(id) + '\'')
        acionista = []
        for row in cursor:
            for col in row:
                acionista.append(col)

        cursor.execute('SELECT * FROM Investimentos WHERE InvestimentoId = \'' + str(acionista[1]) + '\'')
        investimento = []
        for row in cursor:
            for col in row:
                investimento.append(col)

        cursor.execute('SELECT * FROM Indices WHERE TipoCorrecao = \'' + str(investimento[4]) + '\' ORDER BY DataReferencia')
        indices = []
        for row in cursor:
            indice = []
            for col in row:
                indice.append(col)
            indices.append(indice)

        dataAgora = (datetime.today() + relativedelta(months=-1)).strftime(r'%m/%Y')
        dataBase = (datetime.strptime(dataContrato, r'%d/%m/%Y') + relativedelta(months=-1)).strftime(r'%m/%Y')

        for i in range(len(indices)):
            indices[i][0] = indices[i][0].strftime(r'%m/%Y')
            if indices[i][0] == dataAgora:
                indiceAgora = float(indices[i][1])
            if indices[i][0] == dataBase:
                indiceBase = float(indices[i][1])

        saldoCorrigido = (float(valorComprometidoEquity) + float(valorComprometidoPermuta)) * (indiceAgora / indiceBase)
        saldoCorrigido = (str(round(saldoCorrigido, 2)))

        valuesTuple = (
            uuid.uuid4(), investidorId, id, valorComprometidoEquity, valorComprometidoPermuta, 
            saldoCorrigido, dataContrato, datetime.today().strftime(r'%d/%m/%Y'))

        cursor.execute(insert_query, valuesTuple)

        cnxn.commit()

        return redirect('/acionista/' + str(id))
        
    else:
        cursor.execute('SELECT * FROM Investidores')
        listaInvestidores = []
        for row in cursor:
            listaInvestidores.append([row[0], row[1], row[5], row[6]])

        return render_template('/InvestidoresAcionistas/adicionar.html', id=id, listaInvestidores=listaInvestidores)

@app.route('/investidoracionista/excluir/<uuid:id>')
def excluir_investidor_acionista(id):
    select_query = 'SELECT * FROM InvestidoresAcionistas WHERE InvestidorAcionistaId = \'' + str(id) + '\';'
    cursor.execute(select_query)
    investidoresAcionistas = []
    for row in cursor:
        for col in row:
            investidoresAcionistas.append(col)

    cursor.execute('DELETE FROM InvestidoresAcionistas WHERE InvestidorAcionistaId = \'' + str(id) + '\'')
    cnxn.commit()
    
    return redirect('/acionista/' + str(investidoresAcionistas[2]))

@app.route('/investidoracionista/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_investidor_acionista(id):
    if request.method == 'POST':
        update_query = '''UPDATE InvestidoresAcionistas 
            SET ValorComprometidoEquity = ?, ValorComprometidoPermuta = ?, SaldoCorrigido = ?, ValorIntegralizado = ?, DataContrato = ? 
            WHERE InvestidorAcionistaId = ?'''

        vce = request.form['ValorComprometidoEquity'].replace('.', '').replace(',', '.')
        vcp = request.form['ValorComprometidoPermuta'].replace('.', '').replace(',', '.')
        saldoCorrigido = request.form['SaldoCorrigido'].replace('.', '').replace(',', '.')
        valorIntegralizado = request.form['ValorIntegralizado'].replace('.', '').replace(',', '.')
        dataContrato = request.form['DataContrato']

        valuesTuple = (vce, vcp, saldoCorrigido, valorIntegralizado, dataContrato, id)

        cursor.execute(update_query, valuesTuple)
        cnxn.commit()

        cursor.execute('SELECT AcionistaId FROM InvestidoresAcionistas WHERE InvestidorAcionistaId = \'' + str(id) + '\'')
        invaci = []
        for row in cursor:
            for col in row:
                invaci.append(col)

        return redirect('/acionista/' + str(invaci[0]))
        
    else:
        cursor.execute('SELECT * FROM InvestidoresAcionistas WHERE InvestidorAcionistaId = \'' + str(id) + '\'')
        investidorAcionista = []
        for row in cursor:
            for col in row:
                investidorAcionista.append(col)

        return render_template('/InvestidoresAcionistas/editar.html', investidorAcionista=investidorAcionista)

# ----- bankers ----- #

@app.route('/bankers')
def bankers():
    cursor.execute('SELECT * FROM Bankers')
    bankers = []

    for row in cursor:
        banker = []

        for col in row:
            banker.append(col)

        bankers.append(banker)


    return render_template('/Bankers/indice.html', bankers=bankers)

@app.route('/banker/<uuid:id>')
def banker(id):
    cursor.execute('SELECT * FROM Bankers WHERE BankerId = \'' + str(id) + '\'')

    banker = []
    for row in cursor:
        for col in row:
            banker.append(col)

    cursor.execute('''SELECT IB.InvestidorBankerId, IV.InvestidorId, IV.Nome, IV.CpfCnpj
        FROM InvestidoresBankers AS IB
        JOIN Investidores AS IV ON IB.InvestidorId = IV.InvestidorId 
        WHERE IB.BankerId = \'''' + str(id) + '\'')

    investidores = []
    for row in cursor:
        investidor = []
        for col in row:
            investidor.append(col)
        investidores.append(investidor)
        
    valorComprometido = 0
    valorInvestido = 0

    cursor.execute('''SELECT IV.ValorComprometidoEquity, IV.ValorComprometidoPermuta, IV.ValorIntegralizado
        FROM InvestidoresBankers AS IB JOIN InvestidoresAcionistas AS IV ON IB.InvestidorId = IV.InvestidorId 
        WHERE IB.BankerId = \'''' + str(id) + '\'')
    
    for row in cursor:
        valorComprometido += row[0] + row[1]
        valorInvestido += row[2]

    banker.append(locale.currency(valorComprometido, grouping=True, symbol=None))
    banker.append(locale.currency(valorInvestido, grouping=True, symbol=None))
    
    cursor.execute(' SELECT * FROM Conexoes WHERE BankerId = \'' + str(id) + '\'')

    conexoes = []
    for row in cursor:
        conexao = []
        for col in row:
            conexao.append(col)
        conexoes.append(conexao)

    return render_template('Bankers/detalhes.html', 
        banker=banker, 
        investidores=investidores, 
        conexoes=conexoes, 
        enumerables=enumerables)

@app.route('/banker/criar', methods=['GET', 'POST'])
def criar_banker():
    if request.method == 'POST':
        insert_query = '''INSERT INTO Bankers 
            (BankerId, Nome)
            VALUES (?, ?);'''

        bankerId = uuid.uuid4()
        nome = request.form['Nome']    
        valuesTuple = (bankerId, nome)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/banker/' + str(bankerId))
        
    else:
        return render_template('/Bankers/criar.html')

@app.route('/banker/excluir/<uuid:id>')
def excluir_banker(id):
    cursor.execute('DELETE FROM Conexoes WHERE BankerId = \'' + str(id) + '\'')
    cursor.execute('DELETE FROM Bankers WHERE BankerId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/bankers')

@app.route('/banker/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_banker(id):
    if request.method == 'POST':
        update_query = 'UPDATE Bankers SET Nome = ? WHERE BankerId = ?' 
        nome = request.form['Nome']
        valuesTuple = (nome, id)

        cursor.execute(update_query, valuesTuple)
        cursor.commit()

        return redirect('/banker/' + str(id))
    
    cursor.execute('SELECT * FROM Bankers WHERE BankerId = \'' + str(id) + '\'')

    banker = []
    for row in cursor:
        for col in row:
            banker.append(col)
    
    return render_template('/Bankers/editar.html', banker=banker)

# ----- investidorbanker ----- #

@app.route('/investidorbanker/adicionar/<uuid:id>', methods=['GET', 'POST'])
def adicionar_investidor_banker(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO InvestidoresBankers 
            (InvestidorBankerId, InvestidorId, BankerId)
            VALUES (?, ?, ?);'''

        investidorId = request.form['BankerId']

        valuesTuple = (uuid.uuid4(), id, investidorId)

        cursor.execute(insert_query, valuesTuple)

        cnxn.commit()

        return redirect('/investidor/' + str(id))
        
    else:
        cursor.execute('SELECT * FROM Bankers')
        bankers = []
        for row in cursor:
            bankers.append([row[0], row[1]])

        return render_template('/InvestidoresBankers/adicionar.html', id=id, bankers=bankers)

@app.route('/investidorbanker/excluir/<uuid:id>')
def excluir_investidor_banker(id):
    cursor.execute('SELECT * FROM InvestidoresBankers WHERE InvestidorBankerId = \'' + str(id) + '\'')
    ids = []
    for row in cursor:
        for col in row:
            ids.append(col)

    cursor.execute('DELETE FROM InvestidoresBankers WHERE InvestidorBankerId = \'' + str(id) + '\'')
    cnxn.commit()
    rota = request.args['bi']
    if rota == 'b':
        return redirect('/banker/' + str(ids[2]))
    else:
        return redirect('/investidor/' + str(ids[1]))

# ----- chamadas investimentos ----- #

@app.route('/chamadainvestimento/criar/<uuid:id>', methods=['GET', 'POST'])
def criar_chamada_investimento(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO ChamadasInvestimentos (ChamadaInvestimentoId, InvestimentoId, ValorChamada, TipoChamada, DataChamada)
                        VALUES (?, ?, ?, ?, ?);'''

        valorChamada = request.form['ValorChamada'].replace('.', '').replace(',', '.')
        tipoChamada = request.form['TipoChamada']
        dataChamada = request.form['DataChamada']
        valuesTuple = (uuid.uuid4() , id, valorChamada, tipoChamada, dataChamada)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/investimento/' + str(id))
        
    else:
        return render_template('/ChamadasInvestimentos/criar.html', id=id, enumerables=enumerables)

@app.route('/chamadainvestimento/excluir/<uuid:id>')
def excluir_chamada_investimento(id):
    cursor.execute('SELECT InvestimentoId FROM ChamadasInvestimentos WHERE ChamadaInvestimentoId = \'' + str(id) + '\'')
    for row in cursor:
        investimentoId = row[0]
    cursor.execute('DELETE FROM ChamadasInvestimentos WHERE ChamadaInvestimentoId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/investimento/' + str(investimentoId))

@app.route('/chamadainvestimento/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_chamada_investimento(id):
    if request.method == 'POST':
        update_query = '''UPDATE ChamadasInvestimentos
            SET ValorChamada = ?, TipoChamada = ?, DataChamada = ?
            WHERE ChamadaInvestimentoId = ?'''

        valorChamada = request.form['ValorChamada'].replace('.', '').replace(',', '.')
        tipoChamada = request.form['TipoChamada']
        dataChamada = request.form['DataChamada']

        valuesTuple = (valorChamada, tipoChamada, dataChamada, id)

        cursor.execute(update_query, valuesTuple)
        cnxn.commit()

        cursor.execute('SELECT InvestimentoId FROM ChamadasInvestimentos WHERE ChamadaInvestimentoId = \'' + str(id) + '\'')
        for row in cursor:
            for col in row:
                investimentoId = col
        
        return redirect('/investimento/' + str(investimentoId))
    else:
        cursor.execute('SELECT * FROM ChamadasInvestimentos WHERE ChamadaInvestimentoId = \'' + str(id) + '\'')
        chamadaInvestimento = []

        for row in cursor:
            for col in row:
                chamadaInvestimento.append(col)

        return render_template('/ChamadasInvestimentos/editar.html', enumerables=enumerables, chamadaInvestimento=chamadaInvestimento)


# ----- chamadas acionistas ----- #

@app.route('/chamadaacionista/criar/<uuid:id>', methods=['GET', 'POST'])
def criar_chamada_acionista(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO ChamadasAcionistas 
            (ChamadaAcionistaId, AcionistaId, ValorChamada, TipoChamada, DataEnvioEmail, DataLimiteChamada, TextoEmail)
            VALUES (?, ?, ?, ?, ?, ?, ?);'''

        valorChamada = request.form['ValorChamada'].replace('.', '').replace(',', '.')
        tipoChamada = request.form['TipoChamada']
        dataEnvioEmail = request.form['DataEnvioEmail']
        dataLimiteChamada = request.form['DataLimiteChamada']
        textoEmail = request.form['TextoEmail']
        valuesTuple = (uuid.uuid4() , id, valorChamada, tipoChamada, dataEnvioEmail, dataLimiteChamada, repr(textoEmail))

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/acionista/' + str(id))
        
    else:
        texto = 'Prezado(a) Investidor(a),\n\nAnexo a carta da {n}ª chamada de capital do projeto PROJETO.\nOs recursos desta chamada serão utilizados para {pagamento das despesas iniciais do projeto}.\nQualquer dúvida estamos à disposição.\n\nAtenciosamente,\nEquipe Kinea​'
        return render_template('/ChamadasAcionistas/criar.html', id=id, enumerables=enumerables, texto=texto)

@app.route('/chamadaacionista/excluir/<uuid:id>')
def excluir_chamada_acionista(id):
    cursor.execute('SELECT AcionistaId FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + str(id) + '\'')
    for row in cursor:
        acionistaId = row[0]
    cursor.execute('DELETE FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/acionista/' + str(acionistaId))

@app.route('/chamadaacionista/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_chamada_acionista(id):
    if request.method == 'POST':
        update_query = '''UPDATE ChamadasAcionistas
            SET ValorChamada = ?, TipoChamada = ?, DataEnvioEmail = ?, DataLimiteChamada = ?, TextoEmail = ?
            WHERE ChamadaAcionistaId = ?'''

        valorChamada = request.form['ValorChamada'].replace('.', '').replace(',', '.')
        tipoChamada = request.form['TipoChamada']
        dataEnvioEmail = request.form['DataEnvioEmail']
        dataLimiteChamada = request.form['DataLimiteChamada']
        textoEmail = request.form['TextoEmail']

        valuesTuple = (valorChamada, tipoChamada, dataEnvioEmail, dataLimiteChamada, textoEmail, id)

        cursor.execute(update_query, valuesTuple)
        cnxn.commit()

        cursor.execute('SELECT AcionistaId FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + str(id) + '\'')
        for row in cursor:
            for col in row:
                acionistaId = col
        
        return redirect('/acionista/' + str(acionistaId))
    else:
        cursor.execute('SELECT * FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + str(id) + '\'')
        chamadaAcionista = []

        for row in cursor:
            for col in row:
                chamadaAcionista.append(col)

        return render_template('/ChamadasAcionistas/editar.html', enumerables=enumerables, chamadaAcionista=chamadaAcionista)


# ----- conexoes ----- #
        
@app.route('/investidor/conexao/criar/<uuid:id>', methods=['GET', 'POST'])
def criar_conexao_investidor(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO Conexoes 
            (ContatoId, InvestidorId, BankerId, TipoContato, Contato)
            VALUES (?, ?, NULL, ?, ?);'''

        tipoContato = request.form['TipoContato']
        contato = request.form['Contato']
        valuesTuple = (uuid.uuid4() , id, tipoContato, contato)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/investidor/' + str(id))
        
    else:
        return render_template('/Conexoes/Investidor/criar.html', id=id, enumerables=enumerables)
        
@app.route('/banker/conexao/criar/<uuid:id>', methods=['GET', 'POST'])
def criar_conexao_banker(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO Conexoes 
            (ContatoId, InvestidorId, BankerId, TipoContato, Contato)
            VALUES (?, NULL, ?, ?, ?);'''

        tipoContato = request.form['TipoContato']
        contato = request.form['Contato']
        valuesTuple = (uuid.uuid4() , id, tipoContato, contato)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/banker/' + str(id))
        
    else:
        return render_template('/Conexoes/Banker/criar.html', id=id, enumerables=enumerables)

@app.route('/investidor/conexao/excluir/<uuid:id>')
def excluir_conexao_investidor(id):
    cursor.execute('SELECT InvestidorId FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
    for row in cursor:
        investidorId = row[0]
    cursor.execute('DELETE FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/investidor/' + str(investidorId))
    
@app.route('/banker/conexao/excluir/<uuid:id>')
def excluir_conexao_banker(id):
    cursor.execute('SELECT BankerId FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
    for row in cursor:
        bankerId = row[0]
    cursor.execute('DELETE FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/banker/' + str(bankerId))

@app.route('/banker/conexao/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_conexao_banker(id):
    if request.method == 'POST':
        update_query = '''UPDATE Conexoes 
            SET TipoContato = ?, Contato = ?
            WHERE ContatoId = \'''' + str(id) + '\''

        tipoContato = request.form['TipoContato']
        contato = request.form['Contato']
        valuesTuple = (tipoContato, contato)

        cursor.execute(update_query, valuesTuple)
        cnxn.commit()

        cursor.execute('SELECT BankerId FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
        for row in cursor:
            for col in row:
                bankerId = col

        return redirect('/banker/' + str(bankerId))
        
    else:
        cursor.execute('SELECT * FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
        conexao = []
        for row in cursor:
            for col in row:
                conexao.append(col)

        return render_template('/Conexoes/Banker/editar.html', id=id, enumerables=enumerables, conexao=conexao)

@app.route('/investidor/conexao/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_conexao_investidor(id):
    if request.method == 'POST':
        update_query = '''UPDATE Conexoes 
            SET TipoContato = ?, Contato = ?
            WHERE ContatoId = \'''' + str(id) + '\''

        tipoContato = request.form['TipoContato']
        contato = request.form['Contato']
        valuesTuple = (tipoContato, contato)

        cursor.execute(update_query, valuesTuple)
        cnxn.commit()

        cursor.execute('SELECT InvestidorId FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
        for row in cursor:
            for col in row:
                investidorId = col

        return redirect('/investidor/' + str(investidorId))
        
    else:
        cursor.execute('SELECT * FROM Conexoes WHERE ContatoId = \'' + str(id) + '\'')
        conexao = []
        for row in cursor:
            for col in row:
                conexao.append(col)
        return render_template('/Conexoes/Investidor/editar.html', id=id, enumerables=enumerables, conexao=conexao)

# ----- unidades ----- #

@app.route('/unidade/criar/<uuid:id>', methods=['GET', 'POST'])
def criar_unidade(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO Unidades 
            (UnidadeId, InvestimentoId, Andar, Bloco, Area, Valor, Status, UnidadeNumero)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);'''

        unidade = request.form['Unidade']
        andar = request.form['Andar']
        bloco = request.form['Bloco']
        area = request.form['Area'].replace('.', '').replace(',', '.')
        valor = request.form['Valor'].replace('.', '').replace(',', '.')  
        status = request.form['Status']
        valuesTuple = (uuid.uuid4() , id, andar, bloco, area, valor, status, unidade)

        cursor.execute(insert_query, valuesTuple)
        cnxn.commit()

        return redirect('/investimento/' + str(id))
        
    else:
        return render_template('/Unidades/criar.html', id=id, enumerables=enumerables)

@app.route('/unidade/excluir/<uuid:id>')
def excluir_unidade(id):
    cursor.execute('SELECT InvestimentoId FROM Unidades WHERE UnidadeId = \'' + str(id) + '\'')
    for row in cursor:
        bankerId = row[0]
    cursor.execute('DELETE FROM Unidades WHERE UnidadeId = \'' + str(id) + '\'')
    cnxn.commit()

    return redirect('/investimento/' + str(bankerId))

@app.route('/unidade/editar/<uuid:id>', methods=['GET', 'POST'])
def editar_unidade(id):
    if request.method == 'POST':

        cursor.execute('SELECT InvestimentoId FROM Unidades WHERE UnidadeId = \'' + str(id) + '\'')
        
        for row in cursor:
            for col in row:
                investimentoId = col

        update_query = '''UPDATE Unidades
            SET Andar = ?, Bloco = ?, Area = ?, Valor = ?, Status = ?, UnidadeNumero = ?
            WHERE UnidadeId = ?''' 

        unidade = request.form['Unidade']
        andar = request.form['Andar']
        bloco = request.form['Bloco']
        area = request.form['Area']
        valor = request.form['Valor']
        status = request.form['Status']
        valuesTuple = (andar, bloco, area, valor, status, unidade, id)
        
        cursor.execute(update_query, valuesTuple)
        cursor.commit()


        return redirect('/investimento/' + str(investimentoId))
    
    cursor.execute('SELECT * FROM Unidades WHERE UnidadeId = \'' + str(id) + '\'')

    unidade = []
    for row in cursor:
        for col in row:
            unidade.append(col)
    
    return render_template('/Unidades/editar.html', unidade=unidade, enumerables=enumerables)

# ----- pagamentos ----- #

@app.route('/pagamento/adicionar/<uuid:id>', methods=['GET', 'POST'])
def adicionar_pagamento(id):
    if request.method == 'POST':
        insert_query = '''INSERT INTO Pagamentos
            (PagamentoId, InvestidorId, ChamadaAcionistaId, Valor, DataPagamento)
            VALUES (?, ?, ?, ?, ?);'''

        valor = request.form['Valor'].replace('.', '').replace(',', '.')
        dataPagamento = request.form['DataPagamento']
        ids = request.form['ChamadaId'].split('&')
        chamadaId = ids[0]
        investidorAcionistaId = ids[1]
        valuesTuple = (uuid.uuid4(), id, chamadaId, valor, dataPagamento)

        cursor.execute(insert_query, valuesTuple)
        cursor.execute('''UPDATE InvestidoresAcionistas 
            SET ValorIntegralizado = ValorIntegralizado + ?, 
            SaldoCorrigido = SaldoCorrigido - ?
            WHERE InvestidorAcionistaId = ?''', 
            (valor, valor, investidorAcionistaId))

        cnxn.commit()

        return redirect('/investidor/' + str(id))

    else:
        cursor.execute('''SELECT CA.ChamadaAcionistaId, IA.InvestidorAcionistaId, IV.Nome, AC.Nome, CA.ValorChamada, CA.DataEnvioEmail
        FROM ChamadasAcionistas AS CA 
        JOIN InvestidoresAcionistas AS IA ON IA.AcionistaId = CA.AcionistaId
        JOIN Acionistas AS AC ON AC.AcionistaId = IA.AcionistaId
        JOIN Investimentos AS IV ON IV.InvestimentoId = AC.InvestimentoId
        WHERE IA.InvestidorId = \'''' + str(id) + '\' ORDER BY CA.DataEnvioEmail')
        chamadas = []
        for row in cursor:
            chamada = []
            for col in row:
                chamada.append(col)
            chamadas.append(chamada)
        return render_template('Pagamentos/adicionar.html', id=id, chamadas=chamadas)

# ----- carta ----- #

def carta(chamadaId, investidorId):
    # chamadaId = 'BEE06635-DF1B-4D71-8290-44A21AA5E50F'
    # investidorId = '3E493F2F-01D3-4292-A671-3DAE34F71A0A'

    cursor.execute('SELECT * FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + chamadaId + '\'')
    chamada = []
    for row in cursor:
        for col in row:
            chamada.append(col)

    cursor.execute('SELECT * FROM Investidores WHERE InvestidorId = \'' + investidorId + '\'')
    investidor = []
    for row in cursor:
        for col in row:
            investidor.append(col)

    cursor.execute('SELECT * FROM InvestidoresAcionistas WHERE AcionistaId = \'' + str(chamada[1]) + '\'')
    invacis = []
    for row in cursor:
        invaci = []
        for col in row:
            invaci.append(col)
        invacis.append(invaci)

    cursor.execute('SELECT * FROM Acionistas WHERE AcionistaId = \'' + str(chamada[1]) + '\'')
    acionista = []
    for row in cursor:
        for col in row:
            acionista.append(col)
    
    cursor.execute('SELECT * FROM Investimentos WHERE InvestimentoId = \'' + str(acionista[1]) + '\'')
    investimento = []
    for row in cursor:
        for col in row:
            investimento.append(col)

    cursor.execute('SELECT * FROM Conexoes WHERE InvestidorId = \'' + investidorId + '\' AND TipoContato = \'0\'')
    emails = ''
    for row in cursor:
        emails += row[4] + '; '
    investidor.append(emails)
    
    if chamada[3] == 0:
        soma = 0
        for invest in invacis:
            soma += float(invest[3])
            if invest[1] == investidorId:
                valor = float(invest[3])
                investidor.append(locale.currency(valor, grouping=True, symbol=None))
        if soma != 0:
            part = valor/soma
            valorChamada = float(chamada[2]) * part
            chamada.append(locale.currency(valorChamada, grouping=True, symbol=None))        

    if chamada[3] == 1:
        soma = 0
        for invest in invacis:
            soma += float(invest[4])
            if invest[1] == investidorId:
                valor = float(invest[4])
                investidor.append(locale.currency(valor, grouping=True, symbol=None))

        if soma != 0:
            part = valor/soma
            valorChamada = float(chamada[2]) * part
            chamada.append(locale.currency(valorChamada, grouping=True, symbol=None))    
        
    cursor.execute('''SELECT * FROM InvestidoresAcionistas 
        WHERE AcionistaId = \'''' + str(chamada[1]) + '\' AND InvestidorId = \'' + investidorId + '\'')
    for row in cursor:
        for col in row:
            investidor.append(col)

    chamada.append(number_to_long_number(str(chamada[8])))
    parametros = [
        investidor[17].strftime("%d de %B de %Y"),
        investimento[1],
        acionista[8],
        acionista[9],
        chamada[8],
        chamada[9],
        investidor[1],
        chamada[4].strftime("%d de %B de %Y"),
        chamada[5].strftime("%d de %B de %Y"),
        investidor[8],
        acionista[3],
        acionista[4],
        acionista[5],
        investimento[3],
        acionista[7],
        chamadaId,
        investidorId
    ]
    generate_pdf.carta(parametros)
    return

@app.route('/gerarcarta/<uuid:id>')
def gerar_cartas(id):
    cursor.execute('SELECT AcionistaId FROM ChamadasAcionistas WHERE ChamadaAcionistaId = \'' + str(id) + '\'')
    for row in cursor:
        for col in row:
            acionistaId = col
    
    cursor.execute('''SELECT InvestidorId FROM InvestidoresAcionistas 
        WHERE AcionistaId = \'''' + str(acionistaId) + '\'')
    investidores = []
    for row in cursor:
        for col in row:
            investidores.append(col)

    for investidor in investidores:
        cursor.execute('SELECT Contato FROM Conexoes WHERE InvestidorId = \'' + str(investidor) + '\' AND TipoContato = 0')
        corpoEmail = ''
        for row in cursor:
            for col in row:
                corpoEmail += col + '; '
        carta(str(id), str(investidor))
        corpoEmail = email(str(id))
        enviar_email("Chamada de Capital", email, "", corpoEmail, "")

    return redirect('/')

def enviar_email(assunto, destinatarios, comCopia, CorpoEmail, anexo):
    Outlook = win32com.client.Dispatch("Outlook.Application")
    Contas = Outlook.GetNamespace("MAPI").Session.Accounts
    contaEmail = None

    destinatarios = 'lukas.shiroma@usp.br; '
    for account in Contas:
        if account.SmtpAddress == "lukas.shiroma@usp.br":
            contaEmail = account
            _ = account.DeliveryStore
            novoEmail = Outlook.CreateItem(0)
            novoEmail.Subject = assunto
            novoEmail.To = destinatarios
            novoEmail.CC = comCopia
            novoEmail.HTMLBody = CorpoEmail

            novoEmail.Attachments.Add(anexo)           

            novoEmail._oleobj_.Invoke(*(64209, 0, 8, 0, contaEmail))
            novoEmail.Send()

    return

@app.route('/corrigirsaldo')
def corrigir_saldo():
    cursor.execute('SELECT * FROM Indices WHERE TipoCorrecao = \'0\' ORDER BY DataReferencia')

    incc_di = []
    for row in cursor:
        incc_di_row = []
        for col in row:
            incc_di_row.append(col)
        incc_di.append(incc_di_row)

    cursor.execute('SELECT * FROM Indices WHERE TipoCorrecao = \'1\' ORDER BY DataReferencia')

    incc_m = []
    for row in cursor:
        incc_m_row = []
        for col in row:
            incc_m_row.append(col)
        incc_m.append(incc_m_row)

    incc_di_new = get_incc.incc(310)
    incc_m_new = get_incc.incc(1364)
    incc_di_exists = False
    incc_m_exists = False

    for i in incc_di:
        if i[0] == incc_di_new[0]:
            incc_di_exists = True
            
    for i in incc_m:
        if i[0] == incc_m_new[0]:
            incc_m_exists = True

    if not incc_di_exists:
        cursor.execute('''INSERT INTO Indices
            (DataReferencia, Valor, TipoCorrecao, IndiceId)
            VALUES (?, ?, 0, ?)''', (incc_di_new[0], incc_di_new[1], uuid.uuid4()))
        cnxn.commit()

    if not incc_m_exists:
        cursor.execute('''INSERT INTO Indices
            (DataReferencia, Valor, TipoCorrecao, IndiceId)
            VALUES (?, ?, 1, ?)''', (incc_m_new[0], incc_m_new[1], uuid.uuid4()))
        cnxn.commit()

    cursor.execute('''SELECT IA.InvestidorAcionistaId, IA.SaldoCorrigido, IA.DataSaldoCorrigido, IO.TipoCorrecao
            FROM InvestidoresAcionistas AS IA 
            JOIN Acionistas AS AC ON IA.AcionistaId = AC.AcionistaId
            JOIN Investimentos AS IO ON AC.InvestimentoId = IO.InvestimentoId
            WHERE TipoCorrecao = \'0\'''')

    invs_acis = []
    for row in cursor:
        inv_aci = []
        for col in row:
            inv_aci.append(col)
        invs_acis.append(inv_aci)

    dataAgora = (datetime.today() + relativedelta(months=-1)).strftime(r'%m/%Y')
    for k in incc_di:
        k[0] = k[0].strftime(r'%m/%Y')

    for i in invs_acis:
        if i[2] != incc_di_new[0]:
            dataBase = (i[2] + relativedelta(months=-1)).strftime(r'%m/%Y')
            for k in incc_di:
                if k[0] == dataAgora:
                    indiceAgora = float(k[1])
                if k[0] == dataBase:
                    indiceBase = float(k[1])
            saldoCorrigido = float(i[1]) * (indiceAgora / indiceBase)
            cursor.execute(
                '''UPDATE InvestidoresAcionistas SET SaldoCorrigido = ?, DataSaldoCorrigido = ?
                WHERE InvestidorAcionistaId = \'''' + str(i[0]) + '\'', 
                (saldoCorrigido, datetime.today().strftime(r'%d/%m/%Y')))

    cnxn.commit()
    return redirect('/')

# ----- run ----- #

if __name__ == "__main__":
    app.run(debug=True)