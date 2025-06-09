import requests
from logger import setup_logger
import re
import time

logger = setup_logger(__name__)

class Requester():
    @staticmethod
    def _get_headers(pageurl):
        '''
        Send a request to get cookieid as headers.
        '''
        pageurl = re.sub('www', 'm', pageurl)
        resp = requests.get(pageurl)
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en'
        }
        cookies = resp.cookies.get_dict()
        headers['cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])
        return headers

    @staticmethod
    def _get_homepage(pageurl, headers):
        '''
        Send a request to get the homepage response
        '''
        pageurl = re.sub('/$', '', pageurl)
        timeout_cnt = 0
        while True:
            try:
                homepage_response = requests.get(pageurl, headers=headers, timeout=3)
                return homepage_response
            except:
                time.sleep(5)
                timeout_cnt += 1
                if timeout_cnt > 20:
                    class homepage_response:
                        text = 'Sorry, something went wrong.'
                    return homepage_response

    @staticmethod
    def _parse_entryPoint(homepage_response):
        try:
            entryPoint = re.findall(
                '"entryPoint":{"__dr":"(.*?)"}}', homepage_response.text)[0]
        except:
            entryPoint = 'nojs'
        return entryPoint

    @staticmethod
    def _parse_identifier(entryPoint, homepage_response):
        identifier = ""
        if entryPoint in ['ProfilePlusCometLoggedOutRouteRoot.entrypoint', 'CometGroupDiscussionRoot.entrypoint']:
            if len(re.findall('"identifier":"{0,1}([0-9]{5,})"{0,1},', homepage_response.text)) >= 1:
                identifier = re.findall('"identifier":"{0,1}([0-9]{5,})"{0,1},', homepage_response.text)[0]
            elif len(re.findall('fb://profile/(.*?)"', homepage_response.text)) >= 1:
                identifier = re.findall('fb://profile/(.*?)"', homepage_response.text)[0]
            elif len(re.findall('content="fb://group/([0-9]{1,})" />', homepage_response.text)) >= 1:
                identifier = re.findall('content="fb://group/([0-9]{1,})" />', homepage_response.text)[0]
        elif entryPoint in ['CometSinglePageHomeRoot.entrypoint', 'nojs']:
            if len(re.findall('"pageID":"{0,1}([0-9]{5,})"{0,1},', homepage_response.text)) >= 1:
                identifier = re.findall('"pageID":"{0,1}([0-9]{5,})"{0,1},', homepage_response.text)[0]
        return identifier

    @staticmethod
    def _get_comments(headers: dict, post_id: str, get_post_api: str) -> requests.Response:
        data = {
            "variables": str({
                "commentsIntentToken": "RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1",
                "scale": 1,
                "id": post_id,
                "__relay_internal__pv__IsWorkUserrelayprovider": "false"
            }),
            "doc_id": get_post_api
        }

        url = "https://www.facebook.com/api/graphql/"
        try:
            resp = requests.post(url, data=data, headers=headers)
            return resp
        except Exception as e:
            logger.info(f"Lỗi khi request comment {e}")
            return None 

    @staticmethod
    def _get_more_comments(headers: dict, post_id: str, get_post_api: str, end_cursor: str) -> requests.Response:
        data = {
            "variables": str({"commentsAfterCount": -1,
                              "commentsAfterCursor": end_cursor, 
                              "commentsIntentToken": "RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1",
                              "scale": 1,
                              "id": post_id,
                              "__relay_internal__pv__IsWorkUserrelayprovider": "false"
            }),
            "doc_id": get_post_api
        }

        url = "https://www.facebook.com/api/graphql/"

        try:
            resp = requests.post(url, data=data, headers=headers)
            return resp
        except Exception as e:
            logger.info(f"Lỗi khi request comment {e}")
            return None 

    @staticmethod
    def _get_posts(headers: dict, identifier: str, entryPoint: str, docid: str, cursor: str = "") -> requests.Response:
        data = {
            'variables': str({
                'cursor': cursor,
                'id': identifier,
                'count': 3
            }),
            'doc_id': docid
        }
        try:
            resp = requests.post(
                url='https://www.facebook.com/api/graphql/',
                data=data,
                headers=headers
            )
            return resp
        except Exception as e:
            logger.info(f"Lỗi khi request post {e}")
            return None
        