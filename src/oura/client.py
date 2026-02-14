import httpx

from .auth import load_env, get_access_token, refresh_access_token

BASE_URL = "https://api.ouraring.com"


class OuraClient:
  def __init__(self):
    self._token = get_access_token()

  def _ensure_auth(self):
    if not self._token:
      raise RuntimeError("Not authenticated. Run 'oura auth' first.")

  def _bearer_headers(self) -> dict[str, str]:
    self._ensure_auth()
    return {"Authorization": f"Bearer {self._token}"}

  def _request(self, method: str, path: str, **kwargs) -> dict:
    url = f"{BASE_URL}{path}"
    response = httpx.request(method, url, headers=self._bearer_headers(), **kwargs)

    if response.status_code == 401:
      self._token = refresh_access_token()
      response = httpx.request(method, url, headers=self._bearer_headers(), **kwargs)

    response.raise_for_status()
    return response.json()

  # --- User data endpoints ---

  def get_data(
    self,
    data_type: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    next_token: str | None = None,
  ) -> dict:
    params: dict[str, str] = {}
    if start_date:
      params["start_date"] = start_date
    if end_date:
      params["end_date"] = end_date
    if next_token:
      params["next_token"] = next_token
    return self._request("GET", f"/v2/usercollection/{data_type}", params=params)

  def get_all_data(
    self,
    data_type: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
  ) -> dict:
    all_items: list = []
    next_token = None
    while True:
      data = self.get_data(
        data_type,
        start_date=start_date,
        end_date=end_date,
        next_token=next_token,
      )
      all_items.extend(data.get("data", []))
      next_token = data.get("next_token")
      if not next_token:
        break
    return {"data": all_items}

  def get_document(self, data_type: str, document_id: str) -> dict:
    return self._request("GET", f"/v2/usercollection/{data_type}/{document_id}")

  def get_personal_info(self) -> dict:
    return self._request("GET", "/v2/usercollection/personal_info")

  def get_heartrate(
    self,
    *,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    next_token: str | None = None,
  ) -> dict:
    params: dict[str, str] = {}
    if start_datetime:
      params["start_datetime"] = start_datetime
    if end_datetime:
      params["end_datetime"] = end_datetime
    if next_token:
      params["next_token"] = next_token
    return self._request("GET", "/v2/usercollection/heartrate", params=params)

  def get_all_heartrate(
    self,
    *,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
  ) -> dict:
    all_items: list = []
    next_token = None
    while True:
      data = self.get_heartrate(
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        next_token=next_token,
      )
      all_items.extend(data.get("data", []))
      next_token = data.get("next_token")
      if not next_token:
        break
    return {"data": all_items}

  # --- Webhook endpoints ---

  @staticmethod
  def _webhook_headers() -> dict[str, str]:
    client_id, client_secret = load_env()
    return {"x-client-id": client_id, "x-client-secret": client_secret}

  def list_webhooks(self) -> dict:
    r = httpx.get(f"{BASE_URL}/v2/webhook/subscription", headers=self._webhook_headers())
    r.raise_for_status()
    return r.json()

  def create_webhook(
    self,
    callback_url: str,
    verification_token: str,
    event_type: str,
    data_type: str,
  ) -> dict:
    r = httpx.post(
      f"{BASE_URL}/v2/webhook/subscription",
      headers=self._webhook_headers(),
      json={
        "callback_url": callback_url,
        "verification_token": verification_token,
        "event_type": event_type,
        "data_type": data_type,
      },
    )
    r.raise_for_status()
    return r.json()

  def get_webhook(self, webhook_id: str) -> dict:
    r = httpx.get(
      f"{BASE_URL}/v2/webhook/subscription/{webhook_id}",
      headers=self._webhook_headers(),
    )
    r.raise_for_status()
    return r.json()

  def delete_webhook(self, webhook_id: str) -> None:
    r = httpx.delete(
      f"{BASE_URL}/v2/webhook/subscription/{webhook_id}",
      headers=self._webhook_headers(),
    )
    r.raise_for_status()

  def renew_webhook(self, webhook_id: str) -> dict:
    r = httpx.put(
      f"{BASE_URL}/v2/webhook/subscription/renew/{webhook_id}",
      headers=self._webhook_headers(),
    )
    r.raise_for_status()
    return r.json()
