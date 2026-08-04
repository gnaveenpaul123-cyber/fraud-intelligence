from utils.evidence_writer import save_text_file
from selenium_tools.evidence import save_screenshot
from selenium_tools.browser import get_driver
from extraction.qr_reader import extract_qr_text
from extraction.ocr_reader import extract_text_from_image
from collectors.image_downloader import download_image
from utils.file_manager import create_case_folder, save_metadata
import time
import calendar
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from exports.excel_reporter import (
    create_workbook,
    write_post,
    write_summary,
    save_workbook,
)
import math
import os
import shutil
import tempfile
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
from utils.logger import get_logger


logger = get_logger(__name__)


def filter_entries_by_time_range(entries, time_filter):
    """Apply the dashboard time-range selection to RSS entries when dates exist."""
    days_by_range = {
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "Last 90 Days": 90,
        "Last 1 Year": 365,
    }
    days = days_by_range.get(time_filter)
    if not days:
        return entries

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered_entries = []
    for entry in entries:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if not published:
            filtered_entries.append(entry)
            continue
        published_at = datetime.fromtimestamp(calendar.timegm(published), timezone.utc)
        if published_at >= cutoff:
            filtered_entries.append(entry)
    return filtered_entries


def get_post_date(post):
    """Return a display-ready UTC date from the RSS publication metadata."""
    published = post.get("published_parsed") or post.get("updated_parsed")
    if not published:
        return "Unavailable"
    try:
        return datetime.fromtimestamp(
            calendar.timegm(published), timezone.utc
        ).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OverflowError):
        return "Unavailable"



