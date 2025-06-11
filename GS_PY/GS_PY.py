# =========================================================================================
# Integrantes
# =========================================================================================
'''
Thiago Mendes     RM555352
Guilherme Britto  RM558475
João Santis       RM555287
'''

# Importações
import os 
import re
import oracledb
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================================================
# Objetivo do projeto
# =========================================================================================
"""
O GREEN ENERGY PROVIDER é uma plataforma digital desenvolvida para agricultores de médio e grande porte, com o objetivo de facilitar a adoção de energia solar e promover a sustentabilidade no 
agronegócio. A ferramenta utiliza simulações personalizadas e precisas, baseadas em dados reais como consumo energético e orçamento disponível, para apresentar projeções detalhadas de economia 
financeira, tempo de retorno sobre o investimento (payback) e redução de emissões de carbono.

OBJETIVO GERAL

Fornecer uma solução acessível, prática e eficiente que auxilie os agricultores na transição para fontes de energia renovável, 
otimizando custos e ampliando os impactos positivos no meio ambiente e na economia rural.
"""

# =========================================================================================
# Conexão com o Banco de Dados Oracle
# =========================================================================================
try:
    conn = oracledb.connect(user="RM555352", password="260606", dsn="oracle.fiap.com.br:1521/ORCL")
    cursor = conn.cursor()
    conexao = True
except Exception as e:
    conexao = False
    print(f"Erro de conexão: {e}")


# =========================================================================================
# Funções de Utilidade
# =========================================================================================
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def validar_numero(numero):
    try:
        return float(numero) > 0
    except ValueError:
        return False

def checagem_nome(nome: str) -> bool:
    if not isinstance(nome, str) or len(nome) == 0:
        return False
    partes = nome.split()
    return len(partes) >= 2 and all(part.isalpha() for part in partes)

def validar_nome(nome):
    if not checagem_nome(nome):
        return False

def validar_senha(senha):
    if len(senha) < 8 or len(senha) > 16:
        return False
    return True

def validar_email(email):
    padrao = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(com|org)$'
    return re.match(padrao, email)

def validar_condicao(condicao):
    return 1 <= condicao <= 3

estados_UF = [
    "AC",  # Acre
    "AL",  # Alagoas
    "AP",  # Amapá
    "AM",  # Amazonas
    "BA",  # Bahia
    "CE",  # Ceará
    "DF",  # Distrito Federal
    "ES",  # Espírito Santo
    "GO",  # Goiás
    "MA",  # Maranhão
    "MT",  # Mato Grosso
    "MS",  # Mato Grosso do Sul
    "MG",  # Minas Gerais
    "PA",  # Pará
    "PB",  # Paraíba
    "PR",  # Paraná
    "PE",  # Pernambuco
    "PI",  # Piauí
    "RJ",  # Rio de Janeiro
    "RN",  # Rio Grande do Norte
    "RS",  # Rio Grande do Sul
    "RO",  # Rondônia
    "RR",  # Roraima
    "SC",  # Santa Catarina
    "SP",  # São Paulo
    "SE",  # Sergipe    
    "TO"   # Tocantins
]


# =========================================================================================
# Funções de Exportação
# =========================================================================================
def exportar_para_excel(df_resultados, nome_arquivo_excel='resultados_simulacoes.xlsx'):
    """
    Exporta os resultados das simulações para o formato Excel.

    Parâmetros:
    df_resultados (pd.DataFrame): DataFrame contendo os resultados das simulações.
    nome_arquivo_excel (str): Nome do arquivo Excel a ser salvo (padrão: 'resultados_simulacoes.xlsx').
    """
    colunas_resultados = ['simulacao_id', 'custo_investimento', 'economia_anual', 'tempo_para_lucro_anos', 'economia_mensal_R$', 'reducao_carbono_KG']
    
    if all(coluna in df_resultados.columns for coluna in colunas_resultados):
        if df_resultados.empty:
            print("Erro: O DataFrame está vazio. Não há dados para exportar.")
            return
        
        try:
            df_resultados[colunas_resultados].to_excel(nome_arquivo_excel, index=False)
            print(f"Resultados exportados para {nome_arquivo_excel}")
        except Exception as e:
            print(f"Erro ao exportar para Excel: {e}")
    else:
        print("Erro: O DataFrame não contém as colunas necessárias para os cálculos!")

