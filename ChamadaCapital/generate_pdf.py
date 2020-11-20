from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors

width, height = A4
def coord(x, y, unit=1):
    x, y = x * unit, height -  y * unit
    return x, y

def carta(parametros):
    data_contrato = parametros[0]
    investimento = parametros[1]
    itens_contrato = parametros[2]
    clausulas_contrato = parametros[3]
    valor_numero = parametros[4]
    valor_extenso = parametros[5]
    nome = parametros[6]
    data_email = parametros[7]
    data_limite = parametros[8]
    emails = parametros[9]
    banco = parametros[10]
    agencia = parametros[11]
    conta = parametros[12]
    razao_social = parametros[13]
    cnpj = parametros[14]
    chamada_id = parametros[15]
    investidor_id = parametros[16]

    styles = getSampleStyleSheet()
    styleN = styles["BodyText"]
    styleN.alignment = TA_JUSTIFY
    styleN.firstLineIndent = 24
    styleN.leading = 16


    c = canvas.Canvas('%s&%s.pdf' %(chamada_id, investidor_id), pagesize=A4)
    c.setTitle("Chamada de Capital")
    c.setFillColorRGB(0, 0, 0)

    text =  '''Conforme disposto no INSTRUMENTO PARTICULAR DE CONSTITUIÇÃO DE SOCIEDADE EM CONTA DE PARTICIPAÇÃO
    (“Contrato”), celebrado em %s entre o(a) SÓCIO(A) PARTICIPANTE e %s., a Sociedade, por meio de seu administrador 
    abaixo assinado, serve-se da presente para notificar o(a) SÓCIO(A) PARTICIPANTE para que este efetue o aporte de 
    capital na Sociedade, nos termos do(s) item(ns) %s do “Contrato”, no valor total de R$ %s (%s), conforme dados 
    abaixo, sob pena de constituição em mora do(a) Sócio(a) Participante, sujeitando-o ao disposto nas Cláusulas: %s do 
    “Contrato”:''' %(data_contrato, investimento, itens_contrato, valor_numero, valor_extenso, clausulas_contrato)

    data_text = Paragraph(text, styleN)

    data= [[data_text]]

    table = Table(data, colWidths=[17.4 * cm])
    table.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.25, colors.white)]))
    table.wrapOn(c, width, height)
    table.drawOn(c, *coord(1.8, 10.5, cm))

    c.drawString(*coord(2, 2.3, cm), nome)
    c.drawString(*coord(2, 4.2, cm), 'SR(A). %s ("SÓCIO(A) PARTICIPANTE")' %(nome))
    c.setFont("Helvetica", 10)
    c.drawString(*coord(2, 2.9, cm), data_email)
    c.drawString(*coord(2, 4.8, cm), "Correio Eletrônico: %s" %(emails))

    image = 'NovoLogoKinea.png'
    c.drawInlineImage(image, *coord(15, 11.5, cm), width=90, preserveAspectRatio=True)

    textLines = [
    'Data Limite: %s' %(data_limite),
    'Valor da Chamada de Capital: R$ %s' %(valor_numero),
    'Banco: %s' %(banco),
    'Agência: %s' %(agencia),
    'Conta Corrente: %s' %(conta),
    'Razão Social: %s' %(razao_social),
    'CNPJ: %s' %(cnpj)
    ]

    c.setFont("Helvetica-Bold", 10)
    text = c.beginText(*coord(3, 12.6, cm))
    text.setLeading(18)
    for line in textLines:
        text.textLine(line)

    c.drawText(text)

    c.setLineWidth(3)
    c.line(75, 495, 75, 375)
    c.setFont("Helvetica", 10)

    text =  '''O depósito do Valor da Chamada de Capital, segundo as instruções 
    contidas nesta notificação, importará na outorga pela Sociedade ao SÓCIO PARTICIPANTE 
    de ampla e irrestrita quitação em relação à obrigação de aporte de capital, com 
    relação à chamada de capital referente a esta Notificação, independentemente de 
    qualquer formalidade posterior.'''

    data_text = Paragraph(text, styleN)

    data= [[data_text]]

    table = Table(data, colWidths=[17.4 * cm])
    table.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.25, colors.white)]))
    table.wrapOn(c, width, height)
    table.drawOn(c, *coord(1.8, 20.5, cm))

    c.drawString(*coord(2, 22.8, cm), "Atenciosamente, ")
    c.drawString(*coord(2, 23.4, cm), 'Equipe Kinea.')
    c.drawString(*coord(2, 26.4, cm), 'Não Corporativo.')
    c.save()

    return