from utils.evidence_writer import save_text_file
from selenium_tools.evidence import save_screenshot
from selenium_tools.browser import get_driver
from extraction.qr_reader import extract_qr_text
from extraction.ocr_reader import extract_text_from_image
from collectors.image_downloader import download_image
from utils.file_manager import create_case_folder, save_metadata
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
from ai.ai_filter import analyze_scam
from collectors.reddit_collector import (
    fetch_reddit_rss_paginated,
    fetch_reddit_post_data,
    clean_reddit_text,
)


def run_pipeline(
    subreddits,
    posts_per_subreddit=25,
    max_pages=8,
    time_filter="latest",
    progress_callback=None,
):
    """
    Runs the complete fraud investigation pipeline.
    """

    def update_progress(stage, percent):
        if progress_callback:
            progress_callback(stage, percent)

    driver = get_driver()
    try:

        wb, ws, summary_ws = create_workbook()

        last_seen = load_last_seen()

        seen_links = set()

        results = []

        # 👇 Paste the subreddit loop here
        for subreddit in subreddits:

            update_progress(f"Scanning r/{subreddit}", 5)

            print(f"\nChecking r/{subreddit}")

            stop_at_fullname = last_seen.get(subreddit)

            entries = fetch_reddit_rss_paginated(
                subreddit,
                max_pages=max_pages,
                per_page_count=posts_per_subreddit,
                stop_at_fullname=stop_at_fullname,
            )

            print(f"Total NEW posts collected since last run: {len(entries)}")

            total_fetched = len(entries)
            passed_keyword = 0
            passed_ai = 0
            final_with_contact_info = 0

            newest_fullname_this_run = entries[0].get("id", "") if entries else None

            # Leave the "for post in entries:" loop exactly as it is for now.
            for post in entries:

                if post.link in seen_links:
                    continue
                seen_links.add(post.link)

                # ----------------------------
                # Get Reddit text
                # ----------------------------
                summary = BeautifulSoup(post.summary, "html.parser").get_text()
                summary = clean_reddit_text(summary)
                text = (post.title + " " + summary).lower()

                if not is_upi_related_keyword(text):
                    continue

                passed_keyword += 1

                # ----------------------------
                # Fetch full Reddit post
                # ----------------------------
                post_data = fetch_reddit_post_data(post.link)

                if post_data:
                    summary = post_data.get("selftext", "") or summary
                    text = (post.title + " " + summary).lower()

                # Start with Reddit text
                combined_text = post.title + "\n\n" + summary

                # ----------------------------
                # Create evidence folder
                # ----------------------------
                case_folder = create_case_folder(post.id)

                # ----------------------------
                # Download images and OCR
                # ----------------------------
                if "media_thumbnail" in post:

                    thumbnails = post.media_thumbnail

                    for index, image in enumerate(thumbnails, start=1):

                        image_url = image.get("url")

                        print(f"Downloading image {index}: {image_url}")

                        saved_image = download_image(image_url, case_folder, index)

                        if saved_image:

                            # OCR
                            ocr_text = extract_text_from_image(saved_image)

                            print("OCR TEXT")
                            print(ocr_text)
                            save_text_file(case_folder, "ocr.txt", ocr_text)

                            combined_text += "\n" + ocr_text

                            # QR Code
                            qr_text = extract_qr_text(saved_image)

                            if qr_text:
                                print("QR TEXT")
                                print(qr_text)
                                save_text_file(case_folder, "qr.txt", qr_text)

                                combined_text += "\n" + qr_text

                # ----------------------------
                # Extract entities
                # ----------------------------
                entities = extract_entities(combined_text)
                # ----------------------------
                # Decide whether to call AI
                # ----------------------------
                important_entities = entities["upi_ids"] or entities["phones"]

                if not important_entities:
                    print("No important entities found. Skipping AI.")
                    continue

                # ----------------------------
                # AI Analysis
                # ----------------------------
                ai_result = analyze_scam(combined_text)

                if not ai_result["is_scam"]:
                    print("AI classified as NOT a scam.")
                    continue

                passed_ai += 1

                confidence = ai_result["confidence"]
                scam_type = ai_result["scam_type"]
                ai_summary = ai_result["summary"]

                print("AI RESULT")
                print(ai_result)
                print("\nOpening Reddit post in Selenium...")
                driver.get(post.link)

                time.sleep(5)

                print("Page loaded successfully!")
                save_screenshot(driver, case_folder)
                # ----------------------------
                # Create Scam Record
                # ----------------------------
                record = ScamRecord(
                    subreddit=subreddit,
                    title=post.title,
                    summary=summary,
                    link=post.link,
                    phones=entities["phones"],
                    upi_ids=entities["upi_ids"],
                    emails=entities["emails"],
                    urls=entities["urls"],
                    confidence=confidence,
                    scam_type=scam_type,
                    ai_summary=ai_summary,
                )
                results.append(record)
                # ----------------------------
                # Save metadata
                # ----------------------------

                if record.phones or record.upi_ids:
                    final_with_contact_info += 1
                    save_metadata(case_folder, record)
                # ----------------------------
                # Console output
                # ----------------------------
                print("=" * 80)
                print("TITLE:", post.title)
                print("SUMMARY:", summary[:500])
                print("LINK:", post.link)
                print("URLs found:", record.urls)

                # ----------------------------
                # Excel output
                # ----------------------------
                write_post(ws, record)
                update_progress(f"Processed : {post.title[:40]}...", 50)

                time.sleep(3)
            if newest_fullname_this_run:
                last_seen[subreddit] = newest_fullname_this_run

        save_last_seen(last_seen)
        save_workbook(wb, "reddit_scam_report.xlsx")
        return results
    finally:
        driver.quit()