def exportar_para_json(df_resultados, nome_arquivo_json='resultados_simulacoes.json'):
    """
    Exporta os resultados das simulações para o formato JSON.

    Parâmetros:
    df_resultados (pd.DataFrame): DataFrame contendo os resultados das simulações.
    nome_arquivo_json (str): Nome do arquivo JSON a ser salvo (padrão: 'resultados_simulacoes.json').
    """
    colunas_resultados = ['simulacao_id', 'custo_investimento', 'economia_anual', 'tempo_para_lucro_anos', 'economia_mensal_R$', 'reducao_carbono_KG']
    
    if all(coluna in df_resultados.columns for coluna in colunas_resultados):
        if df_resultados.empty:
            print("Erro: O DataFrame está vazio. Não há dados para exportar.")
            return
        
        try:
            if not nome_arquivo_json.endswith('.json'):
                nome_arquivo_json = nome_arquivo_json.rsplit('.', 1)[0] + '.json'
            
            df_resultados[colunas_resultados].to_json(nome_arquivo_json, orient='records', lines=True)
            print(f"Resultados exportados para {nome_arquivo_json}")
        except Exception as e:
            print(f"Erro ao exportar para JSON: {e}")
    else:
        print("Erro: O DataFrame não contém as colunas necessárias para os cálculos!")


# =========================================================================================
# Funções de Simulação
# =========================================================================================
def criar_simulacao(usuario_id, nome, tamanho_disp, estado, consumo, orcamento):
    custo_por_m2 = 1000  # Custo do sistema por metro quadrado de painel solar (em R$)
    producao_por_m2 = 150  # Produção de energia por m² de painel solar por ano (em kWh)
    preco_kwh = 0.50  # Preço médio de venda da energia em R$ por kWh

    # Verificação de valores de entrada
    if tamanho_disp <= 0 or consumo <= 0 or orcamento <= 0:
        print("Erro: Todos os valores de entrada devem ser positivos.")
        return

    custo_investimento = tamanho_disp * custo_por_m2
    energia_gerada_anual = producao_por_m2 * tamanho_disp
    economia_anual = (min(consumo * 12, energia_gerada_anual) * preco_kwh) * 5 

    # Verifica se o orçamento é suficiente
    if orcamento < custo_investimento:
        print(f"\nAVISO: O seu orçamento de R${orcamento} não é suficiente para cobrir o custo de R${custo_investimento}. Faltam R${custo_investimento - orcamento:.2f}.")
    else:
        print(f"\nParabéns! O seu orçamento de R${orcamento} é suficiente para cobrir o custo de R${custo_investimento}.\n")

    try:
        query = """
        INSERT INTO simulacoes (usuario_id, nome, tamanho_disp, estado, consumo, orcamento, custo_investimento, economia_anual)
        VALUES (:usuario_id, :nome, :tamanho_disp, :estado, :consumo, :orcamento, :custo_investimento, :economia_anual)
        """
        cursor.execute(query, {
            'usuario_id': usuario_id,
            'nome': nome,
            'tamanho_disp': tamanho_disp,
            'estado': estado,
            'consumo': consumo,
            'orcamento': orcamento,
            'custo_investimento': custo_investimento,
            'economia_anual': economia_anual
        })
        conn.commit()
        print("Simulação criada com sucesso!")
        
        input("Pressione Enter para continuar...")
    except Exception as e:
        print(f"Erro ao inserir simulação: {e}")

def deletar_simulacao(simulacao_id, usuario_id_logado):
    try:
        # Consultar a simulação no banco de dados
        print(f"Consultando simulação com ID {simulacao_id}...")
        query = "SELECT usuario_id FROM simulacoes WHERE simulacao_id = :simulacao_id"
        cursor.execute(query, {'simulacao_id': simulacao_id})
        simulacao = cursor.fetchone()

        if simulacao is None:
            print(f"Simulação com ID {simulacao_id} não encontrada.")
            return

        # Verificar se a simulação pertence ao usuário logado
        if simulacao[0] != usuario_id_logado:  # Aqui estamos acessando o primeiro valor da tupla
            print("Você não tem permissão para inativar esta simulação.")
            return

        # Se o usuário tem permissão, marcar a simulação como inativa
        query = """
        UPDATE simulacoes
        SET ativo = 'F'
        WHERE simulacao_id = :simulacao_id
        """
        
        cursor.execute(query, {'simulacao_id': simulacao_id})
        conn.commit()
        print(f"Simulação {simulacao_id} excluida com sucesso.")
    
    except Exception as e:
        print(f"Erro ao tentar inativar simulação: {e}")

