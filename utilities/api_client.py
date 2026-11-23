"""Thin client for the DummyPay REST API (Supabase), based on the official API docs.

Every request carries the public `apikey` header; after sign-in it also carries the
user's Bearer token, so the client can do exactly what that user can do in the app.
"""
import os
import ssl

import requests
from requests.adapters import HTTPAdapter

from utilities import config


class _CustomCAAdapter(HTTPAdapter):
    """Trusts a local CA bundle (e.g. a filtering proxy's root certificate).

    Python 3.13+ enables VERIFY_X509_STRICT by default, which rejects some proxy root
    certificates ("CA cert does not include key usage extension"). Certificates are
    still fully verified against the bundle; only that extra strictness is relaxed.
    """

    def __init__(self, ca_bundle: str, **kwargs):
        self._context = ssl.create_default_context(cafile=ca_bundle)
        self._context.verify_flags &= ~ssl.VERIFY_X509_STRICT
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._context
        return super().init_poolmanager(*args, **kwargs)


class ApiError(Exception):
    """Raised for any non-2xx response. `code` is the DummyPay error code (e.g. WALLET_EXISTS)."""

    def __init__(self, status: int, body):
        self.status = status
        self.body = body
        msg = ""
        if isinstance(body, dict):
            # PostgREST -> "message", Edge Functions -> "error", Auth -> "error_code" / "msg"
            msg = body.get("message") or body.get("error") or body.get("error_code") or body.get("msg") or ""
        self.code = str(msg).split(":", 1)[0].strip()
        super().__init__(f"{status} {self.code}: {body}")


class DummyPayApi:
    def __init__(self, base_url: str = config.SUPABASE_URL, anon_key: str = config.ANON_KEY):
        self.base_url = base_url.rstrip("/")
        self.http = requests.Session()
        ca_bundle = os.getenv("REQUESTS_CA_BUNDLE")  # set only on machines behind a filtering proxy
        if ca_bundle and hasattr(ssl, "VERIFY_X509_STRICT"):
            self.http.mount("https://", _CustomCAAdapter(ca_bundle))
        self.http.headers["apikey"] = anon_key
        self.user_id = None
        self.email = None

    # ---- auth ----------------------------------------------------------------
    def sign_in(self, email: str, password: str) -> dict:
        r = self.http.post(f"{self.base_url}/auth/v1/token", params={"grant_type": "password"},
                           json={"email": email, "password": password}, timeout=30)
        return self._use_session(self._check(r))

    def _use_session(self, session: dict) -> dict:
        self.http.headers["Authorization"] = f"Bearer {session['access_token']}"
        self.user_id = session["user"]["id"]
        self.email = session["user"]["email"]
        return session

    # ---- generic calls -------------------------------------------------------
    def rpc(self, function: str, **params):
        """POST /rest/v1/rpc/<function> with named parameters."""
        r = self.http.post(f"{self.base_url}/rest/v1/rpc/{function}", json=params, timeout=30)
        return self._check(r)

    def select(self, table: str, **query):
        """GET /rest/v1/<table> with PostgREST query parameters."""
        r = self.http.get(f"{self.base_url}/rest/v1/{table}", params=query, timeout=30)
        return self._check(r)

    def edge(self, name: str, body: dict):
        """POST /functions/v1/<name> (Edge Function, e.g. add-bank-account)."""
        r = self.http.post(f"{self.base_url}/functions/v1/{name}", json=body, timeout=30)
        return self._check(r)

    def raw(self, method: str, path: str, **kwargs) -> requests.Response:
        """Unchecked request, for tests that assert on the status code themselves."""
        return self.http.request(method, f"{self.base_url}{path}", timeout=30, **kwargs)

    @staticmethod
    def _check(r: requests.Response):
        body = r.json() if r.content else None
        if not r.ok:
            raise ApiError(r.status_code, body)
        return body

    # ---- domain helpers ------------------------------------------------------
    def wallets(self) -> dict[str, int]:
        """{currency: balance_minor} for the signed-in user."""
        rows = self.select("wallets", select="currency,balance_minor")
        return {w["currency"]: w["balance_minor"] for w in rows}

    def profile(self) -> dict:
        return self.select("profiles", select="id,email,display_name,preferred_currency")[0]

    def wallet_summary(self) -> dict:
        return self.rpc("get_wallet_summary")[0]

    def preview(self, amount_minor: int, from_ccy: str, to_ccy: str) -> dict:
        return self.rpc("preview_conversion", p_amount_minor=amount_minor, p_from=from_ccy, p_to=to_ccy)[0]

    def add_wallet(self, currency: str) -> dict:
        """Test-data setup: open a zero-balance wallet in this currency."""
        return self.rpc("add_wallet", p_currency=currency)

    def cross_rates(self, base: str) -> dict[str, float]:
        """{to_currency: rate} for every pair that starts at `base`."""
        rows = self.select("fx_cross_rates", select="to_currency,rate", from_currency=f"eq.{base}")
        return {r["to_currency"]: r["rate"] for r in rows}

    def latest_transaction(self) -> dict | None:
        """The newest transaction of this user (sent, received or welcome grant)."""
        rows = self.rpc("list_my_transactions", p_limit=1)
        return rows[0] if rows else None

    def bank_accounts(self) -> list[dict]:
        """All bank accounts of this user, exactly as the server stores them."""
        return self.select("bank_accounts", select="*", order="created_at.desc")

    def add_bank_account(self, holder: str, bank: str, country: str, currency: str, identifier: str) -> dict:
        """Test-data setup: add a simulated bank account (country = ISO code, e.g. GB)."""
        return self.edge("add-bank-account", {
            "accountHolderName": holder, "bankName": bank, "country": country,
            "currency": currency, "accountIdentifier": identifier,
        })["account"]

    def cards(self) -> list[dict]:
        """All payment cards of this user, exactly as the server stores them."""
        return self.select("payment_cards", select="*", order="created_at.desc")

    def add_card(self, name: str, number: str, expiry: str, cvv: str) -> dict:
        """Test-data setup: add a simulated card (expiry as MM/YY)."""
        return self.edge("add-payment-card", {
            "cardholderName": name, "cardNumber": number, "expiry": expiry, "cvv": cvv,
        })["card"]

    # ---- test-data cleanup ---------------------------------------------------
    def delete_bank_accounts(self, bank_name: str):
        """Delete every bank account of this user with this bank name."""
        r = self.raw("DELETE", "/rest/v1/bank_accounts", params={"bank_name": f"eq.{bank_name}"})
        assert r.status_code in (200, 204), r.text

    def delete_cards(self, last4_values: list[str]):
        """Delete every card of this user whose last four digits are listed."""
        r = self.raw("DELETE", "/rest/v1/payment_cards",
                     params={"last_four_digits": f"in.({','.join(last4_values)})"})
        assert r.status_code in (200, 204), r.text

