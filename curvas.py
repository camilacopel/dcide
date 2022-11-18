"""
Cuidado ao mudar a data inicial.

Registro dos formatos necessários para o arquivo de leitura
Inflação: não para PLD, sim para MPD.
"""
import pandas as pd
import dcide_impressoes as di
from itertools import combinations
from copy import deepcopy

# -----------------------------------------------------------------------------
# Definições iniciais.
# -----------------------------------------------------------------------------
cls_dc = ['Semanas', 'Datas', 'Preços']
cls_ipca = ['Ano', 'Mês', 'Número', 'No Mês', '3 Meses', '6 Meses', 'No Ano',
            '12 Meses']
meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT',
         'NOV', 'DEZ']
data_inicial = pd.DataFrame({'year': [2012], 'month': [1], 'day': [1]})
data_inicial = pd.to_datetime(data_inicial)
data_final = pd.DataFrame({'year': [2023], 'month': [12], 'day': [31]})
data_final = pd.to_datetime(data_final)
# Para curvas de série anual disponíveis
ano_lt_ini = 2013
ano_lt_fim = 2026
conv = True
if conv:
    pasta = r'Dcide convencional/'
else:
    pasta = r'Dcide incentivada/'

# -----------------------------------------------------------------------------
# %% Leituras.
# -----------------------------------------------------------------------------
# PLDs
plds = pd.read_excel("precos.xlsx")
# -----------------------------------------------------------------------------
# IPCA
ipca = pd.read_excel("ipca.xlsx", names=cls_ipca, header=None)
ipca = ipca.loc[ipca.loc[:, 'Mês'].isin(meses), :]
ipca.reset_index(inplace=True, drop='True')
ipca.fillna(method='ffill', inplace=True)
for ind, mes in enumerate(meses):
    ipca.loc[ipca.loc[:, 'Mês'] == mes, 'Mês_num'] = ind + 1
# -----------------------------------------------------------------------------
# Dcide
ano_lt = ano_lt_ini

while ano_lt <= ano_lt_fim:
    arq = pasta + f'serie_anual_{ano_lt}.xlsx'
    serie = pd.read_excel(arq, names=cls_dc, header=None, skiprows=3)
    serie = serie.astype({'Semanas': str, "Datas": str, 'Preços': float})
    # -------------------------------------------------------------------------
    rf = 1
    if ano_lt == ano_lt_ini + rf - 1:
        a1 = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
    elif ano_lt > ano_lt_ini + rf - 1:
        an = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
        a1 = pd.concat([a1, an], ignore_index=True)
    # -------------------------------------------------------------------------
    rf = 2
    if ano_lt == ano_lt_ini + rf - 1:
        a2 = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
    elif ano_lt > ano_lt_ini + rf - 1:
        an = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
        a2 = pd.concat([a2, an], ignore_index=True)
    # -------------------------------------------------------------------------
    rf = 3
    if ano_lt == ano_lt_ini + rf - 1:
        a3 = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
    elif ano_lt > ano_lt_ini + rf - 1:
        an = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
        a3 = pd.concat([a3, an], ignore_index=True)
    # -------------------------------------------------------------------------
    rf = 4
    if ano_lt == ano_lt_ini + rf - 1:
        a4 = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
    elif ano_lt > ano_lt_ini + rf - 1:
        an = serie.loc[serie.loc[:, 'Datas'].str.contains(f'{ano_lt - rf}'), :]
        a4 = pd.concat([a4, an], ignore_index=True)
    # ---------------------------------------------------------------------
    ano_lt += 1

a = [a1, a2, a3, a4]

ipca.to_excel('ipca_formatado.xlsx')  # engine='openpyxl')
for ind in range(len(a)):
    a[ind].to_excel(pasta + f'a{ind + 1}.xlsx')  # engine='openpyxl')

del an, a1, a2, a3, a4, ano_lt
# -----------------------.-----------------------------------------------------
# Tratamentos Iniciais
# -----------------------------------------------------------------------------
# Seleção de intervalos de interesse e remoção de "semanas duplas" do histórico
# de PLD.
# Obs: Acrescentar: média ponderada e correção pela inflação (modificar o nome
# das colunas dentro das funções, se necessário).
plds = plds.loc[plds['Ano'] >= data_inicial[0].year, :]
di.tratamento_plds_ccee(plds)  # Remoção das "semanas duplas".
plds.reset_index(inplace=True, drop=True)
# Conversão para formato de datas.
# E compatilização das dimensões, por elimiação de linhas finais, dado que a
# data inicial em 2012 é compatível.
# Se o ano inicial for modificado, verificar a compatibilidade.
if plds.shape[0] > a[0].shape[0]:
    plds = plds.iloc[:a[0].shape[0], :]
for i in range(len(a)):
    a[i].loc[:, cls_dc[1]] = pd.to_datetime(a[i][cls_dc[1]])
    if a[i].shape[0] > plds.shape[0]:
        a[i] = a[i].iloc[:plds.shape[0], :]
