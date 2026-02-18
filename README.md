# 🛍️ Askit — AI Customer Support for Shopify

**Askit** est une solution SaaS de support client autonome pour boutiques Shopify.  
Contrairement aux chatbots traditionnels basés sur des arbres de décision, Askit repose sur une **architecture hybride intelligente** combinant :

- **IA générative (RAG)** pour la base de connaissances.
- **Intégration API temps réel** pour les données transactionnelles Shopify.

L'objectif : fournir des réponses naturelles, fiables et sécurisées sans intervention humaine.

---

## 🔥 Fonctionnalités clés

### 1. 🧠 Intelligence hybride & contextuelle
Le système détecte automatiquement l’intention de l’utilisateur et route la requête vers le moteur approprié.

| Moteur | Usage | Fonctionnement |
| :--- | :--- | :--- |
| **RAG (Retrieval-Augmented Generation)** | Questions générales | Interroge la base vectorielle contenant la documentation de la boutique |
| **Transactionnel (Shopify API)** | Informations spécifiques | Interroge l’API Shopify en temps réel |

**Exemples :**
- *"Quels sont les délais de livraison ?"* → **RAG**
- *"Où est ma commande #1001 ?"* → **Shopify API**

---

### 2. 🛡️ Protocole de sécurité — *Smart Challenge* (Anti-IDOR)
Pour protéger les données personnelles (PII) sans friction utilisateur :

1. Le bot détecte un numéro de commande (ex: `#1001`).
2. Il récupère les données en arrière-plan mais **n'affiche rien immédiatement**.
3. Il déclenche un défi : demande l'**email associé à la commande**.
4. Les données ne sont révélées **qu'après validation Email ↔ OrderID**.

**Données protégées :** Adresse, statut précis, lien de suivi logistique.

---

### 3. 💬 Widget & Landing Page intégrée

**Widget embeddable**
- Injectée via une simple balise script.

**Showcase Mode**
Le widget inclut sa propre landing page de démonstration pour tester le bot hors environnement Shopify.

---

### 4. 📊 Dashboard d'administration
Interface complète pour le marchand :
- **Monitoring :** Visualisation des conversations en temps réel.
- **Knowledge Base :** Gestion des sources (scraping d'URL + texte brut).
- **Configuration :** Gestion des clés API Shopify et paramétrage du widget.

---

## 🏗️ Architecture technique (Monorepo)
Le projet est divisé en 3 micro-services :

### 1. Backend (`/backend`) — 🧠 Le cerveau
API REST orchestrant la logique métier et l’IA.
- **Framework :** Python (FastAPI)
- **IA & Orchestration :** LangChain + OpenAI (GPT-3.5/4)
- **Base de données :** Supabase (PostgreSQL + pgvector)
- **Authentification :** JWT + Supabase Auth
- **Sécurité :** Rate limiting, CORS strict, validation des inputs.

### 2. Dashboard Admin (`/frontend-dashboard`)
Interface SaaS pour le commerçant.
- **Framework :** React 18 (Vite)
- **UI :** Tailwind CSS + Shadcn/UI
- **State Management :** React Hooks + Context API
- **Analytics :** Recharts

### 3. Widget (`/widget-embed`) — 💬 Le client
Composant injecté chez le visiteur.
- **Framework :** Preact (3kb)
- **Build :** Vite (Library Mode)
- **Styling :** Tailwind CSS (préfixé pour éviter les conflits)
- **Optimisation :** Bundle "Single File" avec CSS et icônes inline.

---

## ⚡ Flux de données — Exemple : *"Où est la commande #1001 ?"*

1. **Widget** : L’utilisateur envoie la requête.
2. **Analyse Backend** : Le regex détecte `#\d{4}`. Le router active le `ShopifyService`.
3. **Appel API Shopify** : Récupération des données de la commande.
4. **Vérification Sécurité** : Email absent du prompt → Challenge déclenché.
5. **Réponse Intermédiaire** : *"Veuillez confirmer votre email pour voir le statut."*
6. **Validation** : L’utilisateur fournit l’email. Le backend vérifie la correspondance.
7. **Résolution LLM** : Le LLM convertit le JSON Shopify en langage naturel.
8. **Réponse finale** : *"Votre commande a été expédiée et arrivera le 14 mars. Voici votre lien de suivi..."*

---

## 🎯 Objectif
Remplacer le support client de niveau 1 (FAQ + suivi de colis) par une solution automatisée, naturelle et sécurisée, réduisant drastiquement :
- Les tickets support.
- Le temps de réponse.
- Les coûts opérationnels.
