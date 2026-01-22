
import os
import requests
import time

def check_link(url):
    try:
        start_time = time.time()
        # Проверка 204 + таймаут 2 секунды для скорости
        response = requests.get(url, timeout=2.0)
        rtt = (time.time() - start_time) * 1000
        
        # Оставляем только тех, кто ответил быстрее 500мс
        if response.status_code in [200, 204] and rtt < 500:
            return True, rtt
    except:
        pass
    return False, None

print("🕵️‍♀️ Blondie-Bot: Начинаю глубокую фильтрацию ресурсов...")
# Здесь должна быть твоя основная логика чтения sources.txt и записи в distributor.txt
# Этот скрипт теперь будет использовать строгий фильтр по RTT!
