import os

from typing import Any, Dict, List
 
import keyring

import requests

from dotenv import load_dotenv
 
 
class InvalidQueryError(Exception):

    """Custom exception for invalid queries in DocumentDB."""
 
 
class DocumentDBClientError(Exception):

    """Base exception for DocumentDB client errors"""
 
 
class AuthenticationError(DocumentDBClientError):

    """Raised when authentication fails"""
 
 
class ValidationError(DocumentDBClientError):

    """Raised when input validation fails"""
 
 
class ResourceAccessError(DocumentDBClientError):

    """Raised when accessing unauthorized resources"""
 
 
class InvalidQueryError(DocumentDBClientError):

    """Raised when query fails to match documents"""
 
 
class DocumentDBClient:

    def __init__(self, base_url: str = None, load_env: bool = True, ssl_verify=True):

        """

        Initialize the DocumentDB client.
 
        Args:

            base_url (str, optional): Base URL of the DocumentDB API. If not provided,

                                    will look for DOCUMENTDB_BASE_URL in environment.

            load_env (bool): Whether to load environment variables from .env file

        """

        if load_env:

            load_dotenv()
 
        self.base_url = base_url or os.getenv("DOCUMENTDB_BASE_URL")

        if not self.base_url:

            raise DocumentDBClientError(

                "Base URL not provided and DOCUMENTDB_BASE_URL not found in environment"

            )
 
        self.base_url = self.base_url.rstrip("/")

        self.token = None

        self._session = requests.Session()

        # Set default SSL verification for all requests made via self._session

        self.ssl_verify = ssl_verify

        self._session.verify = ssl_verify

        # Track last authenticated username for auto-relogin on 401

        self._username = None
 
    def save_credentials(self, username: str, password: str) -> None:

        """

        Save credentials securely using keyring.
 
        Args:

            username (str): Username

            password (str): Password

        """

        keyring.set_password("documentdb", username, password)
 
    def load_credentials(self, username: str) -> str:

        """

        Load credentials securely using keyring.
 
        Args:

            username (str): Username
 
        Returns:

            str: Password
 
        Raises:

            AuthenticationError: If credentials not found

        """

        password = keyring.get_password("documentdb", username)

        if not password:

            raise AuthenticationError(

                f"No stored credentials found for user: {username}"

            )

        return password
 
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:

        """Handle API response and raise appropriate exceptions"""

        try:

            response.raise_for_status()

            # Prefer JSON, but if not JSON return raw text for diagnostics

            try:

                return response.json()

            except ValueError:

                return {"raw_text": response.text}

        except requests.exceptions.HTTPError as e:

            # Try to extract error details from JSON; otherwise include raw text

            error_detail = "Unknown error"

            try:

                body = response.json()

                error_detail = body.get("detail") or body.get("message") or str(body)

            except BaseException:

                # Non-JSON response, include trimmed text

                error_detail = (response.text or "").strip()

            raise DocumentDBClientError(

                f"HTTP {response.status_code}: {error_detail}"

            )
 
    def create_document(

        self, db: str, collection: str, data: Dict[str, Any]

    ) -> Dict[str, str]:

        """

        Create a new document in the database.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            data (Dict[str, Any]): Document data
 
        Returns:

            Dict containing document ID
 
        Raises:

            AuthenticationError: If not authenticated

            ValidationError: If validation fails

            ResourceAccessError: If database access denied

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        base_endpoint = f"{self.base_url}/{db}/{collection}/create"
 
        # Attempt primary payload format

        try:

            return self._request_with_retry("POST", base_endpoint, json={"data": data})

        except DocumentDBClientError as primary_err:

            # Fallback 1: send raw document without wrapper

            try:

                return self._request_with_retry("POST", base_endpoint, json=data)

            except DocumentDBClientError as raw_err:

                # Fallback 2: try trailing slash endpoint

                alt_endpoint = base_endpoint + "/"

                return self._request_with_retry("POST", alt_endpoint, json={"data": data})
 
    def register(

        self, username: str, password: str, store_credentials: bool = True

    ) -> Dict[str, str]:

        """

        Register a new user.
 
        Args:

            username (str): Desired username

            password (str): Password

            store_credentials (bool): Whether to store credentials in keyring
 
        Returns:

            Dict containing registration confirmation
 
        Raises:

            DocumentDBClientError: If registration fails

        """

        response = self._session.post(

            f"{self.base_url}/register",

            params={"username": username, "password": password},

        )

        result = self._handle_response(response)
 
        if store_credentials:

            self.save_credentials(username, password)
 
        return result
 
    def login(

        self, username: str, password: str = None, use_stored: bool = True

    ) -> None:

        """

        Login and obtain access token.
 
        Args:

            username (str): Username

            password (str, optional): Password

            use_stored (bool): Whether to try loading stored credentials if password not provided
 
        Raises:

            AuthenticationError: If login fails or no credentials available

        """

        if password is None and use_stored:

            password = self.load_credentials(username)

        elif password is None:

            raise AuthenticationError("No password provided and use_stored=False")
 
        response = self._session.post(

            f"{self.base_url}/token", data={"username": username, "password": password}

        )

        result = self._handle_response(response)

        self.token = result["access_token"]

        self._session.headers.update({"Authorization": f"Bearer {self.token}"})

        # Remember username for future auto-relogin

        self._username = username
 
    def register_database(self, db: str, collection: str) -> Dict[str, str]:

        """

        Register a database and collection for use.
 
        Args:

            db (str): Database name

            collection (str): Collection name
 
        Returns:

            Dict containing registration confirmation
 
        Raises:

            AuthenticationError: If not authenticated

            ValidationError: If validation fails

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        response = self._session.post(

            f"{self.base_url}/register_database",

            json={"db": db, "collection": collection},

        )

        return self._handle_response(response)
 
    def register_encrypted_field(

        self, db: str, collection: str, field: str

    ) -> Dict[str, str]:

        """

        Register a field for encryption.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            field (str): Field name to encrypt
 
        Returns:

            Dict containing registration confirmation
 
        Raises:

            AuthenticationError: If not authenticated

            ValidationError: If validation fails

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        response = self._session.post(

            f"{self.base_url}/register_field",

            json={"db": db, "collection": collection, "field": field},

        )

        return self._handle_response(response)
 
    def list_databases(self) -> List[Dict[str, str]]:

        """

        List all registered databases and collections.
 
        Returns:

            List of registered databases and collections
 
        Raises:

            AuthenticationError: If not authenticated

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        response = self._session.get(f"{self.base_url}/list_databases")

        return self._handle_response(response)
 
    def list_encrypted_fields(self) -> List[Dict[str, str]]:

        """

        List all registered encrypted fields.
 
        Returns:

            List of registered encrypted fields
 
        Raises:

            AuthenticationError: If not authenticated

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        response = self._session.get(f"{self.base_url}/list_fields")

        return self._handle_response(response)
 
    def update_document(

        self, db: str, collection: str, document_id: str, data: Dict[str, Any]

    ) -> Dict[str, int]:

        """

        Update a document in the database.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            document_id (str): Document ID

            data (Dict[str, Any]): Updated document data
 
        Returns:

            Dict containing modification count
 
        Raises:

            AuthenticationError: If not authenticated

            ResourceAccessError: If database access denied

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        # Ensure document_id is a string

        document_id = str(document_id)
 
        # Send update request

        url = f"{self.base_url}/{db}/{collection}/update/{document_id}"
 
        response = self._session.put(url, json={"data": data})
 
        return self._handle_response(response)
 
    def delete_document(

        self, db: str, collection: str, document_id: str

    ) -> Dict[str, int]:

        """

        Delete a document from the database.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            document_id (str): Document ID
 
        Returns:

            Dict containing deletion count
 
        Raises:

            AuthenticationError: If not authenticated

            ResourceAccessError: If database access denied

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        response = self._session.delete(

            f"{self.base_url}/{db}/{collection}/delete/{document_id}"

        )

        return self._handle_response(response)
 
    def list_documents(

        self, db: str, collection: str, skip: int = 0, limit: int = 100

    ) -> List[Dict[str, Any]]:

        """

        List documents in a collection with pagination.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            skip (int, optional): Number of documents to skip

            limit (int, optional): Maximum number of documents to return
 
        Returns:

            List of documents
 
        Raises:

            AuthenticationError: If not authenticated

            ResourceAccessError: If database access denied

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        response = self._session.get(

            f"{self.base_url}/{db}/{collection}/list",

            params={"skip": skip, "limit": limit},

        )

        return self._handle_response(response)
 
    def find_documents(

        self, db: str, collection: str, query: Dict[str, Any], function_name: str

    ) -> List[Dict[str, Any]]:

        """

        Find documents in the database based on a query.
 
        Args:

            db (str): Database name.

            collection (str): Collection name.

            query (Dict[str, Any]): MongoDB query as a dictionary.
 
        Returns:

            List[Dict[str, Any]]: List of documents matching the query, or None if no documents are found.
 
        Raises:

            AuthenticationError: If not authenticated.

            ResourceAccessError: If database access is denied.

            ValueError: If the query is invalid or response parsing fails.

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        try:

            # Debugging logs
 
            # Send the query to the FastAPI endpoint

            result = self._request_with_retry(

                "POST", f"{self.base_url}/{db}/{collection}/find/", json=query

            )

            # If no documents are found, return None

            if not result:

                return None

            return result
 
        except Exception as e:
 
            # Log error

            print(

                f"Error occurred in find_documents, called from {function_name}: {str(e)}"

            )

            return None  # Return None on failure
 
    def read_document(self, db_name: str, collection: str, user_id: str):

        """Retrieve a document by userID instead of _id"""

        url = f"{self.base_url}/{db_name}/{collection}/query"

        query = {"userID": user_id}  # Query by userID field
 
        response = self._session.post(

            url, json={"filter": query}, verify=self.ssl_verify

        )  # Use POST for querying
 
        if response.status_code == 404 or not response.json():

            return None  # No document found
 
        response.raise_for_status()
 
        docs = response.json()

        return docs[0] if docs else None  # Return first match
 
    def count_documents(

        self, db: str, collection: str, query: Dict[str, Any], function_name: str

    ) -> Dict[str, Any]:

        """

        Count documents in a collection that match the given query.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            query (Dict[str, Any]): Query filter

            function_name (str): Name of calling function for logging
 
        Returns:

            Dict containing count information
 
        Raises:

            AuthenticationError: If not authenticated

            ResourceAccessError: If database access denied

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        try:

            # Use the same endpoint pattern as find_documents which works

            url = f"{self.base_url}/{db}/{collection}/find/"

            response = self._session.post(

                url, json=query, verify=self.ssl_verify

            )

            if response.status_code == 200:

                result = response.json()

                count = len(result) if isinstance(result, list) else 0

                return {'count': count}

            else:

                return {'count': 0}

        except Exception as e:

            print(f"Error occurred in count_documents, called from {function_name}: {str(e)}")

            return {'count': 0}
 
    def delete_documents(

        self, db: str, collection: str, query: Dict[str, Any] = None

    ) -> Dict[str, Any]:

        """

        Delete multiple documents from the database based on a query.

        If no query is provided, deletes all documents in the collection.
 
        Args:

            db (str): Database name

            collection (str): Collection name

            query (Dict[str, Any], optional): Query to filter documents to delete
 
        Returns:

            Dict containing deletion result
 
        Raises:

            AuthenticationError: If not authenticated

            ResourceAccessError: If database access denied

        """

        if not self.token:

            raise AuthenticationError("Not authenticated. Please login first.")
 
        try:

            # Use empty query to delete all documents if no query provided

            delete_query = query if query is not None else {}

            response = self._session.post(

                f"{self.base_url}/{db}/{collection}/delete_many",

                json={"filter": delete_query},

                verify=self.ssl_verify

            )

            if response.status_code == 200:

                return response.json()

            else:

                # Fallback: try alternative endpoint

                response = self._session.delete(

                    f"{self.base_url}/{db}/{collection}/documents",

                    json={"filter": delete_query},

                    verify=self.ssl_verify

                )

                return self._handle_response(response)

        except Exception as e:

            print(f"Error in delete_documents: {str(e)}")

            return {"deleted_count": 0, "error": str(e)}
 
 
    def _get_credentials(self):

        """Resolve credentials for re-authentication, preferring keyring with fallback to environment."""

        try:

            if self._username:

                pwd = self.load_credentials(self._username)

                return self._username, pwd

        except AuthenticationError:

            pass

        env_user = os.getenv("DOCUMENTDB_USERNAME")

        env_pass = os.getenv("DOCUMENTDB_PASSWORD")

        if env_user and env_pass:

            return env_user, env_pass

        raise AuthenticationError("No stored credentials available for re-authentication")
 
    def _request_with_retry(self, method: str, url: str, json=None, data=None, params=None):

        """Perform a request and automatically re-login and retry once on HTTP 401."""

        # First attempt

        response = self._session.request(method, url, json=json, data=data, params=params)

        if response.status_code == 401:

            # Attempt to refresh authentication and retry once

            try:

                username, password = self._get_credentials()

                # Re-login to refresh token/header

                self.login(username, password=password, use_stored=False)

                # Retry the original request

                response = self._session.request(method, url, json=json, data=data, params=params)

            except Exception:

                # If re-login fails, proceed to standard error handling below

                pass

        return self._handle_response(response)
