
from dotenv import load_dotenv
import os

load_dotenv()
frase = os.getenv("RESPOSTA_PRINT")

print(frase)