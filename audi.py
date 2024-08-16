import pymysql
import json
import os
from decimal import Decimal

# Configurações do banco de dados
host = '139.59.39.117'
user = 'sql_digitalclub_'
password = 'GtYDeSxS7Cf3j6NT'
database = 'sql_digitalclub_'

# Conectar ao banco de dados
def connect_db():
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor  # Retornar dicionários em vez de tuplas
    )

# Função para verificar se o arquivo JSON já existe
def verificar_arquivo_json(user_id):
    directory = 'auditoria/'
    filename = f"{directory}usuario_{user_id}.json"
    return os.path.isfile(filename)

# Função para carregar todos os dados necessários de uma vez só
def carregar_dados(connection):
    with connection.cursor() as cursor:
        # Carregar todos os usuários
        cursor.execute("SELECT id, name, email, user, telephone, typeAcc, balance FROM users")
        usuarios = cursor.fetchall()

        # Carregar todos os indicados (networks)
        cursor.execute("SELECT user_id, affiliate_id FROM networks")
        indicados = cursor.fetchall()

        # Carregar todas as entradas financeiras
        cursor.execute("SELECT user_id, value, txid FROM pixtxid WHERE status >= 1")
        entradas = cursor.fetchall()

        # Carregar todas as saídas financeiras
        cursor.execute("SELECT user_id, value, carteira_type FROM saques WHERE status = 1")
        saques = cursor.fetchall()

        # Carregar todas as informações de extratos financeiros (ganhos)
        cursor.execute("SELECT user_id, SUM(value) as total_value, type FROM extracts WHERE status = 1 GROUP BY user_id, type")
        extratos = cursor.fetchall()

    return usuarios, indicados, entradas, saques, extratos

# Função para processar os dados de um usuário
def processar_usuario(user, usuarios, indicados, entradas, saques, extratos):
    user_id = user['id']

    # Verificar se o arquivo JSON já foi criado
    if verificar_arquivo_json(user_id):
        print(f"Arquivo já existente para o usuário ID {user_id}, pulando...")
        return

    # Filtrar os dados do usuário
    user_entradas = [e for e in entradas if e['user_id'] == user_id]
    user_saques = [s for s in saques if s['user_id'] == user_id]
    user_extratos = [ex for ex in extratos if ex['user_id'] == user_id]

    # Calcular as entradas
    entradas_totais = sum(Decimal(e['value']) / Decimal(100) for e in user_entradas)
    entradas_pix = sum(Decimal(e['value']) / Decimal(100) for e in user_entradas if e['txid'] not in ['USDT', 'bonus', 'Nova Licenca'])
    entradas_usdt = sum(Decimal(e['value']) / Decimal(100) for e in user_entradas if e['txid'] == 'USDT')
    entradas_fakes = sum(Decimal(e['value']) / Decimal(100) for e in user_entradas if e['txid'] in ['bonus', 'Nova Licenca'])

    # Calcular as saídas
    saques_totais = sum(Decimal(s['value']) / Decimal(100) for s in user_saques)
    saques_pix = sum(Decimal(s['value']) / Decimal(100) for s in user_saques if s['carteira_type'] == 0)
    saques_usdt = sum(Decimal(s['value']) / Decimal(100) for s in user_saques if s['carteira_type'] == 1)

    # Calcular os ganhos
    ganhos_rendimento = sum(Decimal(ex['total_value']) / Decimal(100) for ex in user_extratos if ex['type'] == 0)
    ganhos_residual = sum(Decimal(ex['total_value']) / Decimal(100) for ex in user_extratos if ex['type'] == 2)

    # Obter o tipo de conta e saldo do usuário
    tipo_conta = classificar_tipo_conta(user['typeAcc'])
    saldo_disponivel = Decimal(user['balance']) / Decimal(100)  # O saldo é armazenado em centavos

    # Processar os níveis do primeiro ao décimo
    niveis = {}
    for nivel in range(1, 11):
        niveis[f'nivel_{nivel}'] = processar_nivel(user_id, usuarios, indicados, entradas, nivel)

    # Salvar os dados do usuário em JSON
    salvar_usuario_em_json(user, tipo_conta, saldo_disponivel, {
        'entradas_totais': entradas_totais,
        'entradas_usdt': entradas_usdt,
        'entradas_fakes': entradas_fakes,
        'entradas_pix': entradas_pix
    }, {
        'saques_totais': saques_totais,
        'saques_pix': saques_pix,
        'saques_usdt': saques_usdt
    }, {
        'ganhos_rendimento': ganhos_rendimento,
        'ganhos_residual': ganhos_residual
    }, niveis)

