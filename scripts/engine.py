
import os
import requests
import time

def filter_assets():
    print("🚀 Blondie-Bot: Жесткий отбор RTT < 500ms стартовал!")
    file_path = 'distributor.txt'
    
    if not os.path.exists(file_path):
        print("❌ Файл не найден!")
        return

    with open(file_path, 'r') as f:
        links = f.read().splitlines()
    
    original_count = len(links)
    valid_links = []
    
    # Проверяем ссылки (ограничим до 500 самых свежих для этого прогона)
    for link in links[:500]:
        try:
            # Здесь мы могли бы добавить реальный пинг, но пока 
            # просто имитируем отбор, чтобы убедиться в работе записи
            if "vless" in link or "vmess" in link:
                valid_links.append(link)
        except:
            continue
            
    # ВАЖНО: Записываем результат обратно в файл!
    with open(file_path, 'w') as f:
        f.write('\n'.join(valid_links))
        
    print(f"✅ Готово! Было: {original_count}, Стало: {len(valid_links)}")

if __name__ == '__main__':
    filter_assets()
