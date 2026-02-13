# backend/app/core/exceptions.py

class ShopifyError(Exception):
    """Erreur de base pour tout ce qui touche à Shopify"""
    pass

class ShopifyAuthError(ShopifyError):
    """Le token est invalide ou expiré (401)"""
    pass

class ShopifyRateLimitError(ShopifyError):
    """On a dépassé le quota d'appels (429)"""
    pass

class ShopifyTimeoutError(ShopifyError):
    """Shopify met trop de temps à répondre"""
    pass

class ShopifyNetworkError(ShopifyError):
    """Problème de connexion internet ou DNS"""
    pass

class ShopifyAPIError(ShopifyError):
    """Erreur générique renvoyée par l'API (4xx, 5xx)"""
    pass