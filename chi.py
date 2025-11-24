import asyncio
import random
from datetime import datetime, timedelta
from mercapi import Mercapi
from mercapi.requests import SearchRequestData
from telegram import Bot
from telegram.constants import ParseMode
import yaml
from pathlib import Path
import os

URL = "https://jp.mercari.com/item/"
FOUND_LOG = "found.log"

def load_config(file_path: str | Path) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)

async def main():
    api = Mercapi()
    try:
        while True:
            config = load_config("config.yaml")
            BOT_TOKEN = config["BOT_TOKEN"]
            CHAT_ID = config["CHAT_ID"]
            ENTRIES = config.get("ENTRIES", 20)
            TIME = config.get("TIME", 30)
            TIME_RAND = config.get("TIME_RAND", 0)
            KEYWORD = config.get("KEYWORD", "blackish house")

            # Random interval
            interval_minutes = random.randint(max(1, TIME - TIME_RAND), TIME + TIME_RAND)
            next_run_time = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Next run at {next_run_time.strftime('%H:%M:%S')} ({interval_minutes} min from now)")

            bot = Bot(token=BOT_TOKEN)
            results = await api.search(
                KEYWORD,
                sort_by=SearchRequestData.SortBy.SORT_CREATED_TIME,
                sort_order=SearchRequestData.SortOrder.ORDER_DESC
            )

            # print(f'Found {results.meta.num_found} results')
            now = datetime.now()
            found = []
            for item in results.items[:ENTRIES]:
                
                if now - item.created < timedelta(minutes=interval_minutes):
                    found.append(item)
                    print(f'Name: {item.name}\nPrice: {item.price}\n')

            if found:
                if os.path.exists(FOUND_LOG):
                    with open(FOUND_LOG) as f:
                        exclude = [x.strip() for x in f.readlines()]
                        found = [ x for x in found if x.id_ not in exclude]
                        if not found:
                            print("Skipped all previously found items")
                            
                if found:
                    print(f'Found {len(found)} results')
                   
                        
                    await bot.send_message(chat_id=CHAT_ID, text=f"少吃一口会死! Found {len(found)} items")
                    with open(FOUND_LOG, "w") as f:
                        for i,item in enumerate(found):
                            photo_url = item.thumbnails[0]
                            caption = item.name
                            f.write(f"{item.id_}\n")
                            # await bot.send_photo(chat_id=CHAT_ID, photo=photo_url, caption=caption)
                            await bot.send_message(
                                chat_id=CHAT_ID,
                                text=f"[link {i+1}]({URL}{item.id_})",
                                parse_mode=ParseMode.MARKDOWN
                            )

            try:
                await asyncio.wait_for(asyncio.sleep(interval_minutes * 60), timeout=1e6)
            except asyncio.CancelledError:
                print("Sleep interrupted, exiting...")
                break

    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")

# --- Entry point for direct script execution ---
if __name__ == "__main__":
    asyncio.run(main())
