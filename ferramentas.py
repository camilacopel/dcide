# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 15:34:54 2019

@author: C043869
"""
import pandas as pd
import numpy as np


def mais_proximo(vetor, valor):
    """
    Função auxiliar. Usada para retornar o primeiro índice do vetor cujo
    valor corresponde à variável 'valor'.
    """
    ind_min = (np.abs(vetor - valor)).argmin()
    return ind_min


def estatisticas(series, alfa=20):
    """
    A partir de uma matriz com dimensões iniciando em séries, devolve uma
    matriz de estatísticas como média, VaR, CVaR, etc.

    Necessita de um objeto do tipo CasoNewave.
    """
    num_series = series.shape[0]
    # Produz a série de percentis.
    vetor_percentual = (np.arange(0, num_series) + 1) / num_series
    # ---------------------------------------------------------------------
    # Média e desvio
    media = series.mean(axis=0)
    desvio = series.std(axis=0)
    # VAR90
    ind = mais_proximo(vetor_percentual, 1 - 0.90)
    var90 = series[ind]
    # VAR95
    ind = mais_proximo(vetor_percentual, 1 - 0.95)
    var95 = series[ind]
    # CVAR
    ind = mais_proximo(vetor_percentual, alfa/100)
    cvar = series[:ind+1].mean(axis=0)
    # Combinação Convexa
    conv = cvar * alfa/100 + media * (1 - alfa/100)
    # Resultados
    titulos = ['Média', 'Desvio', 'VAR90', 'VAR95', 'CVaR', 'Comb.Convexa']
    resultados = pd.DataFrame([media, desvio, var90, var95, cvar, conv],
                              index=titulos)
    return resultados
