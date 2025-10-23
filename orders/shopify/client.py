import requests
from django.conf import settings

class ShopifyClient:
    def __init__(self, shop_url: str = None, api_key: str = None):
        self.shop_url = shop_url or settings.SHOPIFY_SHOP_URL
        self.api_key = api_key or settings.SHOPIFY_ADMIN_TOKEN

        if not self.shop_url or not self.api_key:
            raise ValueError('Shop URL and API key are required')

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': self.api_key
        })
        self.api_version = settings.SHOPIFY_API_VERSION
        self.base_url = f'{self.shop_url}/admin/api/{self.api_version}'
        self.timeout = settings.SHOPIFY_TIMEOUT
        self.api_scopes = settings.SHOPIFY_API_SCOPES

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        try:
            response = self.session.request(
                method,
                f'{self.base_url}{endpoint}',
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f'Error requesting Shopify API: {e}')

    def get_order(self, order_id: str) -> dict: # Get an order by ID
        return self._request('GET', f'/orders/{order_id}.json')

    def create_order(self, order_data: dict) -> dict: # Create a new order
        return self._request('POST', '/orders.json', json=order_data)

    def get_fulfillment(self, order_id: str, fulfillment_id: str) -> dict: # Get a fulfillment by ID
        return self._request('GET', f'/orders/{order_id}/fulfillments/{fulfillment_id}.json')

    def get_fulfillments(self, order_id: str) -> list:
        return self._request('GET', f'/orders/{order_id}/fulfillments.json')

    def create_fulfillment(self, order_id: str, fulfillment_data: dict) -> dict: # Create a new fulfillment for an order
        return self._request('POST', f'/orders/{order_id}/fulfillments.json', json=fulfillment_data)

    def update_fulfillment(self, order_id: str, fulfillment_id: str, fulfillment_data: dict) -> dict:
        return self._request('PUT', f'/orders/{order_id}/fulfillments/{fulfillment_id}.json', json=fulfillment_data)

    def cancel_fulfillment(self, order_id: str, fulfillment_id: str) -> dict: # Cancel a fulfillment for an order
        return self._request('DELETE', f'/orders/{order_id}/fulfillments/{fulfillment_id}.json')

    # Inventory Level Methods
    def get_inventory_levels(self, inventory_item_ids: str = None, location_ids: str = None, limit: int = 50, updated_at_min: str = None) -> dict:
        """Get inventory levels. Pass comma-separated IDs for inventory_item_ids and/or location_ids."""
        params = {}
        if inventory_item_ids:
            params['inventory_item_ids'] = inventory_item_ids
        if location_ids:
            params['location_ids'] = location_ids
        if limit:
            params['limit'] = limit
        if updated_at_min:
            params['updated_at_min'] = updated_at_min
        return self._request('GET', '/inventory_levels.json', params=params)

    def set_inventory_level(self, inventory_item_id: int, location_id: int, available: int) -> dict:
        """Set the inventory level for an inventory item at a location."""
        payload = {
            'inventory_item_id': inventory_item_id,
            'location_id': location_id,
            'available': available
        }
        return self._request('POST', '/inventory_levels/set.json', json=payload)

    def adjust_inventory_level(self, inventory_item_id: int, location_id: int, available_adjustment: int) -> dict:
        """Adjust inventory level by a delta (positive or negative)."""
        payload = {
            'inventory_item_id': inventory_item_id,
            'location_id': location_id,
            'available_adjustment': available_adjustment
        }
        return self._request('POST', '/inventory_levels/adjust.json', json=payload)

    def connect_inventory_item(self, inventory_item_id: int, location_id: int, relocate_if_necessary: bool = False) -> dict:
        """Connect an inventory item to a location."""
        payload = {
            'inventory_item_id': inventory_item_id,
            'location_id': location_id,
            'relocate_if_necessary': relocate_if_necessary
        }
        return self._request('POST', '/inventory_levels/connect.json', json=payload)

    def disconnect_inventory_item(self, inventory_item_id: int, location_id: int) -> dict:
        """Disconnect an inventory item from a location."""
        params = {
            'inventory_item_id': inventory_item_id,
            'location_id': location_id
        }
        return self._request('DELETE', '/inventory_levels.json', params=params)

    # Inventory Item Methods
    def get_inventory_item(self, inventory_item_id: int) -> dict:
        """Get a single inventory item by ID."""
        return self._request('GET', f'/inventory_items/{inventory_item_id}.json')

    def get_inventory_items(self, ids: str) -> dict:
        """Get multiple inventory items. Pass comma-separated IDs (max 100)."""
        params = {'ids': ids}
        return self._request('GET', '/inventory_items.json', params=params)

    def update_inventory_item(self, inventory_item_id: int, inventory_item_data: dict) -> dict:
        """Update an inventory item's details (SKU, cost, tracked status, etc.)."""
        return self._request('PUT', f'/inventory_items/{inventory_item_id}.json', json={'inventory_item': inventory_item_data})

    # Location Methods
    def get_locations(self) -> dict:
        """Get all locations."""
        return self._request('GET', '/locations.json')

    def get_location(self, location_id: int) -> dict:
        """Get a specific location by ID."""
        return self._request('GET', f'/locations/{location_id}.json')

    def get_location_inventory_levels(self, location_id: int) -> dict:
        """Get all inventory levels at a specific location."""
        return self._request('GET', f'/locations/{location_id}/inventory_levels.json')
