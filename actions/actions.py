from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet  # Import necessário para eventos
from supabase import create_client, Client
import requests
import json
from sentence_transformers import SentenceTransformer
import re

# Configurações do Supabase
SUPABASE_URL = "https://oixmmanzunrtyymwhqny.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9peG1tYW56dW5ydHl5bXdocW55Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU5NzY2MjksImV4cCI6MjA0MTU1MjYyOX0.XU5foyzWGynnisYtoSbe_IlVrD50OmWHp5GiWDd5d1g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Modelo de embeddings
embeddings = SentenceTransformer("paraphrase-mpnet-base-v2")

class SetEntityFromPrompt(Action):
    GROQ_API_KEY = "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"
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def name(self) -> Text:
        return "action_set_entity_from_prompt"

    def choose_intent(self, prompt: Text, intent: Text, last_bot_message: Text, model: Text = "llama-3.3-70b-versatile") -> Dict:
        
        headers = {
            "Authorization": f"Bearer {self.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI designed to interpret legal queries provided in Portuguese and return a structured JSON object "
                    "representing only the extracted parameters from the user's input. You must respond exclusively with the JSON, without explanations, messages, or any additional content. "
                    "Your purpose is to extract essential parameters for querying a legal case database.\n\n"
                    "You must identify and extract the following parameters:\n"
                    "YOU SHOULD NEVER CREATE A NEW PARAMETER, JUST EXTRACT FROM THE PROMPT OR THE CONTEXT PROVIDED BY THE USER, NEVER INVENT MORE PARAMETERS"
                    "If the intent is not defined in the user prompt, set an intent as per the user's request"
                    "1. `filtrar_processos`: To request a list of cases based on specified parameters, such as date range or related parties.\n"
                    "   Example: 'Liste todos os processos que ocorreram em 2020-2021 envolvendo a Fire Metals LTDA e Pessoa 2.'\n"
                    "2. `filtrar_documentos`: To request documents related to specific cases.\n"
                    "   Example: 'Me traga os documentos envolvendo o processo 48408.880078/2017-01 e 48408.880100/2018-95.'\n"
                    "3. `consultar_documento_especifico`: To request documents related to specific cases.\n"
                    "   Example: 'Detalhe o documento número 3066009'\n"                    
                    "- `nome_ou_razao_social`: Names of the persons or companies mentioned in the input (if applicable).\n"
                    "- `data_inicial` and `data_final`: Start and end dates for date-based queries (if applicable).\n"
                    "- `processos_identificados`: A list of case numbers matching the pattern '\\b\\d{5}\\.\\d{6}/\\d{4}-\\d{2}\\b' found in the user's input.\n"
                    "- `max_resultados`: Maximum number of results to return (optional).\n"
                    "- `tipoDocumento`: A list of document types the user wants to filter by (if applicable).\n"
                    "- `tipoProcesso`: A list of case types the user wants to filter by (if applicable).\n"
                    "- `tipo_intencao`: The name of the intent as identified by the system.\n\n"
                    "- `documentos_indentificados`: A list containing document identification numbers Exemple: 1630682"
                    "Additionally, if the context provided in the previous AI message contains relevant information, you must also extract parameters based on that context.\n\n"
                    "Example Input: 'List all cases related to Company A between 2020 and 2021.'\n"
                    "Example Output: {\"parameters\": {\"tipo_intencao\": \"consultar_documento\", \"nome_ou_razao_social\": [\"Company A\"], \"data_inicial\": \"2020-01-01\", \"data_final\": \"2021-12-31\", \"processos_identificados\": [], \"documentos_identificados\": [], \"max_resultados\": null, \"tipoDocumento\": [], \"tipoProcesso\": []}}."
                    f"Intencao: {intent}"
                ),
            },
            {
                "role": "user",
                "content": f"Context: {last_bot_message}, User prompt: {prompt}, Intencao: {intent}"
            }
        ]


        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 2000
        }

        response = requests.post(self.GROQ_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            try:
                raw_content = response.json()["choices"][0]["message"]["content"].strip()
                intent_response = json.loads(raw_content)
                print(intent_response)
                return intent_response
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Erro ao processar a resposta: {e}")
                return None
        else:
            print(f"Erro na requisição: {response.status_code} - {response.text}")
            return None

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        # Obtenha o prompt (última mensagem do usuário)
        
        # Obtenha o nome da intenção que disparou a ação
        triggered_intent = tracker.get_slot("actual_intent")

        """ prompt = tracker.latest_message.get("text") """
        prompt = tracker.get_slot("user_prompt")
        
        last_bot_response = tracker.get_slot("last_bot_response")
        
        actual_intent = tracker.get_slot("actual_intent")

        result_max = tracker.get_slot("result_max")

        try:
            result_max = int(result_max) if result_max is not None else None
        except ValueError:
            result_max = None  # Caso não consiga converter, define como None

        if result_max is not None and result_max >= 0:
            prompt += f". Retorne no máximo: {result_max} objetos"
        
        """ return print(f"Intencao atual: {actual_intent} Prompt atual: {prompt}") """
        
        # Chama a função para obter os parâmetros com o tipo de intenção
        api_response = self.choose_intent(prompt, actual_intent, last_bot_response)
        
        
        if api_response:
            # Inclui o tipo da intenção identificado pelo Rasa no JSON final
            parameters = api_response.get("parameters", {})
            parameters["tipo_intencao"] = triggered_intent

            # Preenche o slot com o JSON
            slot_events = [SlotSet("extracted_parameters", parameters)]
            return slot_events
        else:
            dispatcher.utter_message(text="Erro ao processar o prompt. Tente novamente.")
            return []



class ActionSearchSupabase(Action):
    GROQ_API_KEY = "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"
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    def set_last_bot_message(response):
        slot_events = [SlotSet("last_bot_response", response)]
        return slot_events        
    
    def generate_answer(self, query, response_data, intent):
        
        context = ""
        if intent == "consultar_processos" or intent == "pesquisar_procesos_interessados":
            if response_data[0]['stats'].get('total', 0) > 20:
                context += f"Nem todos os resultos podem ser printados,a ao total retornal : {response_data[0]['stats'].get('total', 0)} do banco de dados"
            
            for item in response_data:
                context += f"Processo: {item.get('processo', '').strip()}\nTipo: {item.get('tipo', '').strip()}\nData de Registro: {item.get('Data de Registro', '').strip()}\nInteressados: {item.get('interessados', '').strip()}\n\n"
            
            context_chunk = context.strip()[:10000] 
            print("Pesquisa por processos")
        
        elif intent == "consultar_documento" or intent == "pesquisa_processos_vetorial" or intent == "pesquisar_documentos_interessados":
            print("Pesquisa por documentos")
            for item in response_data:
                processo = item.get('processo', '').strip()
                conteudo = item.get('conteudo', '').strip()
                tipo = item.get('tipo', '').strip()
                documento = item.get('documento', '').strip()
                
                # Removendo os espaços extras e limpando o conteúdo
                conteudo = ' '.join(conteudo.split())
                
                context += f"Documento número: {documento}\nProcesso: {processo}\nTipo: {tipo}\Descrição: {conteudo}...\n"

        elif intent == "consultar_documento_especifico":
            print("Pesquisa por documento específico")
            context = ""

            for item in response_data:
                # Garantir que a informação do conteúdo seja referenciada corretamente
                conteudo = item.get('conteudo', '').strip()
                processo = item.get('processo', '').strip()
                tipo = item.get('tipo', '').strip()
                documento = item.get('documento_id', '').strip()  # Aqui ajustei para usar o 'documento_id'
                
                # Compactar o conteúdo para evitar quebras ou espaços desnecessários
                conteudo = ' '.join(conteudo.split())
                
                # Construindo a resposta formatada
                context += (
                    f"Processo: {processo}\n"
                    f"Tipo: {tipo}\n"
                    f"Documento ID: {documento}\n"
                    f"Conteúdo:\n{conteudo}\n\n"
                )
                
        context_chunk = context.strip()[:10000]

        if not context_chunk:
            dispatcher.utter_message(text="Não encontrei dados para responder a sua pergunta, tente novamente.")
            return

        """ return print(context_chunk) """

        """ return print(f"Chunk: {context_chunk} e {intent} ") """
        headers = {
            "Authorization": f"Bearer {self.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = [
            {
                "role": "system",
                "content": ("You are an AI assistant specializing in queries related to mining processes from the SEI (Sistema Eletrônico de Informações) of the National Mining Agency (ANM)." " Your primary goal is to assist users in accessing, organizing, and structuring relevant information about mining processes." " Users will ask questions in Portuguese, and you must always respond clearly, in detail, and in Portuguese." "/n" "Ensure that your responses are tailored to the user's query context and the type of data provided, making them meaningful and structured." " Focus on delivering a summary or analysis that adds value to the search rather than listing raw data." "/n" "If the search returns more than 10 objects, indicate the total number of results found and suggest refining the query using filters such as process numbers, dates, or interested parties for greater precision." "/n" "Highlight key observations, such as patterns identified in the data (e.g., distribution by category, dates, or frequency of occurrences)." " Use MarkDown format to enhance organization and readability, employing lists, tables, and line breaks for a structured and accessible presentation." " However, avoid using heading sizes like # or ##." 
                            "Whenever you list something, list it numbered and organized in a legible and professional way."
                            "When generating statistics, always send a table code in pure HTML formatted in a table without line breaks ex: <table><thead><tr><th>Coluna 1</th><th>Coluna 2</th><th>Coluna 3</th></tr></thead><tbody><tr><td>Valor 1</td><td>Valor 2</td><td>Valor 3</td></tr><tr><td>Valor A</td><td>Valor B</td><td>Valor C</td></tr></tbody></table>"

                )
            },  
            {
                "role": "user",
                "content": (
                    f"Context:\n{context_chunk}\nQuestion: {query}.s"
                )
            }
        ]



        data = {
            "model": "llama-3.3-70b-versatile",  # Defina o modelo aqui
            "messages": messages,
            "max_tokens": 2000
        }

        response = requests.post(self.GROQ_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            formatted_response = response.json()['choices'][0]['message']['content']
            return formatted_response.replace("\n", "/n")
        else:
            return f"Desculpe, não foi possível gerar uma resposta no momento. {response}"

    def name(self) -> Text:
        return "action_search_supabase"

    def format_date(self, date_str: Optional[str]) -> Optional[str]:
        """Formata uma string de data para o formato esperado pelo Supabase."""
        if not date_str:
            return None
        try:
            from datetime import datetime
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        # Captura os parâmetros dos slots
        """ query_text = tracker.latest_message.get("text", "") """
        query_text = tracker.get_slot("user_prompt")
        
        parameters = tracker.get_slot("extracted_parameters")
        if not parameters:
            dispatcher.utter_message(text="Nenhum parâmetro foi encontrado para a consulta.")
            return []

        # Captura os parâmetros individuais
        process_numbers = parameters.get("processos_identificados", [])
        tipo_processo = parameters.get("tipoProcesso", [])
        tipo_documento = parameters.get("tipoDocumento", [])
        documentos_identificados = parameters.get("documentos_identificados", [])
        data_inicial = parameters.get("data_inicial", None)
        data_final = parameters.get("data_final", None)
        interessados = parameters.get("nome_ou_razao_social", [])
        max_resultados = parameters.get("max_resultados", 100)

        # Define a intenção que acionou a ação
        intent = parameters.get("tipo_intencao", None)
        """ intent = tracker.latest_message.get("intent", {}).get("name") """

        # Mapeia a função RPC com base na intenção
        rpc_function = None
        if intent == "consultar_processos" or intent == "pesquisar_procesos_interessados":
            rpc_function = "pesquisa_processos"
            params = {
                "data_inicial": data_inicial,
                "data_final": data_final,
                "max_resultados": max_resultados,
                "interessados_param": interessados if interessados else None,
                "processos_identificados": process_numbers if process_numbers else None,
                "tipo_documento": tipo_documento if tipo_documento else None,
                "tipo_processo": tipo_processo if tipo_processo else None,
            }
        
        elif intent == "consultar_documento" or intent == "pesquisa_processos_vetorial" or intent == "pesquisar_documentos_interessados":
            rpc_function = "pesquisa_processos_vetorial"
            query_embedding = embeddings.encode([query_text])[0]
            params = {
                "data_inicial": data_inicial if data_inicial else None,
                "data_final": data_final if data_final else None,
                "max_resultados": max_resultados if max_resultados else 10,  # Valor padrão
                "interessados_param": interessados if interessados else None,  # Lista vazia
                "processos_identificados": process_numbers if process_numbers else None,  # Lista vazia
                "tipo_documento": tipo_documento if tipo_documento else None,  # Lista vazia
                "tipo_processo": tipo_processo if tipo_processo else None,  # Lista vazia
            }
        elif intent == "consultar_documento_especifico":
            rpc_function = "pesquisa_documentos"
            params = {
                "data_inicial": data_inicial if data_inicial else None,
                "data_final": data_final if data_final else None,
                "max_resultados": max_resultados if max_resultados else 10,  # Valor padrão
                "interessados_param": interessados if interessados else None,  # Lista vazia
                "documentos_identificados": documentos_identificados if documentos_identificados else None,  # Lista vazia
                "tipo_documento": tipo_documento if tipo_documento else None,  # Lista vazia
                "tipo_processo": tipo_processo if tipo_processo else None,  # Lista vazia
            }
        else:
            print(f"Intencao: {intent} nao suportada")
            dispatcher.utter_message(text=f"Intenção '{intent}' não é suportada para esta ação.")
            return []

        # Chama a função RPC com os parâmetros preparados
        try:
            response = supabase.rpc(rpc_function, params).execute()
            
            """ return print(response.data) """
            
            ia_response = self.generate_answer(query_text, response.data, intent)
            
            dispatcher.utter_message(ia_response)
                        
            return [SlotSet("last_bot_response", ia_response)]

            if not response.data:
                dispatcher.utter_message(text="Nenhum resultado foi encontrado para a sua consulta.")
                return []
            
            for idx, item in enumerate(response.data, start=1):
                dispatcher.utter_message(text=f"{idx}. Processo: {item['Processo']}, Tipo: {item['Tipo']}, Data de Registro: {item['Data de Registro']}, Interessados: {item['Interessados']}")
                
            return []

        except Exception as e:
            return []

class ActionSearchInterestedSupabase(Action):
    def name(self) -> Text:
        return "action_search_interested_supabase"

    def extract_names(self, query: str) -> List[str]:
        """
        Extrai nomes ou razões sociais da query do usuário.
        Captura:
        - Palavras que começam com maiúsculas
        - Nomes compostos com conectores (de, da, dos, etc)
        - Razões sociais com designações empresariais (S.A., LTDA, etc)
        - Caracteres acentuados
        - Números e símbolos comuns em razões sociais
        """
        # Padrões de conectores e designações empresariais comuns
        conectores = r'(?:e|de|da|do|das|dos|\')?'
        designacoes = r'(?:\s+(?:S\.?A\.?|LTDA\.?|MEI|EIRELI|EPP|ME|& CIA\.?|COMP\.?))?'
        
        # Padrão principal para captura de nomes/razões sociais
        padrao = fr'''
            # Início do grupo de captura
            (
                # Primeira palavra começando com maiúscula
                (?:[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)
                # Possíveis palavras adicionais
                (?:
                    # Espaço ou hífen seguido de conector opcional
                    (?:[\s-]+{conectores}\s*)?
                    # Palavra adicional (maiúscula ou minúscula após conector)
                    (?:[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)
                )*
                # Designação empresarial opcional
                {designacoes}
            )
        '''
        
        # Encontra todas as correspondências usando o padrão
        matches = re.finditer(padrao, query, re.VERBOSE)
        names = [match.group(1).strip() for match in matches]
        
        # Se nenhum nome foi encontrado, tenta um padrão mais simples para nomes curtos
        if not names:
            simple_matches = re.findall(r'\b[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+\b', query)
            names.extend(simple_matches)
        
        return names

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Captura a query do usuário
        user_query = tracker.latest_message.get("text", "")
        if not user_query:
            dispatcher.utter_message(text="Não consegui entender sua consulta.")
            return []

        # Extrai nomes da query
        nomes = self.extract_names(user_query)
        if not nomes:
            dispatcher.utter_message(text="Não consegui entender a sua pergunta.")
            return []

        # Chama a função Supabase com os nomes extraídos
        try:
            print(f"Nomes extraídos: {nomes}")  # Debug
            response = supabase.rpc("pesquisar_razao_social", {"nomes_razao_social": nomes}).execute()
    
            if response.data:
                # Formata os resultados para exibição numerando
                result = "\n".join([f"{i+1}. {item}" for i, item in enumerate(response.data)])
                dispatcher.utter_message(
                    text=f"Encontrei os seguintes interessados:/n{result}/nQuais desses interessados você gostaria de saber mais informações?"
                )
            else:
                dispatcher.utter_message(
                    text="Nenhum resultado foi encontrado no banco de dados para os nomes fornecidos. Tente novamente"
                )
            
            """ return [SlotSet("interessados", response.data or None)] """

            return [SlotSet("last_bot_response", f"User last prompt: {user_query}, Response: Encontrei os seguintes interessados:\n{response.data},\nQuais desses interessados você gostaria de saber mais informações?" or "Nenhum resultado encontrado.")]

        except Exception as e:
            dispatcher.utter_message(text=f"Erro ao consultar a base de dados: {str(e)}")
            return []

class ActionSetActualIntent(Action):
    def name(self) -> Text:
        return "action_set_actual_intent"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Obtém o nome da intenção atual
        triggered_intent = tracker.latest_message.get("intent").get("name")
        
        # Retorna um evento SlotSet para salvar o valor no slot actual_intent
        return [SlotSet("actual_intent", triggered_intent)]
    
class ActionSetActualUserPrompt(Action):
    def name(self) -> Text:
        return "action_set_actual_userprompt"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Obtem o ultimo prompt do usuario, disparado em stories onde a pergunta do usuário é importante para pesquisa
        prompt = tracker.latest_message.get("text")

        # Retorna um evento SlotSet para salvar o valor no slot actual_intent
        return [SlotSet("user_prompt", prompt)]