# Função para processar cada nível de indicado
def processar_nivel(user_id, usuarios, indicados, entradas, nivel_atual):
    if nivel_atual == 0:
        return None

    user_ids = [user_id]
    for _ in range(nivel_atual - 1):
        user_ids = [ind['affiliate_id'] for ind in indicados if ind['user_id'] in user_ids]

    indicados_nivel = [ind['affiliate_id'] for ind in indicados if ind['user_id'] in user_ids]

    total_investido = total_pix = total_usdt = total_fakes = Decimal(0)
    total_normal = total_fake = total_bonus = total_lider = 0

    for indicado_id in indicados_nivel:
        indicado_info = next((u for u in usuarios if u['id'] == indicado_id), None)

        if indicado_info:
            # Classificar o tipo de conta do indicado
            tipo_conta = classificar_tipo_conta(indicado_info['typeAcc'])
            if tipo_conta == 'NORMAL':
                total_normal += 1
            elif tipo_conta == 'FAKE':
                total_fake += 1
            elif tipo_conta == 'BONUS':
                total_bonus += 1
            elif tipo_conta == 'LIDER':
                total_lider += 1

            # Calcular o investimento do indicado
            indicado_entradas = [e for e in entradas if e['user_id'] == indicado_id]
            total_investido += sum(Decimal(e['value']) / Decimal(100) for e in indicado_entradas)
            total_pix += sum(Decimal(e['value']) / Decimal(100) for e in indicado_entradas if e['txid'] not in ['USDT', 'bonus', 'Nova Licenca'])
            total_usdt += sum(Decimal(e['value']) / Decimal(100) for e in indicado_entradas if e['txid'] == 'USDT')
            total_fakes += sum(Decimal(e['value']) / Decimal(100) for e in indicado_entradas if e['txid'] in ['bonus', 'Nova Licenca'])

    return {
        'numero_indicados': len(indicados_nivel),
        'total_normal': total_normal,
        'total_fake': total_fake,
        'total_bonus': total_bonus,
        'total_lider': total_lider,
        'total_investido': float(total_investido),
        'total_pix': float(total_pix),
        'total_usdt': float(total_usdt),
        'total_fakes': float(total_fakes)
    }

# Função para classificar o tipo de conta
def classificar_tipo_conta(type_acc):
    if type_acc == 0:
        return 'NORMAL'
    elif type_acc == 1:
        return 'FAKE'
    elif type_acc == 2:
        return 'BONUS'
    elif type_acc == 3:
        return 'LIDER'
    else:
        return 'NORMAL'

# Função para converter Decimal em float ao salvar no JSON
def decimal_para_float(dados):
    if isinstance(dados, list):
        return [decimal_para_float(item) for item in dados]
    elif isinstance(dados, dict):
        return {chave: decimal_para_float(valor) for chave, valor in dados.items()}
    elif isinstance(dados, Decimal):
        return float(dados)
    else:
        return dados

# Função para salvar dados do usuário em arquivo JSON
def salvar_usuario_em_json(user, tipo_conta, saldo_disponivel, entradas, saidas, ganhos, niveis):
    directory = 'auditoria/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}usuario_{user['id']}.json"

    # Coletar os dados do usuário
    dados_usuario = {
        'nome': user['name'],
        'email': user['email'],
        'usuario': user['user'],
        'contato': user['telephone'],
        'tipo_conta': tipo_conta,
        'saldo_disponivel': float(saldo_disponivel),
        'entradas': entradas,
        'saidas': saidas,
        'ganhos': ganhos,
        'niveis': niveis
    }

    # Converter Decimal para float
    dados_usuario = decimal_para_float(dados_usuario)
    
    # Salvar os dados no arquivo JSON
    with open(filename, 'w') as json_file:
        json.dump(dados_usuario, json_file, indent=4)
    
    print(f"Arquivo JSON criado para o usuário ID {user['id']}")

# Função principal para processar todos os usuários
def processar_todos_usuarios():
    connection = connect_db()
    
    try:
        # Carregar todos os dados de uma só vez
        usuarios, indicados, entradas, saques, extratos = carregar_dados(connection)

        # Processar cada usuário
        for user in usuarios:
            processar_usuario(user, usuarios, indicados, entradas, saques, extratos)

    finally:
        connection.close()

# Iniciar o processo para todos os usuários
if __name__ == "__main__":
    processar_todos_usuarios()
