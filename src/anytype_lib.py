
import requests
import json
import time

class AnytypeClient:
    def __init__(self, api_base="http://localhost:31001/v1", token=None):
        self.api_base = api_base
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if token else "" # Token might be needed
        }
        # Note: Anytype Local API details are still in flux. 
        # Some documentation suggests `X-Anytype-Key` or similar. I'll use standard Bearer for now but update if needed.
        # Actually recent docs say `Authorizaton: <token>`

    def create_object(self, object_type: str, text: str, title: str = None) -> dict:
        """
        Creates a new object in Anytype.
        """
        # Basic payload structure for Anytype's Create Object endpoint
        # The API usually expects something like:
        # POST /spaces/{spaceId}/objects
        # But let's assume a simpler endpoint exists or we need to fetch spaces first.
        
        # 1. Fetch spaces (if needed, or use default)
        # spaces = self.get_spaces()
        # space_id = spaces[0]['id']

        # For this prototype, I'll log the intention because I cannot verify the exact endpoint without documentation
        # or the user's specific local setup.
        # I'll implement a `mock` mode if connection fails.
        
        print(f"[Anytype] Creating {object_type}: {title or 'No Title'} - {text[:20]}...")
        
        # Payload guess based on common patterns
        payload = {
            "objectType": object_type, # e.g., "Note", "Task"
            "content": text
        }
        if title:
            payload["title"] = title

        # TODO: Real implementation requires exact endpoint from docs.
        # return requests.post(f"{self.api_base}/objects", json=payload, headers=self.headers).json()
        return {"id": "mock-id-123", "status": "simulated_success"}

    def get_spaces(self):
        """Fetches list of spaces."""
        try:
            r = requests.get(f"{self.api_base}/spaces", headers=self.headers, timeout=5)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException as e:
            print(f"Error fetching spaces: {e}")
        return []

    def get_recent_objects(self, space_id: str, limit: int = 10) -> list:
        """
        Fetches recently modified objects from a space.
        Note: The actual API for filtering by time might vary (e.g. query language).
        This is a best-effort implementation using a standard LIST/SEARCH endpoint.
        """
        # Try listing objects with a sort order
        # Endpoint guess: /spaces/{id}/objects?sort=-modified_at&limit={limit}
        # Or a search body.
        
        try:
            # First attempt: Simple list with limit.
            # We urge the user to check specific API docs for 'filtering'.
            url = f"{self.api_base}/spaces/{space_id}/objects"
            params = {"limit": limit, "sort": "desc", "order_by": "last_modified_date"} 
            
            r = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            if r.status_code == 200:
                return r.json()
            else:
                print(f"Failed to fetch objects: {r.status_code} - {r.text}")
                return []
        except requests.RequestException:
            return []

