from dotenv import load_dotenv
import os

load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')

if openai_key:
    print(f'Clé OpenAI: {openai_key[:15]}...{openai_key[-15:]}')
    print(f'Longueur: {len(openai_key)}')
    print(f'Commence par sk-: {openai_key.startswith("sk-")}')
    newline_count = openai_key.count('\n')
    print(f'Contient des retours à la ligne: {newline_count > 0} ({newline_count} trouvés)')
    print(f'Contient des espaces: {" " in openai_key}')
else:
    print('Aucune clé OpenAI trouvée')
