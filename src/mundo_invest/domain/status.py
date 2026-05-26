from enum import Enum


class StatusCliente(str, Enum):
    AGUARDANDO_ANALISE = "aguardando_analise"
    PROCESSADO = "processado"


class Prioridade(str, Enum):
    ALTA = "prioridade_alta"
    NORMAL = "prioridade_normal"
