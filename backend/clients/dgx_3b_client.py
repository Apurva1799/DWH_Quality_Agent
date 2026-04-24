import json

import time
 
import requests
 
# Define custom exceptions for clarity
 
 
class NIMClientError(Exception):

    """Base exception for NIM client errors."""
 
 
class HealthCheckFailedError(NIMClientError):

    """Raised when the NIM API health check fails."""
 
 
class GenerationRequestFailedError(NIMClientError):

    """Raised when submitting a generation request fails."""
 
 
class RetrievalFailedError(NIMClientError):

    """Raised when retrieving a response fails."""
 
 
class NIMRateLimitError(NIMClientError):

    """Specific error for rate limiting or 429s if they were to occur."""
 
 
class NIMTimeoutError(NIMClientError):

    """Raised when an operation times out on the client side."""
 
 
class LLM_3B_Client:

    DEFAULT_POLL_INTERVAL_SECONDS = 0.5

    # Overall timeout for the client polling loop

    DEFAULT_RETRIEVE_TIMEOUT_SECONDS = 120.0

    # Timeout for the /retrieve API call itself

    DEFAULT_API_RETRIEVE_BUFFER_TIMEOUT = 30.0
 
    def __init__(self, base_url: str, verify_ssl: bool = False):

        """

        Initializes the LLM_3B_Client.
 
        Args:

            base_url (str): The base URL of the NIM API (e.g., "https://10.7.30.1:8193").

            verify_ssl (bool): Whether to verify SSL certificates. Defaults to False.

                               Set to True if you have a trusted certificate for the NIM server.

        """

        if base_url.endswith("/"):

            base_url = base_url[:-1]

        self.base_url = base_url

        self.session = requests.Session()

        self.session.verify = verify_ssl

        # You might want to disable warnings if verify_ssl is False

        if not verify_ssl:

            requests.packages.urllib3.disable_warnings(

                requests.packages.urllib3.exceptions.InsecureRequestWarning

            )
 
    def _make_request(self, method: str, endpoint: str, **kwargs):

        """Helper function to make requests and handle common errors."""

        url = f"{self.base_url}{endpoint}"

        try:

            response = self.session.request(method, url, **kwargs)

            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)

            return response

        except requests.exceptions.HTTPError as e:

            # Try to get more details from the response body if available

            error_detail = ""

            try:

                error_detail = e.response.json()

            except json.JSONDecodeError:

                error_detail = e.response.text
 
            if e.response.status_code == 422:

                raise RetrievalFailedError(

                    f"Validation Error at {url}: {error_detail} (Status {e.response.status_code})"

                ) from e

            elif e.response.status_code == 400:

                raise GenerationRequestFailedError(

                    f"Bad Request at {url}: {error_detail} (Status {e.response.status_code})"

                ) from e

            elif e.response.status_code == 500:

                raise NIMClientError(

                    f"Server Error at {url}: {error_detail} (Status {e.response.status_code})"

                ) from e

            raise NIMClientError(

                f"HTTP error {e.response.status_code} for {url}: {error_detail}"

            ) from e

        except requests.exceptions.ConnectionError as e:

            raise NIMClientError(f"Connection error for {url}: {e}") from e

        except requests.exceptions.Timeout as e:

            raise NIMTimeoutError(f"Request to {url} timed out: {e}") from e

        except requests.exceptions.RequestException as e:

            raise NIMClientError(f"Error during request to {url}: {e}") from e
 
    def health_check(self) -> bool:

        """

        Performs a health check on the NIM API.
 
        Returns:

            bool: True if the service is healthy.
 
        Raises:

            HealthCheckFailedError: If the health check fails.

        """

        try:

            response = self._make_request(

                "GET", "/health", timeout=5

            )  # Short timeout for health check

            if response.status_code == 200:

                print("Health check passed. Service is healthy.")

                return True

            else:  # Should be caught by raise_for_status, but as a fallback

                raise HealthCheckFailedError(

                    f"Health check failed with status {response.status_code}: {response.text}"

                )

        except NIMClientError as e:

            raise HealthCheckFailedError(f"Health check failed: {e}") from e
 
    def _submit_llm_config(

        self, query: str, model: str, rate: int, group_id: str = None

    ) -> str:

        """

        Submits the generation request to the /llm_config endpoint.
 
        Args:

            query (str): The user query or prompt.

            model (str): The model to use (e.g., "meta/llama-3.2-3b-instruct").

            rate (int): The token output rate.

            group_id (str, optional): Optional identifier to group multiple requests.
 
        Returns:

            str: The request ID.
 
        Raises:

            GenerationRequestFailedError: If the request submission fails.

        """

        endpoint = "/llm_config"

        params = {"model": model, "rate": rate}

        if group_id:

            params["group_id"] = group_id
 
        payload = {"query": query}
 
        try:

            print(

                f"Submitting to {self.base_url}{endpoint} with params={params} and payload={payload}"

            )

            response = self._make_request(

                "POST", endpoint, params=params, json=payload, timeout=10

            )  # Timeout for submission

            # The API doc says the response is a string for request ID

            request_id = response.json()

            if not isinstance(request_id, str):

                raise GenerationRequestFailedError(

                    f"Expected string request_id, got {type(request_id)}: {request_id}"

                )

            print(f"Generation request submitted. Request ID: {request_id}")

            return request_id

        except NIMClientError as e:

            raise GenerationRequestFailedError(

                f"Failed to submit LLM config: {e}"

            ) from e

        except json.JSONDecodeError as e:

            raise GenerationRequestFailedError(

                f"Failed to parse request_id from response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}"

            )
 
    def _retrieve_result_stream(

        self, request_id: str, api_retrieve_buffer_timeout: float

    ):

        """Handles streaming retrieval."""

        endpoint = "/retrieve"

        params = {

            "request_id": request_id,

            "stream": True,

            "timeout": api_retrieve_buffer_timeout,

        }

        # For streaming, self._make_request needs to be called with stream=True

        # and we handle the response object directly

        url = f"{self.base_url}{endpoint}"

        try:

            # Use session.post directly for streaming control

            response = self.session.post(

                url,

                params=params,

                stream=True,

                timeout=api_retrieve_buffer_timeout + 5,

                verify=self.session.verify,

            )

            response.raise_for_status()
 
            # Assuming line-delimited text chunks for LLM stream

            # The API doc says the 200 response is application/json with schema "string"

            # This is unusual for streaming. If it's truly one single JSON string streamed,

            # iter_content would be more appropriate. If it's a sequence of JSON strings (one per line)

            # then iter_lines and json.loads on each line.

            # Given the simple "string" schema, it's likely just text chunks.

            for line in response.iter_lines(decode_unicode=True):

                if line:  # filter out keep-alive new lines

                    yield line
 
        except requests.exceptions.HTTPError as e:

            error_detail = ""

            try:

                error_detail = e.response.json()

            except BaseException:

                error_detail = e.response.text

            if (

                e.response.status_code == 202

            ):  # Buffer filling, not an error for the generator itself

                yield "STATUS_202_BUFFERING"  # Special marker, or could handle silently

            elif e.response.status_code == 404:

                raise RetrievalFailedError(

                    f"Request ID {request_id} not found (404)."

                ) from e

            elif e.response.status_code == 408:

                raise NIMTimeoutError(

                    f"Request for ID {request_id} timed out on server (408)."

                ) from e

            elif e.response.status_code == 410:

                raise RetrievalFailedError(

                    f"Request ID {request_id} discarded (410). Do not retry."

                ) from e

            else:

                raise RetrievalFailedError(

                    f"HTTP error {e.response.status_code} during streaming retrieval for {request_id}: {error_detail}"

                ) from e

        except requests.exceptions.RequestException as e:

            raise RetrievalFailedError(

                f"Error during streaming retrieval for {request_id}: {e}"

            ) from e
 
    def _retrieve_result_non_stream(

        self,

        request_id: str,

        api_retrieve_buffer_timeout: float,

        poll_interval_seconds: float,

        overall_retrieve_timeout_seconds: float,

    ):

        """Handles non-streaming (polling) retrieval."""

        endpoint = "/retrieve"

        params = {

            "request_id": request_id,

            "stream": False,

            "timeout": api_retrieve_buffer_timeout,

        }
 
        start_time = time.time()

        while True:

            if time.time() - start_time > overall_retrieve_timeout_seconds:

                raise NIMTimeoutError(

                    f"Client-side polling timeout exceeded for request ID {request_id} after {overall_retrieve_timeout_seconds}s."

                )
 
            try:

                print(f"Polling /retrieve for request_id: {request_id} (stream=False)")

                # Note: self._make_request calls response.raise_for_status()

                # We need to handle 202 specifically before that.

                url = f"{self.base_url}{endpoint}"

                response = self.session.post(

                    url,

                    params=params,

                    timeout=api_retrieve_buffer_timeout + 5,

                    verify=self.session.verify,

                )
 
                if response.status_code == 200:

                    # API doc says response is application/json, example value "string"

                    # So response.json() should directly return the string.

                    content = response.json()

                    if not isinstance(content, str):

                        raise RetrievalFailedError(

                            f"Expected string content, got {type(content)}: {content}"

                        )

                    print(f"Successfully retrieved response for {request_id}.")

                    return content

                elif response.status_code == 202:

                    print(

                        f"Request ID {request_id} is still processing (202). Retrying in {poll_interval_seconds}s..."

                    )

                    time.sleep(poll_interval_seconds)

                    continue  # Retry the loop

                elif response.status_code == 404:

                    raise RetrievalFailedError(

                        f"Request ID {request_id} not found (404)."

                    )

                # Request timed out on server (buffer init)

                elif response.status_code == 408:

                    raise NIMTimeoutError(

                        f"Request for ID {request_id} timed out on server (408)."

                    )

                elif response.status_code == 410:  # Gone

                    raise RetrievalFailedError(

                        f"Request ID {request_id} has been discarded (410). Do not retry."

                    )

                else:

                    # For other non-200/202 codes, raise an error.

                    response.raise_for_status()  # This will raise an HTTPError
 
            except requests.exceptions.HTTPError as e:

                # This will catch errors raised by response.raise_for_status()

                error_detail = ""

                try:

                    error_detail = e.response.json()

                except BaseException:

                    error_detail = e.response.text

                raise RetrievalFailedError(

                    f"HTTP error {e.response.status_code} during retrieval for {request_id}: {error_detail}"

                ) from e

            # Catches ConnectionError, Timeout, etc.

            except requests.exceptions.RequestException as e:

                raise RetrievalFailedError(

                    f"Error during retrieval for {request_id}: {e}"

                ) from e

            except json.JSONDecodeError as e:

                raise RetrievalFailedError(

                    f"Failed to parse JSON response for {request_id}: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}"

                )
 
            time.sleep(poll_interval_seconds)
 
    def generate(

        self,

        query: str,

        model: str,

        stream: bool = False,

        rate: int = 100,

        group_id: str = None,

        overall_retrieve_timeout_seconds: float = DEFAULT_RETRIEVE_TIMEOUT_SECONDS,

        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,

        api_retrieve_buffer_timeout: float = DEFAULT_API_RETRIEVE_BUFFER_TIMEOUT,

    ):

        """

        Checks health, generates an LLM response, and retrieves it.
 
        Args:

            query (str): The user query or prompt.

            model (str): The model to use (e.g., "meta/llama-3.2-3b-instruct").

            stream (bool): If True, returns a generator for streaming response chunks.

                           If False (default), returns the complete response string after polling.

            rate (int): The token output rate (default 100). Min 10, Max 100.

            group_id (str, optional): Optional identifier to group multiple requests.

            overall_retrieve_timeout_seconds (float): Max time (seconds) the client will poll for non-streaming

                                                     or wait for the stream to start.

            poll_interval_seconds (float): Interval (seconds) between polling attempts for non-streaming.

            api_retrieve_buffer_timeout (float): Timeout (seconds, 0.1-120) for the /retrieve API

                                                 call's buffer initialization.
 
        Returns:

            str: If stream=False, the complete LLM response string.

            Generator[str, None, None]: If stream=True, a generator yielding response string chunks.
 
        Raises:

            HealthCheckFailedError: If the API is unhealthy.

            GenerationRequestFailedError: If submitting the generation task fails.

            RetrievalFailedError: If retrieving the response fails for terminal reasons.

            NIMTimeoutError: If a timeout occurs during polling or API interaction.

            NIMClientError: For other client-side errors.

        """

        if not 10 <= rate <= 100:

            raise ValueError("Rate must be between 10 and 100, inclusive.")

        if not 0.1 <= api_retrieve_buffer_timeout <= 120:

            raise ValueError(

                "API retrieve buffer timeout must be between 0.1 and 120 seconds."

            )
 
        # 1. Health Check

        self.health_check()  # Will raise HealthCheckFailedError if unhealthy
 
        # 2. Submit LLM Config

        request_id = self._submit_llm_config(query, model, rate, group_id)
 
        # 3. Retrieve Result

        if stream:

            print(f"Streaming response for request_id: {request_id}")

            # The _retrieve_result_stream now needs to handle the polling for 202 itself or initial connection

            # Let's design it to directly try to stream. If it gets 202, it might have to retry internally

            # or the user of the generator needs to be aware.

            # For simplicity, let's assume the /retrieve?stream=true will block until data is available

            # or return 202 if called too early. The API doc implies 200 for successful stream.

            # Let's make the generator handle the 202 retries for a bit.
 
            def stream_generator():

                start_time = time.time()

                retries_for_202 = 0

                max_retries_for_202 = int(

                    overall_retrieve_timeout_seconds / poll_interval_seconds

                )
 
                while True:

                    if time.time() - start_time > overall_retrieve_timeout_seconds:

                        raise NIMTimeoutError(

                            f"Client-side streaming timeout for request ID {request_id} after {overall_retrieve_timeout_seconds}s waiting for stream to start."

                        )
 
                    try:

                        # Create a new generator instance for each attempt if

                        # needed

                        chunk_iterator = self._retrieve_result_stream(

                            request_id, api_retrieve_buffer_timeout

                        )

                        first_chunk_retrieved = False

                        for chunk in chunk_iterator:

                            if chunk == "STATUS_202_BUFFERING":  # Our special marker

                                if (

                                    not first_chunk_retrieved

                                ):  # Only retry if it's the first thing we get

                                    print(

                                        f"Stream for {request_id} is buffering (202). Retrying in {poll_interval_seconds}s..."

                                    )

                                    time.sleep(poll_interval_seconds)

                                    retries_for_202 += 1

                                    if retries_for_202 > max_retries_for_202:

                                        raise NIMTimeoutError(

                                            f"Max retries for 202 status exceeded for request ID {request_id}."

                                        )

                                    break  # Break inner loop to retry the _retrieve_result_stream call

                                else:  # If we already got data, a 202 mid-stream is weird, maybe log and ignore

                                    print(

                                        f"Warning: Received 202 mid-stream for {request_id}. Ignoring."

                                    )

                                    continue

                            else:

                                first_chunk_retrieved = True

                                yield chunk
 
                        if (

                            first_chunk_retrieved

                        ):  # If we successfully iterated and got data

                            return  # End the generator

                        elif (

                            not first_chunk_retrieved

                            and chunk != "STATUS_202_BUFFERING"

                        ):  # Iterator finished without 202 or data

                            # This case might mean the stream ended prematurely or an error was handled inside _retrieve_result_stream

                            # If _retrieve_result_stream raises an exception, it will propagate out.

                            # If it completes silently, it means no more data.

                            return
 
                    except RetrievalFailedError as e:  # Terminal errors

                        print(f"Streaming failed permanently for {request_id}: {e}")

                        raise

                    except NIMTimeoutError as e:  # Timeout from server

                        print(f"Streaming timed out on server for {request_id}: {e}")

                        raise

                    # Non-terminal errors (like connection issues that aren't 202) might warrant a retry too

                    # but for now, we assume _retrieve_result_stream handles or

                    # raises terminal errors.
 
            return stream_generator()
 
        else:  # Non-streaming

            return self._retrieve_result_non_stream(

                request_id,

                api_retrieve_buffer_timeout,

                poll_interval_seconds,

                overall_retrieve_timeout_seconds,

            )
