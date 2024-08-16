import pandas as pd
import json
import os

# Caminho para a pasta com os arquivos JSON
pasta_auditoria = 'auditoria/'

# Função para carregar os dados dos arquivos JSON em um DataFrame
def carregar_dados_json(pasta):
    dados = []
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.json'):
            caminho_arquivo = os.path.join(pasta, arquivo)
            with open(caminho_arquivo, 'r') as f:
                conteudo = json.load(f)
                # Extrai informações do conteúdo JSON
                entradas = conteudo.get('entradas', {})
                saques = conteudo.get('saidas', {})
                ganhos = conteudo.get('ganhos', {})
                niveis = conteudo.get('niveis', {})
                
                # Adiciona uma linha ao DataFrame com os dados extraídos
                dados.append({
                    'nome': conteudo.get('nome'),
                    'email': conteudo.get('email'),
                    'usuario': conteudo.get('usuario'),
                    'contato': conteudo.get('contato'),
                    'tipo_conta': conteudo.get('tipo_conta', 'NORMAL'),
                    'saldo_disponivel': conteudo.get('saldo_disponivel', 0.0),
                    
                    # Entradas
                    'entradas_totais': entradas.get('total', 0) / 100,
                    'entradas_usdt': entradas.get('USDT', 0) / 100,
                    'entradas_fakes': entradas.get('Fakes', 0) / 100,
                    'entradas_pix': entradas.get('PIX', 0) / 100,
                    
                    # Saques
                    'saques_totais': saques.get('total', 0) / 100,
                    'saques_pix': saques.get('PIX', 0) / 100,
                    'saques_usdt': saques.get('USDT', 0) / 100,
                    
                    # Ganhos
                    'ganhos_rendimento': ganhos.get('rendimento', 0) / 100,
                    'ganhos_residual': ganhos.get('residual', 0) / 100,

                    # Níveis
                    **{
                        f'numero_indicados_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('numero_indicados', 0)
                        for i in range(1, 11)
                    },
                    **{
                        f'total_normal_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_normal', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_fake_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_fake', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_bonus_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_bonus', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_lider_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_lider', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_investido_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_investido', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_pix_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_pix', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_usdt_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_usdt', 0) / 100
                        for i in range(1, 11)
                    },
                    **{
                        f'total_fakes_NIVEL{i:02d}': niveis.get(f'nivel_{i}', {}).get('total_fakes', 0) / 100
                        for i in range(1, 11)
                    },
                })
    return pd.DataFrame(dados)

# Função para salvar os dados em um arquivo Excel
def salvar_em_excel(dataframe, nome_arquivo):
    dataframe.to_excel(nome_arquivo, index=False, engine='openpyxl')

def main():
    # Carregar os dados dos arquivos JSON
    df = carregar_dados_json(pasta_auditoria)
    
    # Nome do arquivo Excel de saída
    arquivo_excel = 'dados_auditoria.xlsx'
    
    # Salvar os dados no arquivo Excel
    salvar_em_excel(df, arquivo_excel)
    print(f"Dados salvos em {arquivo_excel}")

if __name__ == "__main__":
    main()