def run_pipeline(
    subreddits,
    posts_per_subreddit=25,
    max_pages=2,
    time_filter="latest",
    progress_callback=None,
):
    """
    Runs the complete fraud investigation pipeline.
    """

    total_requested = len(subreddits) * posts_per_subreddit
    metrics = {
        "posts_scanned": 0,
        "keyword_matches": 0,
        "keyword_filtered_out": 0,
        "contact_info_found": 0,
        "sent_to_ai": 0,
        "ai_confirmed": 0,
        "contact_information": 0,
        "screenshots_captured": 0,
        "errors": 0,
        "subreddit_stats": {
            subreddit: {
                "posts_scanned": 0,
                "important_info_found": 0,
                "ai_confirmed": 0,
            }
            for subreddit in subreddits
        },
    }
    started_at = time.monotonic()

    def update_progress(stage, percent, **details):
        if progress_callback:
            payload = {"stage": stage, **metrics, **details}
            try:
                progress_callback(stage, percent, payload)
            except TypeError:
                # Existing integrations using the original two-argument callback continue to work.
                progress_callback(stage, percent)
    logger.info("Pipeline started for %s subreddit(s)", len(subreddits))
    if posts_per_subreddit <=25:
        per_page_count = posts_per_subreddit
        max_pages = 1
    else:
        per_page_count = 25
        max_pages = math.ceil(posts_per_subreddit / 25)

    # Start Chrome only after a UPI scam is confirmed.  Browser startup is costly
    # and most scanned posts are rejected by the keyword/entity/AI filters.
    driver = None
    try:

        wb, ws, summary_ws = create_workbook()

        last_seen = load_last_seen()

        seen_links = set()

        results = []

        for subreddit_index, subreddit in enumerate(subreddits, start=1):
            subreddit_metrics = metrics["subreddit_stats"][subreddit]

            update_progress(
                "RSS Collection", 5,
                subreddit=subreddit,
                current_subreddit=subreddit_index,
                total_subreddits=len(subreddits),
                message=f"Collecting posts from r/{subreddit}",
            )

            logger.info("Checking r/%s", subreddit)

            stop_at_fullname = last_seen.get(subreddit)

            try:
                entries = fetch_reddit_rss_paginated(
                    subreddit,
                    max_pages=max_pages,
                    per_page_count=per_page_count,
                    stop_at_fullname=stop_at_fullname,
                )
            except Exception:
                metrics["errors"] += 1
                logger.exception("Reddit collection failed for r/%s; continuing.", subreddit)
                continue

            entries = filter_entries_by_time_range(entries, time_filter)

            print(f"Total NEW posts collected since last run: {len(entries)}")

            total_fetched = len(entries)
            passed_keyword = 0
            sent_to_ai = 0
            passed_ai = 0
            final_with_contact_info = 0

            newest_fullname_this_run = entries[0].get("id", "") if entries else None

            for post_index, post in enumerate(entries, start=1):

                if post.link in seen_links:
                    continue
                seen_links.add(post.link)
                metrics["posts_scanned"] += 1
                subreddit_metrics["posts_scanned"] += 1
                progress_percent = min(
                    90,
                    10 + int(80 * metrics["posts_scanned"] / max(total_requested, 1)),
                )
                update_progress(
                    "RSS Collection", progress_percent,
                    subreddit=subreddit,
                    current_post=post_index,
                    total_posts=total_fetched,
                    message=f"Scanning post {post_index} of {total_fetched}",
                )

                try:
                    summary = BeautifulSoup(post.summary, "html.parser").get_text()
                    summary = clean_reddit_text(summary)
                    text = (post.title + " " + summary).lower()

                    if not is_upi_related_keyword(text):
                        metrics["keyword_filtered_out"] += 1
                        update_progress(
                            "Keyword Filter", progress_percent, subreddit=subreddit,
                            current_post=post_index, total_posts=total_fetched,
                            message="Skipping post with no UPI scam indicators",
                        )
                        continue

                    passed_keyword += 1
                    metrics["keyword_matches"] += 1

                
                # Fetch full Reddit post
                
                    post_data = fetch_reddit_post_data(post.link)

                    if post_data:
                        summary = post_data.get("selftext", "") or summary
                        text = (post.title + " " + summary).lower()

                # Start with Reddit text
                    combined_text = post.title + "\n\n" + summary

                    # Files are staged outside evidence/ until the case has all
                    # required proof: identifier, AI confirmation, and screenshot.
                    with tempfile.TemporaryDirectory(prefix="fraud-intel-") as work_folder:
                        if "media_thumbnail" in post:
                            for index, image in enumerate(post.media_thumbnail, start=1):
                                image_url = image.get("url")
                                update_progress("Image Download", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message=f"Downloading image {index}")
                                try:
                                    saved_image = download_image(image_url, work_folder, index)
                                except Exception:
                                    metrics["errors"] += 1
                                    logger.exception("Image download failed for %s", post.link)
                                    continue
                                if not saved_image:
                                    continue

                                update_progress("OCR Extraction", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message=f"Extracting text from image {index}")
                                try:
                                    ocr_text = extract_text_from_image(saved_image)
                                except Exception:
                                    metrics["errors"] += 1
                                    logger.exception("OCR failed for %s; continuing without OCR text.", saved_image)
                                    ocr_text = ""
                                save_text_file(work_folder, "ocr.txt", ocr_text)
                                combined_text += "\n" + ocr_text

                                try:
                                    qr_text = extract_qr_text(saved_image)
                                except Exception:
                                    metrics["errors"] += 1
                                    logger.exception("QR extraction failed for %s; continuing.", saved_image)
                                    qr_text = ""
                                if qr_text:
                                    save_text_file(work_folder, "qr.txt", qr_text)
                                    combined_text += "\n" + qr_text

                        update_progress("Entity Extraction", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message="Extracting contact information")
                        entities = extract_entities(combined_text)
                        if not entities["upi_ids"]:
                            logger.info("No UPI ID found; skipping %s", post.link)
                            update_progress(
                                "Entity Extraction", progress_percent, subreddit=subreddit,
                                current_post=post_index, total_posts=total_fetched,
                                message="Skipping post with no extractable UPI ID",
                            )
                            continue

                        subreddit_metrics["important_info_found"] += 1
                        sent_to_ai += 1
                        metrics["contact_info_found"] += 1
                        metrics["sent_to_ai"] += 1
                        update_progress("AI Analysis", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message="Classifying potential scam")
                        ai_result = analyze_scam(combined_text)
                        if not ai_result.get("is_scam"):
                            logger.info("AI classified post as not a scam: %s", post.link)
                            continue
                        # Keep the report schema unchanged while guaranteeing that
                        # every saved case has the single supported scam category.
                        ai_result["scam_type"] = "UPI Payment Scam"
                        passed_ai += 1
                        metrics["ai_confirmed"] += 1
                        subreddit_metrics["ai_confirmed"] += 1

                        if not driver:
                            try:
                                update_progress("Screenshot Capture", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message="Starting browser for confirmed UPI scam")
                                driver = get_driver()
                            except Exception:
                                metrics["errors"] += 1
                                logger.exception("Selenium browser could not be started; refusing to save unscreened case: %s", post.link)
                                continue

                        case_folder = None
                        case_folder_existed = False
                        try:
                            update_progress("Screenshot Capture", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message="Capturing browser evidence")
                            driver.get(post.link)
                            # Wait only until Reddit has rendered instead of always
                            # pausing five seconds for every confirmed case.
                            WebDriverWait(driver, 10).until(
                                lambda browser: browser.execute_script("return document.readyState") == "complete"
                            )
                            save_screenshot(driver, work_folder)
                            case_folder = os.path.join("evidence", "reddit", post.id)
                            case_folder_existed = os.path.exists(case_folder)
                            case_folder = create_case_folder(post.id)
                            shutil.copytree(work_folder, case_folder, dirs_exist_ok=True)
                            metrics["screenshots_captured"] += 1
                        except Exception:
                            if case_folder and not case_folder_existed:
                                shutil.rmtree(case_folder, ignore_errors=True)
                            metrics["errors"] += 1
                            logger.exception("Screenshot failed for %s; case was not saved.", post.link)
                            continue

                        record = ScamRecord(
                            subreddit=subreddit,
                            post_date=get_post_date(post),
                            title=post.title,
                            summary=summary,
                            link=post.link,
                            phones=entities["phones"],
                            upi_ids=entities["upi_ids"],
                            account_numbers=entities["account_numbers"],
                            emails=entities["emails"],
                            wallet_addresses=entities["wallet_addresses"],
                            contact_handles=entities["contact_handles"],
                            urls=entities["urls"],
                            confidence=ai_result.get("confidence", 0),
                            scam_type=ai_result.get("scam_type", "Unknown"),
                            ai_summary=ai_result.get("summary", ""),
                        )
                        final_with_contact_info += 1
                        metrics["contact_information"] += 1
                        try:
                            save_metadata(case_folder, record)
                        except Exception:
                            metrics["errors"] += 1
                            logger.exception("Metadata save failed for %s", post.link)
                            continue

                        results.append(record)
                        logger.info("Confirmed, screenshot-backed scam case: %s", post.link)
                        write_post(ws, record)
                        update_progress("Saving", progress_percent, subreddit=subreddit, current_post=post_index, total_posts=total_fetched, message="Saving investigation evidence")
                except Exception:
                    metrics["errors"] += 1
                    logger.exception("Post processing failed for %s; continuing.", post.get("link", "unknown"))
                    continue
            write_summary(
                summary_ws, subreddit, total_fetched, passed_keyword, sent_to_ai,
                passed_ai, final_with_contact_info,
            )
            if newest_fullname_this_run:
                last_seen[subreddit] = newest_fullname_this_run

        save_last_seen(last_seen)
        update_progress("Excel Report", 95, message="Generating Excel report")
        save_workbook(wb, "reddit_scam_report.xlsx")
        metrics["duration_seconds"] = round(time.monotonic() - started_at, 1)
        update_progress("Complete", 100, message="Investigation complete", completed=True)
        logger.info("Pipeline completed in %ss", metrics["duration_seconds"])
        return results
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                logger.exception("Selenium browser could not be closed cleanly.")
