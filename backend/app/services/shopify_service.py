import httpx
import asyncio
import logging
from typing import Optional, Dict, TypedDict
from asyncio import Semaphore


logger = logging.getLogger("uvicorn.error")

class OrderStatus(TypedDict):
    """Structure standardisée pour une commande"""
    number: str
    status: str
    status_emoji: str
    financial_status: str
    items: list[dict]
    tracking_url: Optional[str]
    created_at: str
    total_price: str
    currency: str
    email: str

class ShopifyService:
    DEFAULT_API_VERSION = "2025-01"

    def __init__(self, shop_url: str, access_token: str, api_version: str = None):
        self.shop_url = shop_url.replace("https://", "").replace("http://", "").strip("/")
        version = api_version or self.DEFAULT_API_VERSION
        self.base_url = f"https://{self.shop_url}/admin/api/{version}"
        
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        self.semaphore = Semaphore(2)

    async def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Exécute la requête de manière sécurisée"""
        async with self.semaphore:
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    logger.info(f"🌍 SHOPIFY API: {method} {endpoint} | Params: {params}")
                    
                    response = await client.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        params=params
                    )
                    
                    if response.status_code == 401:
                        logger.error("🔒 Token Shopify invalide")
                        return None
                    
                    if response.status_code != 200:
                        logger.error(f"❌ Erreur API {response.status_code}: {response.text}")
                        return None

                    return response.json()

                except Exception as e:
                    logger.error(f"💥 Erreur connexion Shopify: {e}")
                    return None

    async def get_order_status_data(self, order_identifier: str) -> Optional[OrderStatus]:
        """
        Récupère et nettoie les données de la commande.
        Utilise la logique validée : '#1001'
        """
        clean_id = ''.join(filter(str.isdigit, order_identifier))
        
        search_name = f"#{clean_id}"

        data = await self._make_request("GET", "/orders.json", params={"name": search_name, "status": "any", "limit": 1})
        
        if not data or "orders" not in data or not data["orders"]:
            logger.warning(f"⚠️ Aucune commande trouvée pour : {search_name}")
            return None

        order = data["orders"][0]
        logger.info(f"✅ Commande trouvée : {order['name']} (ID: {order['id']})")

        fulfillment = order.get("fulfillment_status")
        if fulfillment == "fulfilled":
            status, emoji = "Expédiée", "✅"
        elif fulfillment == "partial":
            status, emoji = "Partiellement expédiée", "📦"
        elif fulfillment == "shipped":
             status, emoji = "En transit", "🚚"
        else:
            status, emoji = "En préparation", "⏳"

        tracking_url = order.get("order_status_url", "Non disponible")
        if order.get("fulfillments"):
            for f in order["fulfillments"]:
                if f.get("tracking_url"):
                    tracking_url = f["tracking_url"]
                    break

        items = [
            {
                "name": item["name"],
                "quantity": item["quantity"],
                "price": item["price"]
            }
            for item in order["line_items"]
        ]

        return OrderStatus(
            number=order["name"],
            email=order.get("email", "").lower(),
            status=status,
            status_emoji=emoji,
            financial_status=order.get("financial_status", "unknown"),
            items=items,
            tracking_url=tracking_url,
            created_at=order["created_at"],
            total_price=order["current_total_price"],
            currency=order["currency"]
        )

    def format_for_bot(self, status: OrderStatus, question: str) -> str:
        """Génère la réponse texte pour le client"""
        q_lower = question.lower()

        # Cas 1: Demande de contenu ("C'est quoi dedans ?")
        if any(w in q_lower for w in ["contenu", "quoi", "article", "dedans"]):
            items_list = "\n".join([f"• {i['quantity']}x {i['name']}" for i in status['items']])
            return f"📦 **Commande {status['number']}** contient :\n{items_list}"

        track_link = status['tracking_url']
        if track_link != "Non disponible":
            track_link = f"[Cliquez ici pour suivre]({track_link})"

        return (
            f"📦 **Commande {status['number']}**\n"
            f"Statut : {status['status_emoji']} **{status['status']}**\n"
            f"Total : {status['total_price']} {status['currency']}\n"
            f"🔗 Suivi : {track_link}"
        )