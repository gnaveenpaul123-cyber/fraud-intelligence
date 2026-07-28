from collectors.image_downloader import download_image
from utils.file_manager import (create_case_folder, save_metadata)
import time
from bs4 import BeautifulSoup
from exports.excel_reporter import (
    create_workbook,
    write_post,
    write_summary,
    save_workbook,
)
from utils.storage import load_last_seen, save_last_seen

from config.keywords import is_upi_related_keyword
from extraction.entity_extractor import extract_entities
from models.scam_record import ScamRecord

from collectors.reddit_collector import (
    fetch_reddit_rss_paginated,
    fetch_reddit_post_data,
    clean_reddit_text
)

from ai.ai_filter import is_upi_scam_ai

# Subreddits to monitor (r/fraud removed — subreddit no longer exists, returns 404)
subreddits = [
    "IsThisAScamIndia"
]





wb, ws, summary_ws = create_workbook()

last_seen = load_last_seen()

seen_links = set()


for subreddit in subreddits:
    print(f"\nChecking r/{subreddit}")

    stop_at_fullname = last_seen.get(subreddit) 
    entries = fetch_reddit_rss_paginated(
        subreddit, max_pages=1, per_page_count=25, stop_at_fullname=stop_at_fullname
    )
    print(f"Total NEW posts collected since last run: {len(entries)}")

    
    total_fetched = len(entries)
    passed_keyword = 0
    passed_ai = 0
    final_with_contact_info = 0

    
    newest_fullname_this_run = entries[0].get("id", "") if entries else None

    for post in entries:
        if post.link in seen_links:
            continue
        seen_links.add(post.link)
        

        summary = BeautifulSoup(post.summary, "html.parser").get_text()
        summary = clean_reddit_text(summary)
        text = (post.title + " " + summary).lower()
            
        if not is_upi_related_keyword(text):
            continue
        passed_keyword += 1

       
        # Post passed Stage 1 — fetch the full Reddit post data
        post_data = fetch_reddit_post_data(post.link)

        if post_data:
            #print(post_data.keys())   # Temporary debugging
            summary = post_data.get("selftext", "") or summary
            text = (post.title + " " + summary).lower()
        entities = extract_entities(text)
        record = ScamRecord(
                subreddit=subreddit,
                title=post.title,
                summary=summary,
                 link=post.link,
                phones=entities["phones"],
                upi_ids=entities["upi_ids"],
                emails=entities["emails"],
                urls=entities["urls"]
            )
        #time.sleep(2)  

        # Stage 2: AI verification ---
        #if not is_upi_scam_ai(post.title, summary):
         #   print(f"Skipped (AI ruled not a UPI scam): {post.title}")
          #  continue
        passed_ai += 1
        
        case_folder = create_case_folder(post.id)
        save_metadata(case_folder, record)
        if "media_thumbnail" in post:
            thumbnails = post.media_thumbnail
            for index, image in enumerate(thumbnails, start=1):
                image_url = image.get("url")
                print(f"Downloading image {index}:{image_url}")
                download_image(image_url, case_folder,index)
                #print("Evidence folder:",case_folder)


        if record.phones or record.upi_ids:
            final_with_contact_info += 1

        print("=" * 80)
        print("TITLE:", post.title)
        print("SUMMARY:", summary[:500])
        print("LINK:", post.link)
        print("URLs found:", record.urls)
        # appending the info into workbook
        write_post(ws, record)

        time.sleep(3)  # pause between AI calls to stay under rate limits

    # addidng the numbers to worksheet
    write_summary(
    summary_ws,
    subreddit,
    total_fetched,
    passed_keyword,
    passed_ai,
    final_with_contact_info,
)

    
    if newest_fullname_this_run:
        last_seen[subreddit] = newest_fullname_this_run
   
    time.sleep(30)  


save_last_seen(last_seen)

save_workbook(wb, "reddit_upi_scams.xlsx")
print("\n✅ reddit_upi_scams.xlsx created successfully (with Summary sheet)!")
