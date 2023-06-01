
# importação de bibliotecas
import pandas as pd
import seaborn as sns

# Criação de dataframe
gas_df = pd.read_csv("gasolina.csv")

# Visualização
sns.set_style('whitegrid')
grafico = sns.lineplot(data=gas_df, x='dia', y='venda')
grafico.set(title= 'Gráfico - Preço da gasolina no tempo', xlabel='Dia', ylabel='Preço')

# Armazenamento
fig = grafico.get_figure()
fig.savefig('gasolina.png', dpi=300)
