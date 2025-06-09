import pandas as pd
from utils import Utils
from logger import setup_logger
from requester import Requester
from parser import Parser
import os
import json
import facebook_urls
import time

logger = setup_logger(__name__)

class FacebookScraper():
    def crawl_post(self, page_url: str, docid: str, save_dir="data\\image", num_iterations=3, comment_api_path="./api_info/comment_api.json", return_posts=False):
        try:
            logger.info(f"Thực hiện lấy post và comment từng post:")
            headers = Requester._get_headers(page_url)
            homepage_response = Requester._get_homepage(page_url, headers)
            entryPoint = Requester._parse_entryPoint(homepage_response)
            identifier = Requester._parse_identifier(entryPoint, homepage_response)
            cursor = "Cg8Ob3JnYW5pY19jdXJzb3IJAAABmkFRSFJLX0FIbmlyNjVBMFZiWnJIWk1kakNfZ2N2OWd5bEtwdFoyTTVicGdmZ1hMTXlJNHpUN1JydFVjZXY2b3NnT1E3Y24yZW01N0RWSl9JMjZYQXVPcm8wUlJyMGNWQTF6ejlRNEFXV19RbVdWV05RV1JHMW5JNDJkTEJYUUJkOFpzcHpRWk9ZNDlVUHh6cjNOcnhmS3FvRG5sNUJVYUpEQ0dTanpfUkFKc2NfMU9wNXd1c3hyZnl0Szlrc3BSR2JCdEVNVnQ2azZUZHF2QlRzWXpwSWxoZ3hSLVdCR3E4NGRkNWlQY2hULWRkSW9aNXhHOFhXblUyRW1FR1RQa2NxT3lvWEtpVFZpNmxtUWk4eGpENXlMZVY3Y2UwcXRtS3VuWUtxdllhX2kxNUl0LXdNcVRNM3Nwa0F1N2hlVnVQQzBScHltQzhyb3I3dVl6QnVTRUZ4Z0toZUhHNTBuS1FtemY0OXZsZkpaV0ExdnlYMm1sdWtJcmlxeE92aXR4RGE3MS1aeXJ5VF9rSXNUei1NREgtSUFlNWlRDwlhZF9jdXJzb3IODw9nbG9iYWxfcG9zaXRpb24CAA8Gb2Zmc2V0AgAPEGxhc3RfYWRfcG9zaXRpb24C/wE="
            all_posts = []
            post_ids = set()
            docid = Utils.load_json(docid).get("ProfileCometTimelineFeedRefetchQuery")
            cmt_api = Utils.load_json(comment_api_path)
            os.makedirs(save_dir, exist_ok=True)
            max_retry = 3
            retry_count = 0
            for round_idx in range(num_iterations):
                logger.info(f"--- ITER {round_idx+1} ---")
                prev_cursor = cursor  # Lưu lại cursor trước khi request
                resp = Requester._get_posts(headers, identifier, entryPoint, docid, cursor)
                if not resp or resp.status_code != 200:
                    logger.warning(f"Lỗi khi gửi request lấy post {resp.status_code if resp else 'No response'}")
                    break
                data_lines = [d for d in resp.text.split('\r\n', -1) if d.strip()]
                end_cursor_found = False
                for idx, data in enumerate(data_lines):
                    try:
                        obj = json.loads(data)
                        if idx == len(data_lines) - 1:
                            new_cursor = obj.get('data', {}).get('page_info', {}).get('end_cursor')
                            logger.info(f"end_cursor: {new_cursor}")
                            if new_cursor:
                                cursor = new_cursor
                                end_cursor_found = True
                            continue
                        post_info = Parser.parse_post_obj(obj, save_dir=save_dir)
                        post_id = post_info.get("feedback_id")
                        if post_info["post_content"] and post_id:
                            if post_id in post_ids:
                                continue  # Bỏ qua post đã lưu
                            post_ids.add(post_id)
                            post_url = post_info.get("post_url")
                            comments = []
                            if post_url and post_id:
                                comment_api = cmt_api.get('CommentListComponentsRootQuery')
                                more_comment_api = cmt_api.get('CommentsListComponentsPaginationQuery')
                                cmt_headers = Requester._get_headers(post_url)
                                resp_cmt = Requester._get_comments(cmt_headers, post_id, comment_api)
                                if resp_cmt and resp_cmt.status_code == 200:
                                    comment_info = Parser.parse_comments_info(resp_cmt, save_dir=save_dir)
                                    page_info = Parser.parse_page_info(resp_cmt)
                                    comments.extend(comment_info.get('comments', []))
                                    # Giới hạn 300 comment
                                    if len(comments) >= 300:
                                        comments = comments[:300]
                                    else:
                                        iter_cmt = 1
                                        while page_info.get('has_next_page') and len(comments) < 300:
                                            logger.info(f"Lấy thêm comment lần {iter_cmt} cho post {post_id}")
                                            end_cursor = page_info.get('end_cursor')
                                            resp_cmt = Requester._get_more_comments(cmt_headers, post_id, more_comment_api, end_cursor)
                                            if resp_cmt and resp_cmt.status_code == 200:
                                                more_comments = Parser.parse_comments(resp_cmt.json(), save_dir=save_dir)
                                                comments.extend(more_comments)
                                                if len(comments) >= 300:
                                                    comments = comments[:300]
                                                    break
                                                page_info = Parser.parse_page_info(resp_cmt)
                                                iter_cmt += 1
                                            else:
                                                break
                            post_info["comments"] = comments
                            all_posts.append(post_info)
                    except Exception as e:
                        logger.warning(f"Lỗi dòng: {e}")
                if not end_cursor_found:
                    retry_count += 1
                    logger.warning(f"Không lấy được end_cursor, thử lại lần {retry_count}/{max_retry} với cursor cũ.")
                    cursor = prev_cursor
                    time.sleep(3)
                    if retry_count >= max_retry:
                        logger.error("Vượt quá số lần retry, dừng crawl.")
                        break
                    continue
                retry_count = 0
                if not cursor:
                    logger.info("Không còn cursor để crawl tiếp.")
                    break
                time.sleep(20)
            os.makedirs("data/json", exist_ok=True)
            fanpage_name = page_url.rstrip('/').split('/')[-1] or "unknown"
            file_path = f"data/json/posts_{fanpage_name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_posts, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu thông tin các post vào {file_path}")
            if return_posts:
                return all_posts
        except Exception as e:
            logger.error(f"Lỗi khi lấy post {e}")
            raise Exception(f"Lỗi khi lấy post {e}")

if __name__ == "__main__":
    post_api_path = "./api_info/post_api.json"
    comment_api_path = "./api_info/comment_api.json"
    scraper = FacebookScraper()
    all_posts = []
    post_ids = set()
    with open("./facebook_urls/page_urls.txt", "r", encoding="utf-8") as f:
        for line in f:
            fanpage_url = line.strip()
            if fanpage_url:
                logger.info(f"=== Bắt đầu crawl fanpage: {fanpage_url} ===")
                posts = scraper.crawl_post(fanpage_url, post_api_path, comment_api_path=comment_api_path, num_iterations=30, return_posts=True)
                for post in posts:
                    post_id = post.get("feedback_id")
                    if post_id and post_id not in post_ids:
                        all_posts.append(post)
                        post_ids.add(post_id)
    os.makedirs("data/json", exist_ok=True)
    with open("data/json/all_posts.json", "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    logger.info("Đã lưu tất cả post vào data/json/all_posts.json")
    logger.info("=== Hoàn thành việc crawl fanpage ===")
    logger.info(f"Tổng số post đã crawl: {len(all_posts)}")