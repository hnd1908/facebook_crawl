from typing import Tuple
import requests
from logger import setup_logger
import os

logger = setup_logger(__name__)

class Parser():
    @staticmethod
    def _get_payload(payload: str) -> dict:
        parser_payload = payload.strip().split('&')

        payload_dict = dict()
        for item in parser_payload:
            key, value = item.split('=')
            payload_dict[key] = value

        return payload_dict
    
    @staticmethod
    def _get_api_value(payload: str) -> Tuple[str, int]:
        payload_dict = Parser._get_payload(payload)
        
        api_name = payload_dict['fb_api_req_friendly_name']
        api_key = payload_dict['doc_id']

        return (api_name, api_key)
    
    @staticmethod
    def parse_total_cmt(resp_json: dict) -> int:
        total_cmt = resp_json['data']['node']['comment_rendering_instance_for_feed_location']['comments']['total_count']
        return total_cmt

    @staticmethod
    def parse_total_parent_cmt(resp_json: dict) -> int:
        total_parent_cmt = resp_json['data']['node']['comment_rendering_instance_for_feed_location']['comments']['count']
        return total_parent_cmt
    
    @staticmethod
    def parse_comments(resp_json: dict) -> list:
        edges = resp_json['data']['node']['comment_rendering_instance_for_feed_location']['comments']['edges']

        comments = list()
        for edge in edges:
            comment = {
                'text': "",
                'image': None
            }
            try:
                comment['text'] = edge['node']['body']['text']
            except Exception as e:
                logger.warning("Không tìm thấy text trong comment") 
            
            try:
                i = len(edge['node']['attachments'])
                comment['image'] = edge['node']['attachments'][i-1]['style_type_renderer']['attachment']['media']['image'] 
            except Exception as e:
                logger.warning("Không tìm thấy ảnh trong comment")

            comments.append(comment)

        return comments

    @staticmethod
    def parse_comments_info(resp: requests.Response) -> dict:
        resp_json = resp.json()
        comments_info = dict()

        comments_info['total_comment'] = Parser.parse_total_cmt(resp_json)
        # comments_info['total_parent_comment'] = Parser.parse_total_parent_cmt(resp_json)
        comments_info['comments'] = Parser.parse_comments(resp_json)

        return comments_info

    @staticmethod
    def parse_page_info(resp: requests.Response) -> str:
        resp_json = resp.json()
        page_info = resp_json['data']['node']['comment_rendering_instance_for_feed_location']['comments']['page_info']
        return page_info
    
    
    @staticmethod
    def extract_message_and_attachments(obj):
        message = ""
        attachments = []
        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']
                # print(node)
            else:
                node = obj['data']['node']
                # print(node)
            if 'label' not in obj:
                message = node['comet_sections']['content']['story']['comet_sections']['message']['story']['message']['text'].strip()
                attachments = node['comet_sections']['content']['story'].get('attachments', [])
            else:
                message = node['comet_sections']['content']['story']['comet_sections']['message']['story']['message']['text'].strip()
                attachments = node['comet_sections']['content']['story'].get('attachments', [])
        except Exception as e:
            logger.warning(f"Không lấy được text: {e}")
            attachments = []
        message = message.replace('\n', ' ').replace('\r', ' ')
        message = message.split('Theo:')[0].split('Nguồn:')[0].split('Cre:')[0].strip()
        return message, attachments
    
    @staticmethod
    def extract_post_url(obj):
        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']
            else:
                node = obj['data']['node']
            story = node['comet_sections']['content']['story']
            post_url = story.get("wwwURL", None)
            return post_url
        except Exception as e:
            logger.warning(f"Không lấy được post url: {e}")
            return None

    @staticmethod
    def extract_comment_count(obj):
        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']
            else:
                node = obj['data']['node']
            comment_count = node.get('comet_sections', {}) \
                .get('feedback', {}) \
                .get('story', {}) \
                .get('story_ufi_container', {}) \
                .get('story', {}) \
                .get('feedback_context', {}) \
                .get('feedback_target_with_context', {}) \
                .get('comment_list_renderer', {}) \
                .get('feedback', {}) \
                .get('comment_rendering_instance', {}) \
                .get('comments', {}) \
                .get('total_count', 0)
            return comment_count
        except Exception as e:
            logger.warning(f"Không lấy được comment count: {e}")
            return 0

    @staticmethod
    def extract_share_count(obj):
        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']
            else:
                node = obj['data']['node']
            feedback_ctx = node.get('comet_sections', {}) \
                .get('feedback', {}) \
                .get('story', {}) \
                .get('story_ufi_container', {}) \
                .get('story', {}) \
                .get('feedback_context', {}) \
                .get('feedback_target_with_context', {})
            
            summary = feedback_ctx.get('comet_ufi_summary_and_actions_renderer', {})
            feedback = summary.get('feedback', {})
            share_count = feedback.get('i18n_share_count', None)
            return share_count
        except Exception as e:
            logger.warning(f"Không lấy được share count: {e}")
            return None

    @staticmethod
    def extract_reactions(obj):
        total_reactions = 0
        reactions_detail = {}

        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']
            else:
                node = obj['data']['node']

            feedback_ctx = node.get('comet_sections', {}) \
                .get('feedback', {}) \
                .get('story', {}) \
                .get('story_ufi_container', {}) \
                .get('story', {}) \
                .get('feedback_context', {}) \
                .get('feedback_target_with_context', {})
            
            summary = feedback_ctx.get('comet_ufi_summary_and_actions_renderer', {})
            feedback = summary.get('feedback', {})
            total_reactions = feedback.get('reaction_count', {}).get('count', 0)
            top_reactions = feedback.get('top_reactions', {}).get('edges', [])
            
            for react in top_reactions:
                node_react = react.get('node', {})
                name = node_react.get('localized_name', 'Unknown')
                count = react.get('reaction_count', 0)
                reactions_detail[name] = count
                
        except Exception as e:
            logger.warning(f"Không lấy được reactions: {e}")
        return total_reactions, reactions_detail

    @staticmethod
    def extract_feedback_id(obj):
        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']
            else:
                node = obj['data']['node']
            feedback = node.get('feedback', {})
            feedback_id = feedback.get('id', None)
            return feedback_id
        except Exception as e:
            logger.warning(f"Không lấy được feedback id: {e}")
            return None

    @staticmethod
    def extract_creation_time(obj):
        try:
            if 'label' not in obj:
                node = obj['data']['node']['timeline_list_feed_units']['edges'][0]['node']['comet_sections']
            else:
                node = obj['data']['node']['comet_sections']
            timestamp = node.get('timestamp', {})
            story = timestamp.get('story', {})
            creation_time = story.get('creation_time', None)
            return creation_time
        except Exception as e:
            logger.warning(f"Không lấy được creation_time: {e}")
            return None

    @staticmethod
    def download_images_from_attachments(attachments, save_dir="data\\image"):
        image_paths = []
        for att in attachments:
            try:
                styles = att.get('styles', {})
                attachment = styles.get('attachment', {})
                if attachment.get('media', {}).get('__typename') == "Video":
                    print("Bỏ qua video.")
                    continue
                if 'all_subattachments' in attachment:
                    nodes = attachment['all_subattachments'].get('nodes', [])
                    for node in nodes:
                        media = node.get('media', {})
                        if media.get('__typename') == "Video":
                            print("Bỏ qua node video.")
                            continue
                        viewer_image = media.get('viewer_image', {})
                        uri = viewer_image.get('uri')
                        if uri:
                            filename = os.path.join(save_dir, os.path.basename(uri.split("?")[0]))
                            img = requests.get(uri)
                            with open(filename, "wb") as f:
                                f.write(img.content)
                            print(f"Đã lưu ảnh: {filename}")
                            image_paths.append(filename)
                elif 'media' in attachment:
                    media = attachment['media']
                    if media.get('__typename') == "Video":
                        print("Bỏ qua media video.")
                        continue
                    uri = media.get('photo_image', {}).get('uri')
                    if uri:
                        filename = os.path.join(save_dir, os.path.basename(uri.split("?")[0]))
                        img = requests.get(uri)
                        with open(filename, "wb") as f:
                            f.write(img.content)
                        print(f"-- Đã lưu ảnh: {filename}")
                        image_paths.append(filename)
            except Exception as e:
                print("Không lấy được ảnh:", e)
        return image_paths

    @staticmethod
    def parse_post_obj(obj, save_dir="data\\image"):
        message, attachments = Parser.extract_message_and_attachments(obj)
        total_reactions, reactions_detail = Parser.extract_reactions(obj)
        feedback_id = Parser.extract_feedback_id(obj)
        creation_time = Parser.extract_creation_time(obj)
        share_count = Parser.extract_share_count(obj)
        comment_count = Parser.extract_comment_count(obj)
        image_paths = Parser.download_images_from_attachments(attachments, save_dir)
        post_url = Parser.extract_post_url(obj)
        return {
            "post_content": message,
            "image_paths": image_paths,
            "feedback_id": feedback_id,
            "creation_time": creation_time,
            "total_reactions": total_reactions,
            "reactions_detail": reactions_detail,
            "share_count": share_count,
            "comment_count": comment_count,
            "post_url": post_url
        }



        