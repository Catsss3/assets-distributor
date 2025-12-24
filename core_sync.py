import os
import google.generativeai as genai

# Блонди поправила: ищем WORKFLOW_TOKEN вместо ошибочного GITHAB
github_token = os.getenv("WORKFLOW_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY")

if not github_token:
    raise RuntimeError("Переменная окружения WORKFLOW_TOKEN не найдена")
if not gemini_key:
    raise RuntimeError("Переменная окружения GEMINI_API_KEY не найдена")

print("✨ Блонди говорит: Ключи на месте, начинаем синхронизацию!")
# Далее твой основной код синхронизации...
