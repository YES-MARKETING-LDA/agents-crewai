from firebase_functions import https_fn
from firebase_admin import initialize_app
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

import os

os.environ['OPENAI_API_KEY'] = ''
os.environ['SERPER_API_KEY'] = ''
os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o'

# Sua função interna
def generate_post(tema_do_artigo):
    search_tool = SerperDevTool()
    scrap_tool = ScrapeWebsiteTool()

    bucador = Agent(
        role = 'Buscador de Conteúdo',
        goal = 'Buscar online conteúdo sobre {tema}',
        backstory = 'Você está trabalhando na criação de artigos para o Linkedin sobre {tema}.'
                    'Você vai fazer uma busca sobre informações na internet, coletá-las e agrupá-las.'
                    'Seu trabalho servirá de base para o Redator de Conteúdo,',
        tools = [search_tool, scrap_tool],
        verbose = True
    )

    redator = Agent(
        role = 'Redator de Conteúdo',
        goal = 'Escrever um texto para Linkedin sobre {tema}',
        backstory = 'Você está trabalhando na redação de um artigo para o Linkedin sobre {tema}.'
                    'Você vai utilizar os dados coletados pelo Buscador de Conteúdo para escrever um texto'
                    'interessante, divertido e factualmente correto para o Linkedin'
                    'Dê opiniões sobre {tema}, mas ao fazê-lo, deixe claro que são opiniões pessoais',
        tools = [search_tool, scrap_tool],
        verbose = True
    )

    editor = Agent(
        role = 'Editor de Conteúdo',
        goal = 'Editar um texto de Linkedin para que ele tenha um tom mais informal',
        backstory = 'Você está trabalhando na edição de um artigo para o Linkedin.'
                    'Você vai receber um texto do Redator de Conteúdo e editá-lo para um tom de Walter Gandarella, que é mais informal.',
        tools = [search_tool, scrap_tool],
        verbose = True
    )

    buscar = Task(
        description = (
            "1. Priorize as últimas tendências, os principais atores e as notícias mais relevantes sobre {tema}.\n"
            "2. Identifique o público-alvo, considerando seus interesses e pontos de dor.\n"
            "3. Inclua palavras-chave de SEO e dados ou fontes relevantes"
        ),
        agent = bucador,
        expected_output = 'Um plano de tendência sobre {tema}, com as palavras mais relevantes de SEO e as últimas notícias.'
    )

    redigir = Task(
        description = (
            "1. Use os dados coletados para criar um post de Linkedin atraente sobre {tema}.\n"
            "2. Incorpore palavras-chave de SEO de forma natural.\n"
            "3. Certifique-se de que o post esteja estruturado de forma cativante, com uma conclusão que faça o leitor refletir."
        ),
        agent = redator,
        expected_output = 'Um texto de Linkedin sobre {tema}.'
    )

    editar = Task(
        description = ("Revisar a postagem do Linkedin quanto a erros gramaticais e alinhamento com o tom pessoal de Walter Gandarella."),
        agent = editor,
        expected_output = 'Um texto de Linkedin pronto para publicação, seguindo o tem esperado. O texto está separado em parágrafos e não usa bullet points.'
    )

    equipe = Crew(
        agents = [bucador, redator, editor],
        tasks = [buscar, redigir, editar],
        verbose = True
    )

    # tema_do_artigo = 'O que fazem a Crewai e a N8N, quais as diferenças entre os dois e como é que a minha empresa de marketing beneficiaria com a sua utilização?'
    entradas = { "tema": tema_do_artigo }
    resultado = equipe.kickoff(inputs = entradas)
    return resultado.raw

@https_fn.on_request(region="europe-west3", timeout_sec=540)
def generatePost(req):
    try:
        request_json = req.get_json()

        if not request_json or "topic" not in request_json:
            return {"success": False, "error": "JSON inválido. 'topic' é obrigatorios."}, 400

        topic = request_json["topic"]
        # tipo = request_json["type"]

        # Chama a função interna
        resultado = generate_post(topic)

        return {"success": True, "result": resultado}

    except Exception as e:
        return {"success": False, "error": str(e)}, 500
