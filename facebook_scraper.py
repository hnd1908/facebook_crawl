import pandas as pd
from utils import Utils
from logger import setup_logger
from requester import Requester
from parser import Parser
import os
import json

logger = setup_logger(__name__)

class FacebookScraper():
    def crawl_post(self, page_url: str, docid: str, save_dir="data\\image", num_iterations=3, comment_api_path="./api_info/comment_api.json"):
        try:
            logger.info(f"Thực hiện lấy post và comment từng post:")
            headers = Requester._get_headers(page_url)
            homepage_response = Requester._get_homepage(page_url, headers)
            entryPoint = Requester._parse_entryPoint(homepage_response)
            identifier = Requester._parse_identifier(entryPoint, homepage_response)
            cursor = ""
            all_posts = []
            docid = Utils.load_json(docid).get("ProfileCometTimelineFeedRefetchQuery")
            cmt_api = Utils.load_json(comment_api_path)
            os.makedirs(save_dir, exist_ok=True)
            for round_idx in range(num_iterations):
                logger.info(f"--- ITER {round_idx+1} ---")
                resp = Requester._get_posts(headers, identifier, entryPoint, docid, cursor)
                if not resp or resp.status_code != 200:
                    logger.warning(f"Lỗi khi gửi request lấy post {resp.status_code if resp else 'No response'}")
                    break
                data_lines = [d for d in resp.text.split('\r\n', -1) if d.strip()]
                for idx, data in enumerate(data_lines):
                    try:
                        obj = json.loads(data)
                        if idx == len(data_lines) - 1:
                            cursor = obj.get('data', {}).get('page_info', {}).get('end_cursor')
                            logger.info(f"end_cursor: {cursor}")
                            continue
                        post_info = Parser.parse_post_obj(obj, save_dir=save_dir)
                        if post_info["post_content"]:
                            post_url = post_info.get("post_url")
                            post_id = post_info.get("feedback_id")
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
                                    iter_cmt = 1
                                    while page_info.get('has_next_page'):
                                        logger.info(f"Lấy thêm comment lần {iter_cmt} cho post {post_id}")
                                        end_cursor = page_info.get('end_cursor')
                                        resp_cmt = Requester._get_more_comments(cmt_headers, post_id, more_comment_api, end_cursor)
                                        if resp_cmt and resp_cmt.status_code == 200:
                                            more_comments = Parser.parse_comments(resp_cmt.json(), save_dir=save_dir)
                                            comments.extend(more_comments)
                                            page_info = Parser.parse_page_info(resp_cmt)
                                            iter_cmt += 1
                                        else:
                                            break
                            post_info["comments"] = comments
                            all_posts.append(post_info)
                    except Exception as e:
                        logger.warning(f"Lỗi dòng: {e}")
                if not cursor:
                    logger.info("Không còn cursor để crawl tiếp.")
                    break
            os.makedirs("data/json", exist_ok=True)
            with open("data/json/posts.json", "w", encoding="utf-8") as f:
                json.dump(all_posts, f, ensure_ascii=False, indent=2)
            logger.info("Đã lưu thông tin các post vào data/json/posts.json")
        except Exception as e:
            logger.error(f"Lỗi khi lấy post {e}")
            raise Exception(f"Lỗi khi lấy post {e}")

if __name__ == "__main__":
    fanpage_url = "https://www.facebook.com/Theanh28/"
    post_api_path = "./api_info/post_api.json"
    comment_api_path = "./api_info/comment_api.json"
    scraper = FacebookScraper()
    scraper.crawl_post(fanpage_url, post_api_path, comment_api_path=comment_api_path)