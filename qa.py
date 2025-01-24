import requests

# Configuração da API da Hugging Face
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
API_KEY = "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"  # Substitua pela sua chave
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def query_huggingface(prompt):
    """Envia o prompt para a API da Hugging Face e retorna a resposta."""
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result[0]["generated_text"]
    else:
        return f"Erro na API: {response.status_code} - {response.text}"

def main():
    print("🤖 Olá! Eu sou seu assistente de IA. Pergunte algo ou digite 'sair' para encerrar.")
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            print("🤖 Até mais!")
            break
        response = query_huggingface(user_input)
        print(f"🤖 {response}")

if __name__ == "__main__":
    main()