def editar_simulacao(simulacao_id, usuario_id_logado):
    try:
        # Consultar a simulação no banco de dados para verificar a propriedade
        print(f"Consultando simulação com ID {simulacao_id}...")
        query = "SELECT usuario_id FROM simulacoes WHERE simulacao_id = :simulacao_id AND ativo = 'T'"
        cursor.execute(query, {'simulacao_id': simulacao_id})
        simulacao = cursor.fetchone()

        if simulacao is None:
            print(f"Simulação com ID {simulacao_id} não encontrada.")
            return

        print(f"Simulação encontrada: {simulacao}")

        # Verificar se a simulação pertence ao usuário logado
        if simulacao[0] != usuario_id_logado:  # A coluna 'usuario_id' está no índice 10
            print("Você não tem permissão para alterar esta simulação.")
            return

        # Receber novos dados para atualização
        limpar_tela()

        nome = input("Novo nome da simulação: ")
        while not nome.strip():  # Valida se o nome da simulação não está vazio
            print("Nome da simulação inválido!.")
            nome = input("Novo nome da simulação: ")

        tamanho_disp = input("Novo tamanho disponível (em m²): ")
        while not validar_numero(tamanho_disp):  # Valida tamanho disponível
            print("Tamanho inválido. Insira um número válido.")
            tamanho_disp = input("Novo tamanho disponível (em m²): ")
        tamanho_disp = float(tamanho_disp)

        estado = input("Novo estado (UF): ").upper()
        while estado not in estados_UF:  # Valida se o estado tem 2 caracteres
            print("Estado inválido! Digite a sigla do estado (ex: SP).")
            estado = input("Novo estado (UF): ").upper()

        consumo = input("Novo consumo energético (em kWh): ")
        while not validar_numero(consumo):  # Valida consumo energético
            print("Consumo inválido. Insira um número válido.")
            consumo = input("Novo consumo energético (em kWh): ")
        consumo = float(consumo)

        orcamento = input("Novo orçamento disponível: R$ ")
        while not validar_numero(orcamento):  # Valida orçamento
            print("Orçamento inválido. Insira um número válido.")
            orcamento = input("Novo orçamento disponível: R$ ")
        orcamento = float(orcamento)

        # Atualizar os dados no banco de dados
        query = """
        UPDATE simulacoes
        SET nome = :nome, tamanho_disp = :tamanho_disp, estado = :estado, 
            consumo = :consumo, orcamento = :orcamento
        WHERE simulacao_id = :simulacao_id
        """
        cursor.execute(query, {
            'nome': nome,
            'tamanho_disp': tamanho_disp,
            'estado': estado,
            'consumo': consumo,
            'orcamento': orcamento,
            'simulacao_id': simulacao_id
        })
        conn.commit()

        print(f"Simulação atualizada com sucesso.")

    except Exception as e:
        print(f"Erro ao tentar atualizar simulação: {e}")


# =========================================================================================
# Funções de Cálculo
# =========================================================================================
def calcular_economias(simulacao_data):
    df = pd.DataFrame(simulacao_data)
    
    # Calcular o tempo para lucro (em anos), usando a economia anual diretamente
    df['tempo_para_lucro_anos'] = df.apply(
        lambda row: calcular_tempo_para_lucro(row['custo_investimento'], row['economia_anual']), 
        axis=1
    )
    
    # Calcular a economia mensal: dividindo a economia anual por 12
    df['economia_mensal_R$'] = df['economia_anual'] / 12
    
    # Calcular a redução de carbono (em kg): assume que cada kWh reduz 0.2 kg de CO₂
    df['reducao_carbono_KG'] = df['consumo'] * 0.2
    
    # Adicionar uma coluna de 'rentabilidade' para indicar o retorno do investimento (se desejado)
    df['rentabilidade'] = (df['economia_anual'] / df['custo_investimento']) * 100  # Rentabilidade em %
    
    # Validar se há algum valor negativo ou zero em variáveis críticas (evitar erros em cálculos)
    df['tempo_para_lucro_anos'] = df['tempo_para_lucro_anos'].apply(lambda x: max(x, 0) if pd.notnull(x) else 0)
    df['economia_mensal_R$'] = df['economia_mensal_R$'].apply(lambda x: max(x, 0) if pd.notnull(x) else 0)
    df['reducao_carbono_KG'] = df['reducao_carbono_KG'].apply(lambda x: max(x, 0) if pd.notnull(x) else 0)

    return df

