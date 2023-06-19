
# importação de bibliotecas
import pandas as pd
import seaborn as sns

# Criação do dataset com os dados do arquivo .csv
data = pd.read_csv('gasolina.csv')

# Criação do gráfico
grafico = sns.lineplot(data, x="dia", y="venda")
grafico.set(title="Preço da gasolina 1 a 10 de Julho 2021",xlabel="Dia", ylabel="Preço")

# Armazenamento da figura gerada
fig = grafico.get_figure()
fig.savefig('gasolina.png', dpi=250)
