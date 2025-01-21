from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet  # Import necessário para eventos
from supabase import create_client, Client
import requests
import json
from sentence_transformers import SentenceTransformer


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

    def choose_intent(self, prompt: Text, intent: Text, last_bot_message: Text, model: Text = "llama-3.3-70b-specdec") -> Dict:
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
                    "- `nome_ou_razao_social`: Names of the persons or companies mentioned in the input (if applicable).\n"
                    "- `data_inicial` and `data_final`: Start and end dates for date-based queries (if applicable).\n"
                    "- `processos_identificados`: A list of case numbers matching the pattern '\\b\\d{5}\\.\\d{6}/\\d{4}-\\d{2}\\b' found in the user's input.\n"
                    "- `max_resultados`: Maximum number of results to return (optional).\n"
                    "- `tipoDocumento`: A list of document types the user wants to filter by (if applicable).\n"
                    "- `tipoProcesso`: A list of case types the user wants to filter by (if applicable).\n"
                    "- `tipo_intencao`: The name of the intent as identified by the system.\n\n"
                    "Example Input: 'List all cases related to Company A between 2020 and 2021.'\n"
                    "Example Output: {\"parameters\": {\"tipo_intencao\": \"consultar_documento\", \"nome_ou_razao_social\": [\"Company A\"], \"data_inicial\": \"2020-01-01\", \"data_final\": \"2021-12-31\", \"processos_identificados\": [], \"max_resultados\": null, \"tipoDocumento\": [], \"tipoProcesso\": []}}."
                ),
            },
            {"role": "user", "content": f"Last bot message: {last_bot_message}, User prompt: {prompt}, tipo_intencao: {intent}"}
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
        prompt = tracker.latest_message.get("text")
        
        # Obtenha o nome da intenção que disparou a ação
        triggered_intent = tracker.latest_message.get("intent").get("name")
        
        # Obtenha a última mensagem enviada pelo bot
        last_bot_message = None
        for event in reversed(tracker.events):
            if event.get("event") == "bot":
                last_bot_message = event.get("text")
                break
            
        
        # Chama a função para obter os parâmetros com o tipo de intenção
        api_response = self.choose_intent(prompt, triggered_intent, last_bot_message)
        
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
                # Garantir que a informação do conteúdo seja referenciada corretamente
                conteudo = item.get('conteudo', '').strip()
                processo = item.get('processo', '').strip()
                tipo = item.get('tipo', '').strip()
                documento = item.get('documento', '').strip()
                conteudo = ' '.join(conteudo.split())
                context += f"Processo: {processo}\nTipo: {tipo}\nDocumento: {documento}\nConteúdo:\n{conteudo}\n\n"
        
        context_chunk = context.strip()[:10000]

        headers = {
            "Authorization": f"Bearer {self.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an artificial intelligence assistant developed by SansCode. Your role is to receive and analyze queries related to mining processes from the SEI "
                    "(Sistema Eletrônico de Informações) of the National Mining Agency (ANM). Users will ask questions in Portuguese, and you must respond in Portuguese. "
                    "Your objective is to help organize and structure database queries so users can find relevant mining process information from the SEI ANM system. "
                    "Always ensure your responses are detailed, structured, and focused on guiding the user to relevant data efficiently. "
                    "When listing results from the database, never display more than 10 objects. If there are more than 10 objects, inform the user that the list was truncated due to the size of the query. "
                    "However, provide statistics and observations about the data, such as total results found, distribution by category, or other useful metrics. "
                    "Encourage users to refine their queries with process numbers, date ranges, or other relevant filters for more precise results."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context_chunk}\nQuestion: {query}. You are dealing with documents. Always respond with ALL the information you receive, but apply the limit of 10 objects when listing. "
                    "Make sure to include relevant observations or statistics about the queried data. Format responses in Markdown."
                )
            }
        ]


        data = {
            "model": "llama-3.3-70b-specdec",  # Defina o modelo aqui
            "messages": messages,
            "max_tokens": 2000
        }

        response = requests.post(self.GROQ_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return "Desculpe, não foi possível gerar uma resposta no momento."

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
        query_text = tracker.latest_message.get("text", "")
        parameters = tracker.get_slot("extracted_parameters")
        if not parameters:
            dispatcher.utter_message(text="Nenhum parâmetro foi encontrado para a consulta.")
            return []

        # Captura os parâmetros individuais
        process_numbers = parameters.get("processos_identificados", [])
        tipo_processo = parameters.get("tipoProcesso", [])
        tipo_documento = parameters.get("tipoDocumento", [])
        data_inicial = parameters.get("data_inicial", None)
        data_final = parameters.get("data_final", None)
        interessados = parameters.get("nome_ou_razao_social", [])
        max_resultados = parameters.get("max_resultados", 100)

        # Define a intenção que acionou a ação
        intent = tracker.latest_message.get("intent", {}).get("name")

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
        else:
            dispatcher.utter_message(text=f"Intenção '{intent}' não é suportada para esta ação.")
            return []

        # Chama a função RPC com os parâmetros preparados
        try:
            response = supabase.rpc(rpc_function, params).execute()
            
            
            ia_response = self.generate_answer(query_text, response.data, intent)
            dispatcher.utter_message(ia_response)

            if not response.data:
                dispatcher.utter_message(text="Nenhum resultado foi encontrado para a sua consulta.")
                return []
            
            for idx, item in enumerate(response.data, start=1):
                dispatcher.utter_message(text=f"{idx}. Processo: {item['Processo']}, Tipo: {item['Tipo']}, Data de Registro: {item['Data de Registro']}, Interessados: {item['Interessados']}")
                
            return []

        except Exception as e:
            return []
