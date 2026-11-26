
import uuid

def send_funds(api, email, amount=100):
    recipient = api.rpc("lookup_recipient", p_email=email)

    wallets = api.wallets()
    currency = next(
        c for c, balance in wallets.items()
        if balance >= amount
    )

    quote = api.rpc(
        "create_transfer_quote",
        p_recipient_id=recipient[0]["user_id"],
        p_sending_currency=currency,
        p_amount_minor=amount,
        p_input_side="send"
    )

  
    result = api.rpc(
        "execute_transfer",
        p_quote_id=quote["quote_id"],
        p_idempotency_key=str(uuid.uuid4())
    )

    return quote, result