# -----------------------------------------------------------------------------
# Correção da Inflação para a Dcide
# -----------------------------------------------------------------------------
# Cópia para a correção do IPCA atual.
a_atual = deepcopy(a)

# Correção até janeiro do ano de realização do contrato.
for j in range(a[0].shape[0]):
    for ind in range(len(a)):
        ano_ori = a[ind].loc[j, 'Datas'].year
        mes_ori = a[ind].loc[j, 'Datas'].month
        num_ori = ipca.query(f'Ano == {ano_ori} and Mês_num == {mes_ori}'
                             )['Número'].values
        ano_ref = ano_ori + ind + 1
        num_ref = ipca.query(f'Ano == {ano_ref} and Mês_num == {1}'
                             )['Número'].values
        # Para anos futuros.
        if ano_ref > ipca.loc[ipca.shape[0] - 1, 'Ano']:
            num_ref = [ipca.loc[ipca.shape[0] - 1, 'Número']]
        # Preços mais recentes, com índices futuros ainda não disponíveis.
        if len(num_ori) == 0:
            num_ori = num_ref
        # Correção pela inflação.
        a[ind].loc[j, 'Preços'] *= num_ref[0] / num_ori[0]

# Correção até a data atual.
num_ref = [ipca.loc[ipca.shape[0] - 1, 'Número']]

for j in range(a_atual[0].shape[0]):
    for ind in range(len(a_atual)):
        ano_ori = a_atual[ind].loc[j, 'Datas'].year
        mes_ori = a_atual[ind].loc[j, 'Datas'].month
        num_ori = ipca.query(f'Ano == {ano_ori} and Mês_num == {mes_ori}'
                             )['Número'].values

        # Preços mais recentes, com índices futuros ainda não disponíveis.
        if len(num_ori) == 0:
            num_ori = num_ref
        # Correção pela inflação.
        a_atual[ind].loc[j, 'Preços'] *= num_ref[0] / num_ori[0]


for ind in range(len(a)):
    a[ind].to_excel(pasta + f'a{ind + 1}_ipca.xlsx')  # engine='openpyxl')
    # a_atual[ind].to_excel(pasta + f'a{ind + 1}_ipca_atual.xlsx',
    #                      'engine='openpyxl')
    a_atual[ind].to_excel(pasta + f'a{ind + 1}_ipca_atual.xlsx')
# ===========================================================================
# %%
# -----------------------------------------------------------------------------
# Impressões.
# -----------------------------------------------------------------------------
a_tipos = [1, 2, 3, 4]
comb = combinations(a_tipos, 2)
anos = [ano for ano in range(2012, 2022)]
cl_prec = 'Pesado SE'  # Coluna da planilha plds a usar como referência.
cores = ['navy', 'firebrick', 'goldenrod', 'dodgerblue']  # Cores das curvas.
legendas = ['A+1', 'A+2', 'A+3', 'A+4']
ang = '-50'
espaços = 15

lim_graf_pld = 500

for i in list(comb):
    lista = [i[0], i[1]]  # Lista de curvas 'A + x' a serem impressas.
    # Lista de curvas 'A + x' que terão setas.
    if i[0] == 1:
        setas = [i[1]]
    else:
        setas = lista
    di.imprimir(a, plds, lista, cl_prec, cores, legendas, data_inicial,
                data_final, setas, ang, lim_graf_pld, pasta, espaços=espaços)

for i in a_tipos:
    lista = [a_tipos[i - 1]]
    if i == 1:
        setas = [0]
    else:
        setas = lista
    di.imprimir(a, plds, lista, cl_prec, cores, legendas, data_inicial,
                data_final, setas, ang, lim_graf_pld, pasta, espaços=espaços)

lista = a_tipos
setas = [0]
di.imprimir(a, plds, lista, cl_prec, cores, legendas, data_inicial,
            data_final, setas, ang, lim_graf_pld, pasta)
# %%

for i in range(4):
    anos = [ano for ano in range(2013 + i, 2022 + i)]
    di.imprimir_tri(a[i], lista, anos, cl_prec, cores[i], legendas[i],
                    data_inicial, data_final, lim_graf_pld, pasta)
    print(f'Impressão {legendas[i]} concluída.')


# %%

# data_imp_i = pd.datetime(year=2016, month=10, day=1)
# data_imp_f = pd.datetime(year=2021, month=9, day=1)
# dcide_med = []
# bbb = a[0]['Datas'].values


# linha_min = (a[0]['Datas'].values == data_imp_i).argmin()
# # linha_max = a[0]['Datas'] == data_imp_f
# # linha_mmmm = linha_min.argmin(True)

# # for i in range(4):
#     dcide_med.append(a[i]['Preços'][linha_min:linha_max].mean())
