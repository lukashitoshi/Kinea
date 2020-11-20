from enum import Enum
    
class TipoContato(Enum):
    Email = 0
    Telefone = 1
    Endereço = 2

class TipoPessoa(Enum):
    Fisica = 0
    Juridica = 1

class TipoChamada(Enum):
    Equity = 0
    Permuta = 1
    
class TipoCorrecao(Enum):
    INCCDI = 0
    INCCM = 1
    IPCA = 2
    CDI = 3

class StatusUnidade(Enum):
    Vendido = 0
    Disponivel = 1
    Quitado = 2
    
