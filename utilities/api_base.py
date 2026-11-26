import os
import ssl

import requests
from requests.adapters import HTTPAdapter

from utilities import config


# Trusts a local CA bundle (needed behind a filtering proxy such as Netfree on Python 3.13+).
class _CustomCAAdapter(HTTPAdapter):

    # Builds an SSL context from the bundle without the strict X.509 check that rejects the proxy's certificate.
    def __init__(self, ca_bundle: str, **kwargs):
        self._context = ssl.create_default_context(cafile=ca_bundle)
        self._context.verify_flags &= ~ssl.VERIFY_X509_STRICT
        super().__init__(**kwargs)

    # Makes every HTTPS connection use that SSL context.
    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._context
        return super().init_poolmanager(*args, **kwargs)


class DummyPayApi:

    # Opens an HTTP session that sends the public API key with every request.
    def __init__(self):
        self.base_url = config.SUPABASE_URL
        self.http = requests.Session()
        ca_bundle = os.getenv("REQUESTS_CA_BUNDLE")
        if ca_bundle:
            self.http.mount("https://", _CustomCAAdapter(ca_bundle))
        self.http.headers["apikey"] = config.ANON_KEY

    # Signs in and sends the user's token with every following request.
    def sign_in(self, email: str, password: str):
        r = self.http.post(f"{self.base_url}/auth/v1/token", params={"grant_type": "password"},
                           json={"email": email, "password": password}, timeout=30)
        token = self._check(r)["access_token"]
        self.http.headers["Authorization"] = f"Bearer {token}"

    # Calls a server function: POST /rest/v1/rpc/<function>.
    def rpc(self, function: str, **params):
        r = self.http.post(f"{self.base_url}/rest/v1/rpc/{function}", json=params, timeout=30)
        return self._check(r)

    # Reads rows of a table: GET /rest/v1/<table>.
    def select(self, table: str, **query):
        r = self.http.get(f"{self.base_url}/rest/v1/{table}", params=query, timeout=30)
        return self._check(r)

    # Calls an Edge Function: POST /functions/v1/<name>.
    def edge(self, name: str, body: dict):
        r = self.http.post(f"{self.base_url}/functions/v1/{name}", json=body, timeout=30)
        return self._check(r)

    # Deletes rows of a table that match the filter: DELETE /rest/v1/<table>.
    def delete(self, table: str, **query):
        r = self.http.delete(f"{self.base_url}/rest/v1/{table}", params=query, timeout=30)
        return self._check(r)

    # Returns the response body, or fails with the server's message if the server answered with an error.
    @staticmethod
    def _check(r: requests.Response):
        if not r.ok:
            raise RuntimeError(f"{r.status_code}: {r.text}")
        return r.json() if r.content else None

    # The user's wallets as {currency: balance in minor units}.
    def wallets(self) -> dict[str, int]:
        rows = self.select("wallets", select="currency,balance_minor")
        return {w["currency"]: w["balance_minor"] for w in rows}

    # The user's preferred currency (e.g. ILS).
    def preferred_currency(self) -> str:
        return self.select("profiles", select="preferred_currency")[0]["preferred_currency"]

    # The total balance the server calculates for the user.
    def wallet_summary(self) -> dict:
        return self.rpc("get_wallet_summary")[0]

    # The server's conversion of an amount (in minor units) from one currency to another.
    def preview(self, amount_minor: int, from_ccy: str, to_ccy: str) -> dict:
        return self.rpc("preview_conversion", p_amount_minor=amount_minor, p_from=from_ccy, p_to=to_ccy)[0]

    # Opens a zero-balance wallet in this currency.
    def add_wallet(self, currency: str) -> dict:
        return self.rpc("add_wallet", p_currency=currency)

    # The exchange rates from this currency, as {to_currency: rate}.
    def cross_rates(self, base: str) -> dict[str, float]:
        rows = self.select("fx_cross_rates", select="to_currency,rate", from_currency=f"eq.{base}")
        return {r["to_currency"]: r["rate"] for r in rows}

    # The user's newest transaction.
    def latest_transaction(self) -> dict | None:
        rows = self.rpc("list_my_transactions", p_limit=1)
        return rows[0] if rows else None

    # All bank accounts of the user, exactly as the server stores them.
    def bank_accounts(self) -> list[dict]:
        return self.select("bank_accounts", select="*", order="created_at.desc")

    # Adds a simulated bank account (country as an ISO code, e.g. US).
    def add_bank_account(self, holder: str, bank: str, country: str, currency: str, identifier: str) -> dict:
        return self.edge("add-bank-account", {
            "accountHolderName": holder, "bankName": bank, "country": country,
            "currency": currency, "accountIdentifier": identifier,
        })["account"]

    # All payment cards of the user, exactly as the server stores them.
    def cards(self) -> list[dict]:
        return self.select("payment_cards", select="*", order="created_at.desc")

    # Adds a simulated card (expiry as MM/YY).
    def add_card(self, name: str, number: str, expiry: str, cvv: str) -> dict:
        return self.edge("add-payment-card", {
            "cardholderName": name, "cardNumber": number, "expiry": expiry, "cvv": cvv,
        })["card"]

    # Deletes every bank account of the user with this bank name.
    def delete_bank_accounts(self, bank_name: str):
        self.delete("bank_accounts", bank_name=f"eq.{bank_name}")

    # Deletes every card of the user whose last four digits are in the list.
    def delete_cards(self, last4_values: list[str]):
        self.delete("payment_cards", last_four_digits=f"in.({','.join(last4_values)})")
