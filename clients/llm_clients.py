import requests

import json

import time

import logging

from typing import Any, Dict, Optional, Union
 
logger = logging.getLogger(__name__)
 
class LLMClient:

    def __init__(self, base_url: str, verify_ssl: bool = False):

        if base_url.endswith("/"):

            base_url = base_url[:-1]

        self.base_url = base_url

        self.session = requests.Session()

        self.session.verify = verify_ssl  # Disable SSL verification globally if False
 
        # Optional: suppress only the "InsecureRequestWarning"

        if not verify_ssl:

            from urllib3.exceptions import InsecureRequestWarning

            import urllib3

            urllib3.disable_warnings(InsecureRequestWarning)
 
    def ping(self) -> bool:

        url = f"{self.base_url}/ping"

        try:

            response = self.session.get(url, timeout=5)

            response.raise_for_status()

            logger.info(f"Ping successful: {response.text}")

            return True

        except requests.exceptions.RequestException as e:

            logger.error(f"Ping failed: {e}")

            return False
 
    def submit_llm_request(

        self,

        model: str,

        query_text: str,

        seed: int = 42,

        temperature: float = 0.8,

        top_k: int = 20,

        top_p: float = 0.9,

        keep_alive: str = "30m",

    ) -> Optional[str]:

        url = f"{self.base_url}/llm_config"

        params = {

            "model": model,

            "seed": seed,

            "temperature": temperature,

            "top_k": top_k,

            "top_p": top_p,

            "keep_alive": keep_alive,

        }

        payload = {"query": query_text}
 
        try:

            logger.info(

                f"Submitting request to {url} with params={params} and payload={payload}"

            )

            response = self.session.post(url, params=params, json=payload, timeout=30)

            response.raise_for_status()

            request_id = response.text.strip('"')

            logger.info(f"Request submitted successfully. Request ID: {request_id}")

            return request_id

        except requests.exceptions.HTTPError as e:

            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")

            return None

        except requests.exceptions.RequestException as e:

            logger.error(f"Request error: {e}")

            return None

        except Exception as e:

            logger.error(f"Unexpected error: {e}")

            return None
 
    def retrieve_result(

        self, request_id: str, poll_interval: float = 2.0, timeout: float = 300.0

    ) -> Union[str, list, Dict[str, Any], None]:

        url = f"{self.base_url}/retrieve"

        params = {"request_id": request_id, "action": "GENERATE"}

        start_time = time.time()
 
        logger.info(f"Polling for request_id: {request_id}")
 
        while time.time() - start_time < timeout:

            try:

                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 200:

                    try:

                        return response.json()

                    except json.JSONDecodeError:

                        logger.warning("Received plain text instead of JSON.")

                        return response.text

                elif response.status_code == 202:

                    time.sleep(poll_interval)

                else:

                    logger.error(

                        f"Error retrieving result: {response.status_code} - {response.text}"

                    )

                    response.raise_for_status()

            except requests.exceptions.RequestException as e:

                logger.error(f"Polling error: {e}")

                time.sleep(poll_interval)

            except Exception as e:

                logger.error(f"Unexpected polling error: {e}")

                return None
 
        logger.error(f"Timeout reached while polling for request_id: {request_id}")

        return None
 
    def generate_text(

        self,

        model: str,

        query_text: str,

        seed: int = 42,

        temperature: float = 0.8,

        top_k: int = 20,

        top_p: float = 0.9,

        keep_alive: str = "30m",

        poll_interval: float = 2.0,

        timeout: float = 300.0,

    ) -> Union[str, list, Dict[str, Any], None]:

        logger.info("Starting generation process...")
 
        if not self.ping():

            logger.error("Server ping failed.")

            return None
 
        request_id = self.submit_llm_request(

            model=model,

            query_text=query_text,

            seed=seed,

            temperature=temperature,

            top_k=top_k,

            top_p=top_p,

            keep_alive=keep_alive,

        )
 
        if not request_id:

            logger.error("Failed to submit request.")

            return None
 
        return self.retrieve_result(request_id, poll_interval, timeout)
