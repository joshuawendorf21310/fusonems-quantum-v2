import os

import stripe


def env_int(key, default):
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return int(default)


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    raise SystemExit("STRIPE_SECRET_KEY is required.")

BRAND = os.getenv("BILLING_BRAND_NAME", "FusonEMS Quantum")

PRODUCTS = [
    ("FusionEMS Quantum — Agency Subscription", "QUANTUM_AGENCY_CORE_MONTHLY"),
    ("FusionCare — Patient Payments", "FUSIONCARE_PATIENT"),
    ("Medical Transport — Patient Self-Pay", "MEDICAL_TRANSPORT_PATIENT"),
]

ADD_ONS = [
    ("CAD Module Add-on", "STRIPE_PRICE_ID_CAD", "CAD"),
    ("ePCR Module Add-on", "STRIPE_PRICE_ID_EPCR", "EPCR"),
    ("Billing Ops Add-on", "STRIPE_PRICE_ID_BILLING", "BILLING"),
    ("Comms Add-on", "STRIPE_PRICE_ID_COMMS", "COMMS"),
    ("Scheduling Add-on", "STRIPE_PRICE_ID_SCHEDULING", "SCHEDULING"),
    ("Fire Module Add-on", "STRIPE_PRICE_ID_FIRE", "FIRE"),
    ("HEMS Module Add-on", "STRIPE_PRICE_ID_HEMS", "HEMS"),
    ("Inventory/Narcotics Add-on", "STRIPE_PRICE_ID_INVENTORY", "INVENTORY"),
    ("Training/QA/Legal Add-on", "STRIPE_PRICE_ID_TRAINING", "TRAINING"),
]


def get_or_create_product(name):
    products = stripe.Product.list(limit=100)
    for product in products.auto_paging_iter():
        if product["name"] == name:
            return product
    return stripe.Product.create(name=name, metadata={"platform": BRAND})


def get_or_create_price(product_id, nickname, amount, interval="month"):
    prices = stripe.Price.list(product=product_id, limit=100)
    for price in prices.auto_paging_iter():
        if price.get("nickname") == nickname:
            return price
    return stripe.Price.create(
        product=product_id,
        unit_amount=amount,
        currency="usd",
        recurring={"interval": interval},
        nickname=nickname,
    )


def main():
    core_product = get_or_create_product("FusionEMS Quantum — Agency Subscription")
    core_amount = env_int("STRIPE_PRICE_AMOUNT_CORE_MONTHLY", 250000)
    core_price = get_or_create_price(core_product["id"], "QUANTUM_AGENCY_CORE_MONTHLY", core_amount)
    print("CORE_SUBSCRIPTION_PRICE_ID", core_price["id"])

    for name, env_key, module in ADD_ONS:
        product = get_or_create_product(name)
        amount = env_int(f"STRIPE_PRICE_AMOUNT_{module}", 25000)
        price = get_or_create_price(product["id"], name, amount)
        print(f"{env_key}={price['id']}")

    get_or_create_product("FusionCare — Patient Payments")
    get_or_create_product("Medical Transport — Patient Self-Pay")


if __name__ == "__main__":
    main()
