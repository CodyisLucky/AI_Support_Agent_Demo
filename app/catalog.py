ITEMS: list[dict] = [
    {
        "id": "cream-cleanser",
        "name": "Cloud Cream Cleanser",
        "kind": "skincare",
        "price_cents": 2400,
        "summary": "A gentle cream cleanser for dry or sensitive skin.",
    },
    {
        "id": "hydrating-serum",
        "name": "Dew Hydrating Serum",
        "kind": "skincare",
        "price_cents": 4200,
        "summary": "A light serum with glycerin for skin that feels tight.",
    },
    {
        "id": "daily-moisturizer",
        "name": "Soft Daily Moisturizer",
        "kind": "skincare",
        "price_cents": 3200,
        "summary": "A daytime moisturizer with a soft, non-greasy finish.",
    },
    {
        "id": "mineral-sunscreen",
        "name": "Sheer Mineral SPF",
        "kind": "skincare",
        "price_cents": 2800,
        "summary": "A mineral face sunscreen, SPF 30, with a sheer tint.",
    },
    {
        "id": "gel-cleanser",
        "name": "Fresh Gel Cleanser",
        "kind": "skincare",
        "price_cents": 2200,
        "summary": "A clear gel cleanser for oily or combination skin.",
    },
    {
        "id": "calming-toner",
        "name": "Calming Toner",
        "kind": "skincare",
        "price_cents": 2600,
        "summary": "An alcohol-free toner that leaves skin soft, not tight.",
    },
    {
        "id": "eye-cream",
        "name": "Quiet Eye Cream",
        "kind": "skincare",
        "price_cents": 3800,
        "summary": "A small-jar cream for the eye area, used morning or night.",
    },
    {
        "id": "night-cream",
        "name": "Rest Night Cream",
        "kind": "skincare",
        "price_cents": 4600,
        "summary": "A richer cream to use after cleansing in the evening.",
    },
    {
        "id": "clay-mask",
        "name": "Clear Clay Mask",
        "kind": "skincare",
        "price_cents": 3000,
        "summary": "A weekly clay mask that rinses off clean.",
    },
    {
        "id": "face-oil",
        "name": "Glow Face Oil",
        "kind": "skincare",
        "price_cents": 4400,
        "summary": "A few drops of face oil to press on after moisturizer.",
    },
    {
        "id": "face-mist",
        "name": "Dew Face Mist",
        "kind": "skincare",
        "price_cents": 1800,
        "summary": "A light mist to refresh makeup or bare skin.",
    },
    {
        "id": "lip-treatment",
        "name": "Repair Lip Treatment",
        "kind": "skincare",
        "price_cents": 1400,
        "summary": "A balm for dry lips, worn alone or under color.",
    },
    {
        "id": "skin-tint",
        "name": "Veil Skin Tint",
        "kind": "makeup",
        "price_cents": 3600,
        "summary": "Light coverage that evens skin tone and lets skin show through.",
    },
    {
        "id": "cream-blush",
        "name": "Petal Cream Blush",
        "kind": "makeup",
        "price_cents": 2200,
        "summary": "A buildable cream blush you can tap on with fingers.",
    },
    {
        "id": "mascara",
        "name": "Lift Mascara",
        "kind": "makeup",
        "price_cents": 2000,
        "summary": "A defining mascara that washes off with cleanser.",
    },
    {
        "id": "lip-color",
        "name": "Satin Lip Color",
        "kind": "makeup",
        "price_cents": 1800,
        "summary": "A comfortable satin lip color in a warm rose shade.",
    },
    {
        "id": "concealer",
        "name": "Soft Concealer",
        "kind": "makeup",
        "price_cents": 2400,
        "summary": "A creamy concealer for spots and under the eyes.",
    },
    {
        "id": "brow-pencil",
        "name": "Brow Pencil",
        "kind": "makeup",
        "price_cents": 1600,
        "summary": "A slim pencil to fill sparse brows with light strokes.",
    },
    {
        "id": "cream-shadow",
        "name": "Cream Eyeshadow",
        "kind": "makeup",
        "price_cents": 2000,
        "summary": "A blendable cream shadow in a soft taupe.",
    },
    {
        "id": "setting-powder",
        "name": "Soft Setting Powder",
        "kind": "makeup",
        "price_cents": 2800,
        "summary": "A finely milled powder to set tint or concealer.",
    },
    {
        "id": "highlighter",
        "name": "Warm Highlighter",
        "kind": "makeup",
        "price_cents": 2200,
        "summary": "A cream highlighter for cheekbones, tapped on with a finger.",
        "stock": 0,
    },
    {
        "id": "lip-liner",
        "name": "Lip Liner",
        "kind": "makeup",
        "price_cents": 1400,
        "summary": "A rose liner that matches Satin Lip Color.",
    },
    {
        "id": "setting-spray",
        "name": "Stay Setting Spray",
        "kind": "makeup",
        "price_cents": 2600,
        "summary": "A light spray to help makeup last through the day.",
    },
    {
        "id": "product-consult",
        "name": "Product consultation",
        "kind": "service",
        "price_cents": 4000,
        "summary": "Thirty minutes in the shop to choose skincare and makeup for your routine.",
    },
    {
        "id": "makeup-service",
        "name": "Professional makeup",
        "kind": "service",
        "price_cents": 8500,
        "summary": "A full makeup application by a makeup artist for an event or appointment.",
    },
]

_BY_ID = {item["id"]: item for item in ITEMS}

SECTIONS = (
    ("skincare", "Skincare"),
    ("makeup", "Makeup"),
    ("service", "Services"),
)


def get_item(item_id: str) -> dict | None:
    return _BY_ID.get(item_id)


def in_stock(item: dict) -> bool:
    stock = item.get("stock")
    return stock is None or stock > 0


def format_price(cents: int) -> str:
    return f"${cents / 100:.2f}"


def sections() -> list[dict]:
    grouped = []
    for kind, title in SECTIONS:
        grouped.append(
            {
                "title": title,
                "entries": [item for item in ITEMS if item["kind"] == kind],
            }
        )
    return grouped