def calcular_tempo_para_lucro(custo_investimento, economia_anual):
    """
    Calcula o tempo necessário para que a economia anual ultrapasse o custo do investimento,
    sem considerar o orçamento, apenas com o acúmulo da economia anual.
    """
    # Calcular o tempo para lucro em anos, dividindo o custo de investimento pela economia anual
    tempo_anos = custo_investimento / economia_anual
    return round(tempo_anos, 2)

def gerar_aviso(df):
    return df[['simulacao_id', 'custo_investimento', 'economia_anual', 'tempo_para_lucro_anos', 'economia_mensal_R$', 'reducao_carbono_KG']]


# =========================================================================================
# Funções de Exibição e Consultas
# =========================================================================================
def listar_colunas_linhas(usuario_id):
    """
    Função para listar as colunas e linhas dos dados fornecidos pelo usuário
    e aplicar filtros nas consultas.
    """
    os.system("cls")
    print(""" 
--------------------------------      
Escolha a/as coluna/as          
para serem exibidas:           
                               
1 - Nome da simulação          
2 - Estado                     
3 - Tamanho disponível         
4 - Consumo                    
5 - Orçamento
6 - Todas                    
0 - Ir para filtragem           
""")          
    colunas_filtro = []
    
    escolhas = 'x'
    while escolhas != '0':
        escolhas = input("Opções: ")
        match escolhas:
            case '1':
                colunas_filtro.append("NOME")
            case '2':
                colunas_filtro.append("ESTADO")
            case '3':
                colunas_filtro.append("TAMANHO_DISP")
            case '4':
                colunas_filtro.append("CONSUMO")
            case '5':
                colunas_filtro.append("ORCAMENTO")
            case '6':
                colunas_filtro = ["NOME", "ESTADO", "TAMANHO_DISP", "CONSUMO", "ORCAMENTO"]
                break
            case '0':
                break
            case _:
                print("Opção inválida! Tente novamente.")
                continue

    escolha = 'x'
    while escolha not in ['1', '2', '3', '4', '5']:
        escolha = input("\nA partir de qual coluna deseja filtrar: ")
        if escolha not in ['1', '2', '3', '4', '5']:
            print("Opção inválida! Tente novamente.")

    match escolha:
        case '1':
            comeco_nome = input("Digite uma parte do Nome: ")
            print("-"*100)
            listar_dados(usuario_id, 'nome', comeco_nome, condicao='LIKE', coluna_retorno=colunas_filtro)
            print("-"*100)
            input("Pressione ENTER para seguir...")
        
        case '2':
            estado = input("Digite uma parte do Estado(UF): ").upper()
            print("-"*100)
            listar_dados(usuario_id, 'estado', estado, condicao='LIKE', coluna_retorno=colunas_filtro)
            print("-"*100)
            input("Pressione ENTER para seguir...")
        
        case '3':
            print("-"*100)
            tamanho = input("Tamanho de Referência: ")
            while not validar_numero(tamanho):
                print("Tamanho inválido.")
                tamanho = input("Tamanho de Referência: ")
            
            print("""---------------------------------      
1 - Maior que o tamanho informado |
2 - Menor que o tamanho informado |
3 - Entre dois tamanhos           |
            """)
            condicao = input("Escolha a condição: ")
            while condicao not in ['1', '2', '3']:
                print("Opção inválida! Tente novamente.")
                condicao = input("Escolha a condição: ")
            
            match condicao:
                case '1':
                    print("-"*100)
                    listar_dados(usuario_id, 'tamanho_disp', float(tamanho), condicao='>', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
                case '2':
                    print("-"*100)
                    listar_dados(usuario_id, 'tamanho_disp', float(tamanho), condicao='<', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
                case '3':
                    tamanho2 = input("Tamanho limite: ")
                    while not validar_numero(tamanho2):
                        print("Insira os dados corretos!")
                        tamanho2 = input("Tamanho limite: ")
                        
                    print("-"*100)    
                    listar_dados(usuario_id, 'tamanho_disp', (float(tamanho), float(tamanho2)), condicao='BETWEEN', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
        
        case '4':
            print("-"*100)
            consumo = input("\nConsumo: ")
            while not validar_numero(consumo):
                print("Consumo inválido.")
                consumo = input("Consumo: ")
            
            print("""---------------------------------      
1 - Maior que o consumo informado |
2 - Menor que o consumo informado |
3 - Entre dois consumos           |
            """)
            condicao = input("Escolha a condição: ")
            while condicao not in ['1', '2', '3']:
                print("Opção inválida! Tente novamente.")
                condicao = input("Escolha a condição: ")
            
            match condicao:
                case '1':
                    print("-"*100)
                    listar_dados(usuario_id, 'consumo', float(consumo), condicao='>', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
                case '2':
                    print("-"*100)
                    listar_dados(usuario_id, 'consumo', float(consumo), condicao='<', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
                case '3':
                    consumo2 = input("Consumo limite: ")
                    while not validar_numero(consumo2):
                        print("Insira os dados corretos!")
                        consumo2 = input("Consumo limite: ")
                        
                    print("-"*100)    
                    listar_dados(usuario_id, 'consumo', (float(consumo), float(consumo2)), condicao='BETWEEN', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
        
        case '5':
            print("-"*100)
            orcamento = input("\nOrçamento: ")
            while not validar_numero(orcamento):
                print("Orçamento inválido.")
                orcamento = input("Orçamento: ")
            
            print("""---------------------------------      
1 - Maior que o orçamento informado |
2 - Menor que o orçamento informado |
3 - Entre dois orçamentos           |
            """)
            condicao = input("Escolha a condição: ")
            while condicao not in ['1', '2', '3']:
                print("Opção inválida! Tente novamente.")
                condicao = input("Escolha a condição: ")
            
            match condicao:
                case '1':
                    print("-"*100)
                    listar_dados(usuario_id, 'orcamento', float(orcamento), condicao='>', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
                case '2':
                    print("-"*100)
                    listar_dados(usuario_id, 'orcamento', float(orcamento), condicao='<', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")
                case '3':
                    orcamento2 = input("Orçamento limite: ")
                    while not validar_numero(orcamento2):
                        print("Insira os dados corretos!")
                        orcamento2 = input("Orçamento limite: ")
                        
                    print("-"*100)    
                    listar_dados(usuario_id, 'orcamento', (float(orcamento), float(orcamento2)), condicao='BETWEEN', coluna_retorno=colunas_filtro)
                    input("Pressione Enter...")

def listar_todos_dados(usuario_id):
    # Inicia a query para selecionar todos os dados de simulações
    query = "SELECT * FROM simulacoes WHERE usuario_id = :usuario_id AND ativo = 'T'"
    params = {'usuario_id': usuario_id}
    
    # Executa a consulta no banco de dados
    cursor.execute(query, params)
    
    # Obtém os dados e as colunas
    data = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    
    # Cria um DataFrame a partir dos dados recuperados
    df = pd.DataFrame(data, columns=colunas)
    
    # Exibe a lista de simulações, ou uma mensagem caso não haja dados
    if df.empty:
        print("Nenhum dado encontrado.")
    else:
        print(df)

def listar_dados(usuario_id, coluna=None, valor=None, condicao=None, coluna_retorno=None):
    # Inicia a query com o filtro pelo usuario_id
    query = "SELECT * FROM simulacoes WHERE usuario_id = :usuario_id AND ativo = 'T'"
    params = {'usuario_id': usuario_id}

    # Aplica outros filtros se forem passados como argumentos
    if coluna and valor:
        if condicao == 'LIKE':
            query += f" AND {coluna} LIKE :valor"
            params['valor'] = f"%{valor}%"
        elif condicao == 'BETWEEN':
            query += f" AND {coluna} BETWEEN :inicio AND :fim"
            params['inicio'], params['fim'] = valor
        elif condicao == '>':
            query += f" AND {coluna} > :valor"
            params['valor'] = valor
        elif condicao == '<':
            query += f" AND {coluna} < :valor"
            params['valor'] = valor
        else:
            query += f" AND {coluna} = :valor"
            params['valor'] = valor

    cursor.execute(query, params)
    data = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=colunas)

    if coluna_retorno:
        coluna_retorno = [col for col in coluna_retorno if col in df.columns]
        df = df[coluna_retorno]

    print("Nenhum dado encontrado." if df.empty else df)

def acessar_economias(df):
    plt.figure(figsize=(10, 6))
    
    # Gráfico único: Tempo para começar a gerar lucro em anos
    plt.barh(df['nome'], df['tempo_para_lucro_anos'], color='lightcoral', edgecolor='black')
    plt.title('Tempo para Começar a Gerar Lucro (em Anos)', fontsize=14)
    plt.xlabel('Tempo para Lucro (anos)', fontsize=12)
    plt.ylabel('Simulações', fontsize=12)

    plt.tight_layout()
    plt.show()

def consultar_simulacoes(usuario_id):
    try:
        query = "SELECT * FROM simulacoes WHERE usuario_id = :usuario_id AND ativo = 'T'"
        cursor.execute(query, {'usuario_id': usuario_id})
        simulacoes = cursor.fetchall()
        if not simulacoes:
            print("-----------------------------------------------------------")
            print("Nenhuma simulação encontrada.")
            input("Pressione Enter...")
            return None
        else:
            df_simulacoes = pd.DataFrame(simulacoes, columns=['simulacao_id', 'nome', 'tamanho_disp', 'estado', 'consumo', 'orcamento', 'custo_investimento', 'economia_anual', 'data','usuario_id', 'ativo'])
            print("\n----------------------------------------------------------------------------------------------------------------------------------------------")
            print(df_simulacoes)
            return df_simulacoes
    except Exception as e:
        print(f"Erro ao consultar simulações: {e}")
        input("Pressione Enter...")
        return None


# =========================================================================================
# Funções de Cadastro e Login
# =========================================================================================
def cadastrar_usuario():
    """
    Função para cadastrar um novo usuário no sistema.
    Valida o nome, email e senha antes de inserir os dados no banco de dados.
    """
    limpar_tela()
    print("""-----------------------------------------------------------
                        CADASTRO""")
    
    # Nome
    nome = input("Nome: ")
    while validar_nome(nome) == False:
        print("Formato de nome Inválido! (ex: Antonio Aguiar)")
        nome = input("Nome: ")
    
    # Email
    email = input("Email: ")
    while not validar_email(email):
        print("Email Inválido! (ex: antonio22@gmail.com)")
        email = input("Email: ")
        
    # Senha
    senha = input("Senha (8-16 caracteres): ")
    while not validar_senha(senha):
        print("Senha Inválida! Siga as exigências")
        senha = input("Senha (8-16 caracteres): ")

    try:
        query = "INSERT INTO usuarios (nome, email, senha) VALUES (:nome, :email, :senha)"
        cursor.execute(query, {"nome": nome, "email": email, "senha": senha})
        conn.commit()
        print(f"Usuário {nome} cadastrado com sucesso!")
        input("Pressione Enter para continuar...")

        # Retorna o ID do novo usuário
        query = "SELECT usuario_id FROM usuarios WHERE email = :email"
        cursor.execute(query, {'email': email})
        usuario_id = cursor.fetchone()[0]
        return usuario_id
    except oracledb.IntegrityError:
        print("Erro: Email já cadastrado. Tente novamente.")
        input("Pressione Enter para continuar...")
        return None
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        return None


def login():
    """
    Função de login para usuários no sistema.
    Realiza a validação do email e senha e retorna o ID do usuário logado.
    """
    while True:
        limpar_tela()
        print("""-----------------------------------------------------------
                        LOGIN""")
        email = input("Email: ")
        while not validar_email(email):
            print("Email Inválido! (ex: antonio22@gmail.com)")
            email = input("Email: ")
            
        senha = input("Senha (8-16 caracteres): ")
        while not validar_senha(senha):
            print("Senha Inválida! Siga as exigências")
            senha = input("Senha (8-16 caracteres): ")
        
        try:
            query = "SELECT usuario_id FROM usuarios WHERE email = :email AND senha = :senha"
            cursor.execute(query, {'email': email, 'senha': senha})
            user = cursor.fetchone()
            if user:
                print("Login realizado com sucesso!")
                input("Pressione Enter para continuar...")
                return user[0]  # Retorna o ID do usuário logado
            else:
                print("Dados não encontrados!")
                opcao = input("Deseja se cadastrar? 1 (sim) 2 (não): ")
                while opcao not in ['1', '2']:
                    print("Opção inválida!")
                    opcao = input("Deseja se cadastrar? 1 (sim) 2 (não): ")
                
                if opcao == '1':
                    usuario_id = cadastrar_usuario()  # Cadastro do novo usuário
                    if usuario_id:  # Se o cadastro for bem-sucedido
                        return usuario_id
                    else:
                        print("Cadastro não realizado corretamente.")
                        continue
                elif opcao == '2':
                    print("Tentando novamente o login...")
                    continue
        except Exception as e:
            print(f"Erro ao realizar login: {e}")
            return None


# =========================================================================================
# Funções do Menu Principal
# =========================================================================================
def menu(usuario_id):
    """
    Função que exibe o menu principal e permite ao usuário interagir com o sistema.
    Dependendo da escolha, são exibidas opções de consultar, editar ou criar simulações.
    """
    while conexao:
        limpar_tela()
        print("""-----------------------------------------------------------
                    Green Energy Provider

Bem-vindo ao Simulador de Introdução de energia sustentável

1 - Consultar Simulações
2 - Editar/Excluir Simulações
3 - Realizar Simulação
4 - Sobre Nós (Recomendado)
5 - Exportações de dados (Excel | JSON)
0 - Sair
""")
        opcao = input("Escolha uma opção: ")

        match opcao:
            case '1':
                limpar_tela()
                
                # Solicitar a escolha entre consultar dados ou resultados de análises
                escolha = 'x'
                while escolha not in ['1', '2']:  # Valida se a escolha é 1 ou 2
                    escolha = input("Consultar dados Fornecidos(1) Consultar resultados das Análises(2): ")
                    if escolha not in ['1', '2']:
                        print("Opção inválida! Tente novamente.")
                
                match escolha:
                    case '1':
                        listar_colunas_linhas(usuario_id)
                    case '2':
                        df_simulacoes = consultar_simulacoes(usuario_id)
                        if df_simulacoes is not None:
                            df_economias = calcular_economias(df_simulacoes)
                            aviso = gerar_aviso(df_economias)
                            print("-"*142)
                            print("\nRelatório de Economias e Redução de Carbono:\n")
                            print("-"*123)
                            print(aviso)
                            acessar_economias(df_economias)
                            print("-"*123)
                            input("Pressione Enter...")

            case '2':
                limpar_tela()
                print("----------------------------------------------------------------------------------------------------------------------------------------------------")
                listar_todos_dados(usuario_id)
                print("----------------------------------------------------------------------------------------------------------------------------------------------------")
                
                alteracao = 'x'
                while alteracao not in ['1', '2', '']:  # Validando se a escolha é 1, 2 ou Enter
                    alteracao = input("\nEditar(1) Excluir(2) Menu(Enter): ")
                    if alteracao not in ['1', '2', '']:
                        print("Opção inválida! Tente novamente.")
                
                match alteracao:
                    case '1':
                        id_alterar = input("\nID para edição: ")
                        while not validar_numero(id_alterar):  # Valida se o ID é um número inteiro
                            print("Digite um numero inteiro válido!")
                            id_alterar = input("\nID da simulação: ")
                        id_alterar = int(id_alterar)
                        
                        editar_simulacao(id_alterar, usuario_id)
                        input("\nPressione Enter...")

                    case '2':
                        id_inativar = input("\nID da simulação: ")
                        while not validar_numero(id_inativar):  # Valida se o ID é um número inteiro
                            print("Digite um numero inteiro válido!")
                            id_inativar = input("\nID da simulação: ")
                        id_inativar = int(id_inativar)
                        
                        deletar_simulacao(id_inativar, usuario_id)
                        input("\nPressione Enter...")
                        
            case '3':
                limpar_tela()
                print("-----------------------------------------------------------")
                
                nome = input("Nome da simulação: ")
                while not nome.strip():  # Valida se o nome da simulação não está vazio
                    print("Nome da simulação inválido!.")
                    nome = input("Nome da simulação: ")

                tamanho_disp = input("Tamanho disponível (em m²): ")
                while not validar_numero(tamanho_disp):  # Valida tamanho disponível
                    print("Tamanho inválido. Insira um número válido.")
                    tamanho_disp = input("Tamanho disponível (em m²): ")
                tamanho_disp = float(tamanho_disp)
                
                estado = input("Estado (UF): ").upper()
                while estado not in estados_UF:  # Valida se o estado tem 2 caracteres
                    print("Estado inválido! Digite a sigla do estado (ex: SP).")
                    estado = input("Estado (UF): ").upper()

                consumo = input("Consumo energético (em kWh): ")
                while not validar_numero(consumo):  # Valida consumo energético
                    print("Consumo inválido. Insira um número válido.")
                    consumo = input("Consumo energético (em kWh): ")
                consumo = float(consumo)
                
                orcamento = input("Orçamento disponível: R$")
                while not validar_numero(orcamento):  # Valida orçamento
                    print("Orçamento inválido. Insira um número válido.")
                    orcamento = input("Orçamento disponível: ")
                orcamento = float(orcamento)
                
                criar_simulacao(usuario_id,nome,tamanho_disp,estado,consumo,orcamento)

            case '4':
                limpar_tela()
                print("""--------------------------------------------------------------------------------------------------
                                            SOBRE NÓS
                        
Somos uma empresa dedicada a fornecer soluções de energia sustentável para fazendas e propriedades 
rurais. Nosso objetivo é otimizar o consumo energético e reduzir os impactos ambientais através de
simulações de economia e eficiência energética como incentivo para a adoção de energia solar.
                """)
                input("Pressione Enter...")
            
            case '5':
                print("""\n-------------------------------------------------
1 - Excel
2 - JSON
3 - Ambos
Enter - Menu
""")
                decisao = input("Opção: ")
                
                match(decisao):
                    
                    case '1':
                        # Exporta somente para Excel
                        df_simulacoes = consultar_simulacoes(usuario_id)
                        if df_simulacoes is not None:
                            df_economias = calcular_economias(df_simulacoes)
                            if isinstance(df_economias, pd.DataFrame):
                                aviso = gerar_aviso(df_economias)
                                if isinstance(aviso, pd.DataFrame):
                                    print("-" * 142)
                                    nome_arq = input("Nome do Arquivo (Por padrão 'resultados_simulacoes'): ") or "resultados_simulacoes.xlsx"
                                    if not nome_arq.endswith('.xlsx'):
                                        nome_arq += '.xlsx'
                                    exportar_para_excel(aviso, nome_arquivo_excel=nome_arq)
                                else:
                                    print("Erro: 'gerar_aviso' não retornou um DataFrame válido!")
                            else:
                                print("Erro: 'calcular_economias' não retornou um DataFrame válido!")
                        else:
                            print("Nenhum dado para ser exportado!")
                    
                    case '2':
                        # Exporta somente para JSON
                        df_simulacoes = consultar_simulacoes(usuario_id)
                        if df_simulacoes is not None:
                            df_economias = calcular_economias(df_simulacoes)
                            if isinstance(df_economias, pd.DataFrame):
                                aviso = gerar_aviso(df_economias)
                                if isinstance(aviso, pd.DataFrame):
                                    print("-" * 142)
                                    nome_arq = input("Nome do Arquivo (Por padrão 'resultados_simulacoes'): ") or "resultados_simulacoes.json"
                                    if not nome_arq.endswith('.json'):
                                        nome_arq += '.json'
                                    exportar_para_json(aviso, nome_arquivo_json=nome_arq)
                                else:
                                    print("Erro: 'gerar_aviso' não retornou um DataFrame válido!")
                            else:
                                print("Erro: 'calcular_economias' não retornou um DataFrame válido!")
                        else:
                            print("Nenhum dado para ser exportado!")
                    
                    case '3':
                        # Exporta para ambos (Excel e JSON)
                        df_simulacoes = consultar_simulacoes(usuario_id)
                        if df_simulacoes is not None:
                            df_economias = calcular_economias(df_simulacoes)
                            if isinstance(df_economias, pd.DataFrame):
                                aviso = gerar_aviso(df_economias)
                                if isinstance(aviso, pd.DataFrame):
                                    print("-" * 142)
                                    nome_arq = input("Nome do Arquivo (Por padrão 'resultados_simulacoes'): ") or "resultados_simulacoes.xlsx"
                                    if not nome_arq.endswith('.xlsx'):
                                        nome_arq += '.xlsx'
                                    nome_json = nome_arq.rsplit('.', 1)[0] + '.json'
                                    exportar_para_excel(aviso, nome_arquivo_excel=nome_arq)
                                    exportar_para_json(aviso, nome_arquivo_json=nome_json)
                                else:
                                    print("Erro: 'gerar_aviso' não retornou um DataFrame válido!")
                            else:
                                print("Erro: 'calcular_economias' não retornou um DataFrame válido!")
                        else:
                            print("Nenhum dado para ser exportado!")
                    
                    case _:
                        print("Opção inválida")
                
            case '0':
                print("Saindo... Até logo!")
                conn.close()  # Fecha a conexão ao sair
                break

            case _:
                print("Opção inválida.")



usuario_id = login()
if usuario_id:
    menu(usuario_id)
else:
    print("Encerrando programa.")