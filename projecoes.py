"""
Cuidado ao mudar a data inicial
Registro dos formatos necessários para o arquivo de leitura
Futuro: atualizar apenas o necessário.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import estudos_ferramentas as ef
import dcide_impressoes as di
import sklearn.linear_model as lm

# -----------------------------------------------------------------------------
# Definições iniciais.
# -----------------------------------------------------------------------------
cls_dc = ['Semanas', 'Datas', 'Preços']
cls_ipca = ['Ano', 'Mês', 'Número','No Mês', '3 Meses', '6 Meses', 'No Ano',
            '12 Meses']
meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT',
         'NOV', 'DEZ']
data_inicial = pd.DataFrame({'year': [2012], 'month': [1], 'day': [1]})
data_inicial = pd.to_datetime(data_inicial)
data_final = pd.DataFrame({'year': [2020], 'month': [12], 'day': [31]})
data_final = pd.to_datetime(data_final)
# -----------------------------------------------------------------------------
# Leituras.
# -----------------------------------------------------------------------------
plds = pd.read_excel("precos.xlsx")
a = [pd.read_excel("dcide_mpd_a1.xlsx", names=cls_dc, header=None, skiprows=3),
     pd.read_excel("dcide_mpd_a2.xlsx", names=cls_dc, header=None, skiprows=3),
     pd.read_excel("dcide_mpd_a3.xlsx", names=cls_dc, header=None, skiprows=3),
     pd.read_excel("dcide_mpd_a4.xlsx", names=cls_dc, header=None, skiprows=3)]
ipca = pd.read_excel("ipca.xlsx", names=cls_ipca, header=None, skiprows=7)
ipca.dropna(axis=0, how='all', inplace=True)
ipca.reset_index(inplace=True, drop='True')
ipca = ipca.loc[ipca.loc[:, 'Número'].isna()==False, :]
ipca.fillna(method='ffill', inplace=True)
for ind, mes in enumerate(meses):
    ipca.loc[ipca.loc[:, 'Mês']==mes, 'Mês_num'] = ind + 1

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
# Labels e tratamento de NaN.
cols_a_pol = cls_dc[:-1] + ['A1', 'A2', 'A3', 'A4']
a_pol = pd.concat((a[0], a[1]['Preços'], a[2]['Preços'], a[3]['Preços']),
                  axis=1)
a_pol.columns = cols_a_pol
a_pol = a_pol.interpolate()

# %%
# ----------------------------------------------------------------------------
# Relações e diferenças entre as curvas MPD
# ----------------------------------------------------------------------------
a_rel_a2a1 = a_pol.loc[:, 'A2'] / a_pol.loc[:, 'A1']
a_rel_a3a2 = a_pol.loc[:, 'A3'] / a_pol.loc[:, 'A2']
a_rel_a4a3 = a_pol.loc[:, 'A4'] / a_pol.loc[:, 'A3']
ref = np.ones_like(a_rel_a2a1)
a_rel = np.vstack([a_rel_a2a1, a_rel_a3a2, a_rel_a4a3, ref])
a_rel = a_rel.T

a_dif_a2a1 = a_pol.loc[:, 'A2'] - a_pol.loc[:, 'A1']
a_dif_a3a2 = a_pol.loc[:, 'A3'] - a_pol.loc[:, 'A2']
a_dif_a4a3 = a_pol.loc[:, 'A4'] - a_pol.loc[:, 'A3']
a_dif = np.vstack([a_dif_a2a1, a_dif_a3a2, a_dif_a4a3, ref])
a_dif = a_dif.T

cols_a_rel = ['A2/A1', 'A3/A2', 'A4/A3', 'Referência']
cols_a_dif = ['A2-A1', 'A3-A2', 'A4-A3', 'Referência']

a_rel = pd.DataFrame(a_rel, columns = cols_a_rel)
a_rel.index = plds['Data Fim'].values

a_dif = pd.DataFrame(a_dif, columns = cols_a_dif)
a_dif.index = plds['Data Fim'].values


# Impressões
plt.figure()
a_rel.plot(use_index=True, fontsize=20, figsize=(20, 12), lw=3)
plt.legend(cols_a_rel, fontsize=20)
plt.savefig('fig 1 - relacoes.jpg')
plt.close()

a_dif.plot(use_index=True, fontsize=20, figsize=(20, 12), lw=3)
plt.legend(cols_a_dif, fontsize=20)
plt.savefig('fig 1.1 - diferencas.jpg')
plt.close()
# Visualização dos dados em ordem
a_rel_sort = pd.concat([a_rel[col].sort_values().reset_index(drop=True)
                        for col in a_rel.columns], axis =1, ignore_index=True)


# %%
# ----------------------------------------------------------------------------
# Ajuste por polinômios
# ----------------------------------------------------------------------------
a_rel_est = ef.estatisticas(a_rel_sort.values)
a_rel_est.columns = cols_a_rel
a_rel_est.to_excel('projecao.xlsx')

a5 = []
for ind in range(a_pol.shape[0]):
    x = np.array([2020, 2021, 2022, 2023])
    y = a_pol.loc[ind, 'A1':].values.astype('float')
    eq = np.poly1d(np.polyfit(x, y, 2))
    z = eq(2024)
    a5.append(z)

a_pol_res = a_pol.copy()
a_pol_res['A5'] = a5

colunas = ['A+1', 'A+2', 'A+3', 'A+4', 'A+5(estimado)']
a_pol_res.index = plds['Data Fim'].values
plt.figure()
a_pol_res.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
             lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 2 - ajuste por polinomios.jpg')
plt.close()


# %%
# ----------------------------------------------------------------------------
# Relação A5/A4 por polinômios sobre as relações entre as MPDs
# ----------------------------------------------------------------------------

a5p = []

for ind in range(a_rel.shape[0]):
    x = np.array([1, 2, 3])
    y = a_rel.iloc[ind, 0:3].values.astype('float')
    eq = np.poly1d(np.polyfit(x, y, 2))
    z = eq(x[-1] + 1)
    a5p.append(z)

a_rel_res = a_rel.copy()
a_rel_res['A5/A4'] = a5p

cols_a_rel2 = ['A2/A1', 'A3/A2', 'A4/A3', 'Referência', 'A5/A4']
plt.figure()
a_rel_res.plot(use_index=True, fontsize=20, figsize=(20, 12),
             lw=3)
plt.legend(cols_a_rel2, fontsize=20)
plt.savefig('fig 3 - relação A5 A4 por polinomios das relações.jpg')
plt.close()

# %%
# ----------------------------------------------------------------------------
# Ajuste da A+5 pela média das relações
# ----------------------------------------------------------------------------

a_rel_med = a_rel_res.copy()
a_rel_med.drop('Referência', inplace=True, axis=1)
a_rel_med['A5/A4'] = a_rel_med.loc[:, 'A2/A1':'A4/A3'].values.mean(axis=1)

a_pol_med = a_pol_res.copy()
a_pol_med['A5'] = a_rel_med['A5/A4'] * a_pol_med['A4']

a_pol_med.index = plds['Data Fim'].values
plt.figure()
a_pol_med.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
             lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 4 - ajuste pela media das relacoes.jpg')
plt.close()

# %%
# ----------------------------------------------------------------------------
# Ajuste da A+5 pela relação A4/A3
# ----------------------------------------------------------------------------

a_pol_a4a3 = a_pol_res.copy()
a_pol_a4a3['A5'] = a_rel_med['A4/A3'] * a_pol_res['A4']

plt.figure()
a_pol_a4a3.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
              lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 5 - ajuste pela relacaoA4A3.jpg')
plt.close()

# %%
# ----------------------------------------------------------------------------
# Ajuste da A+5 pela lineariazação das médias das relações A3/A2 e A4/A5
# ----------------------------------------------------------------------------
projecaoa5a4 = 0.9588043419399588
p10_a4_media2019 = 0.974382 
fator = projecaoa5a4 * p10_a4_media2019
print(fator)
a_pol_cte = a_pol_res.copy()
a_pol_cte['A5'] = a_pol_med['A4'] * projecaoa5a4

colunas = ['A+1', 'A+2', 'A+3', 'A+4', 'A+5 (estimado)']
plt.figure()
a_pol_cte.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
             lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 6 - ajuste por constante.jpg')
plt.close()

a_pol_cte_p10 = a_pol_res.copy()
a_pol_cte_p10['A5'] = a_pol_med['A4'] * fator

colunas = ['A+1', 'A+2', 'A+3', 'A+4', 'A+5 P10 (estimado)']
plt.figure()
a_pol_cte_p10.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
                  lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 7 - ajuste por constante e p10.jpg')
plt.close()

# %%
# ----------------------------------------------------------------------------
# Relação A5/A4 por polinômios sobre as relações entre as MPDs A2 a A4
# ----------------------------------------------------------------------------

a5p2 = []

for ind in range(a_rel.shape[0]):
    x = np.array([1, 2])
    y = a_rel.iloc[ind, 1:3].values.astype('float')
    eq = np.poly1d(np.polyfit(x, y, 2))
    z = eq(x[-1]+1)
    a5p2.append(z)

a_rel_res2 = a_rel.copy()
a_rel_res2['A5/A4'] = a5p2

cols_a_rel2 = ['A2/A1', 'A3/A2', 'A4/A3', 'Referência', 'A5/A4']
plt.figure()
a_rel_res2.plot(use_index=True, fontsize=20, figsize=(20, 12),
                lw=3)
plt.legend(cols_a_rel2, fontsize=20)
plt.savefig('fig 8 - relação A5 A4 por polinomios das relações a2a3a4.jpg')
plt.close()


# %%
# ----------------------------------------------------------------------------
# Relação A5/A4 por polinômios sobre as diferenças entre as MPDs
# ----------------------------------------------------------------------------

a5pd = []

for ind in range(a_dif.shape[0]):
    x = np.array([1, 2, 3])
    y = a_dif.iloc[ind, 0:3].values.astype('float')
    eq = np.poly1d(np.polyfit(x, y, 2))
    z = eq(x[-1]+1)
    a5pd.append(z)

a_dif_res = a_dif.copy()
a_dif_res['A5-A4'] = a5pd

a5pd.sort()
a5pd_res = np.array(a5pd)
a5pd_est = ef.estatisticas(a5pd_res)

cols_a_rel_d = ['A2-A1', 'A3-A2', 'A4-A3', 'Referência', 'A5-A4']
plt.figure()
a_dif_res.plot(use_index=True, fontsize=20, figsize=(20, 12),
              lw=3)
plt.legend(cols_a_rel_d, fontsize=20)
plt.savefig('fig 3.1 - relação A5 A4 por polinomios das diferenças.jpg')
plt.close()

# %%
# ----------------------------------------------------------------------------
# Relação A5/A4 pela diferença A4 - A3 * A4/A3
# ----------------------------------------------------------------------------

a_dif_rel_a4a3 = a_pol_res.copy()
a_dif_rel_a4a3['A5'] = a_pol_res['A4'] + a_dif['A4-A3'] * a_rel_med['A4/A3']
a_dif_rel_a4a3['A6'] = (a_dif_rel_a4a3['A5'] + (a_dif_rel_a4a3['A5'] -
                        a_pol_res['A4'])* (a_dif_rel_a4a3['A5'] / a_pol_res['A4']))


plt.figure()
a_dif_rel_a4a3.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
              lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 9 - ajuste pela diferença reduzida.jpg')
plt.close()


# %%

a_rel_pos = a_rel['A4/A3'] * (a_rel['A4/A3'] < 1)
a_rel_pos.drop(a_rel_pos[a_rel_pos==0].index, axis=0, inplace=True)
print(a_rel_pos.mean())

a_rel_neg = a_rel['A4/A3'] * (a_rel['A4/A3'] >= 1)
a_rel_neg.drop(a_rel_neg[a_rel_neg==0].index, axis=0, inplace=True)
print(a_rel_neg.mean())

# %%
# ----------------------------------------------------------------------------
# Relação A5/A1 por redução progressiva
# ----------------------------------------------------------------------------

a_rel_a2a1 = a_pol.loc[:, 'A2'] / a_pol.loc[:, 'A1']
a_rel_a3a1 = a_pol.loc[:, 'A3'] / a_pol.loc[:, 'A1']
a_rel_a4a1 = a_pol.loc[:, 'A4'] / a_pol.loc[:, 'A1']
ref = np.ones_like(a_rel_a2a1)
a_rel_a1 = np.vstack([ref, a_rel_a2a1, a_rel_a3a1, a_rel_a4a1])
a_rel_a1 = a_rel_a1.T

z5_t = []
z6_t = []
rscore = []

for ind in range(a_rel_a1.shape[0]):
    x = np.array([2, 3, 4]).T
    y = a_rel_a1[ind, 1:].astype('float')

    reg = np.polyfit(x, y, 1)
    reg_pol = np.poly1d(reg)

    z5 = reg_pol(5)
    z6 = reg_pol(6)

    z5_t.append((z5) * a_pol.loc[ind, 'A1'])
    z6_t.append((z6) * a_pol.loc[ind, 'A1'])

rscore = np.array(rscore)

a_rel_a1_res = a_pol.copy()
a_rel_a1_res['A5'] = np.array(z5_t)
a_rel_a1_res['A6'] = np.array(z6_t)

colunas = ['A+1', 'A+2', 'A+3', 'A+4', 'A+5(estimado)', 'A+6(estimado)']
a_rel_a1_res.index = plds['Data Fim'].values
plt.figure()
a_rel_a1_res.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
                                lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 11 - ajuste por polinomios da progressao.jpg')
plt.close()

# %%
# ----------------------------------------------------------------------------
# Relação A5/A4 pela diferença entre semanas
# ----------------------------------------------------------------------------

a_dif_sem = a_pol_cte.copy()
a_dif_sem.reset_index(inplace=True, drop=True)
a_rel.reset_index(inplace=True, drop=True)

for ind in range(a_dif_sem.shape[0]):
    if ind == 0:
        pass
    else:
        dif = a_dif_sem.loc[ind, 'A4'] - a_dif_sem.loc[ind-1, 'A4']
        dif = dif * a_rel.loc[ind, 'A4/A3']
        a_dif_sem.loc[ind, 'A5'] = a_dif_sem.loc[ind-1, 'A5'] + dif

plt.figure()
a_dif_sem.loc[:, 'A1':].plot(use_index=True, fontsize=20, figsize=(20, 12),
              lw=3)
plt.legend(colunas, fontsize=20)
plt.savefig('fig 12 - soma de diferenças.jpg')
plt.close()
