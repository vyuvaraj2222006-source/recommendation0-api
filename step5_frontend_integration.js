/**
 * STEP 5: FRONTEND INTEGRATION
 * ==============================
 * JavaScript client to integrate recommendations into your e-commerce site
 */

class RecommendationClient {
    /**
     * Initialize the recommendation client
     * @param {string} apiBaseUrl - Base URL of the recommendation API
     */
    constructor(apiBaseUrl = 'http://localhost:5000') {
        this.apiBaseUrl = apiBaseUrl;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Get cached data if available and not expired
     */
    _getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            console.log('Cache hit:', key);
            return cached.data;
        }
        return null;
    }

    /**
     * Store data in cache
     */
    _setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Make API request with error handling
     */
    async _request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Recommendation API error:', error);
            return null;
        }
    }

    /**
     * Get personalized recommendations for a user
     * @param {number} userId - User ID
     * @param {number} count - Number of recommendations
     * @param {array} excludeItems - Item IDs to exclude
     */
    async getUserRecommendations(userId, count = 10, excludeItems = []) {
        const cacheKey = `user:${userId}:${count}:${excludeItems.join(',')}`;
        
        // Check cache first
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        // Make API request
        const excludeParam = excludeItems.length > 0 ? `&exclude=${excludeItems.join(',')}` : '';
        const data = await this._request(`/api/v1/recommendations/user/${userId}?n=${count}${excludeParam}`);
        
        if (data && data.recommendations) {
            this._setCache(cacheKey, data.recommendations);
            return data.recommendations;
        }

        return [];
    }

    /**
     * Get similar items (for product detail pages)
     * @param {number} itemId - Current item ID
     * @param {number} count - Number of similar items
     */
    async getSimilarItems(itemId, count = 10) {
        const cacheKey = `similar:${itemId}:${count}`;
        
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this._request(`/api/v1/recommendations/similar/${itemId}?n=${count}`);
        
        if (data && data.similar_items) {
            this._setCache(cacheKey, data.similar_items);
            return data.similar_items;
        }

        return [];
    }

    /**
     * Get popular items (for homepage)
     * @param {number} count - Number of items
     * @param {string} category - Optional category filter
     */
    async getPopularItems(count = 10, category = null) {
        const cacheKey = `popular:${count}:${category || 'all'}`;
        
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        const categoryParam = category ? `&category=${category}` : '';
        const data = await this._request(`/api/v1/recommendations/popular?n=${count}${categoryParam}`);
        
        if (data && data.recommendations) {
            this._setCache(cacheKey, data.recommendations);
            return data.recommendations;
        }

        return [];
    }

    /**
     * Clear cache (call when user logs in/out or makes purchase)
     */
    clearCache() {
        this.cache.clear();
        console.log('Recommendation cache cleared');
    }
}


/**
 * UI RENDERING FUNCTIONS
 * =======================
 */

/**
 * Render recommendations as product cards
 * @param {array} recommendations - Array of recommendation objects
 * @param {string} containerId - ID of container element
 */
function renderRecommendations(recommendations, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    // Clear existing content
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="no-recommendations">No recommendations available</p>';
        return;
    }

    // Create product cards
    recommendations.forEach(item => {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        card.innerHTML = `
            <div class="recommendation-image">
                <img src="${item.image_url || '/placeholder.jpg'}" 
                     alt="${item.name}"
                     onerror="this.src='/placeholder.jpg'">
            </div>
            <div class="recommendation-details">
                <h3 class="recommendation-title">${item.name}</h3>
                <p class="recommendation-category">${item.category}</p>
                <div class="recommendation-footer">
                    <span class="recommendation-price">$${item.price.toFixed(2)}</span>
                    ${item.rating ? `<span class="recommendation-rating">⭐ ${item.rating.toFixed(1)}</span>` : ''}
                </div>
                <button class="recommendation-btn" onclick="addToCart(${item.item_id})">
                    Add to Cart
                </button>
            </div>
        `;
        
        // Add click tracking
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('recommendation-btn')) {
                trackRecommendationClick(item.item_id);
                window.location.href = `/product/${item.item_id}`;
            }
        });

        container.appendChild(card);
    });
}


/**
 * USAGE EXAMPLES FOR DIFFERENT PAGE TYPES
 * ========================================
 */

// Initialize the client (do this once globally)
const recoClient = new RecommendationClient('https://your-api-endpoint.com');

/**
 * Example 1: Homepage - Show popular items
 */
async function loadHomepageRecommendations() {
    const popular = await recoClient.getPopularItems(12);
    renderRecommendations(popular, 'homepage-recommendations');
}

/**
 * Example 2: Product Detail Page - Show similar items
 */
async function loadSimilarProducts(currentProductId) {
    const similar = await recoClient.getSimilarItems(currentProductId, 8);
    renderRecommendations(similar, 'similar-products');
}

/**
 * Example 3: User Dashboard - Personalized recommendations
 */
async function loadPersonalizedRecommendations(userId) {
    const recommendations = await recoClient.getUserRecommendations(userId, 10);
    renderRecommendations(recommendations, 'recommended-for-you');
}

/**
 * Example 4: Shopping Cart - Related products
 */
async function loadCartRecommendations(userId, cartItems) {
    const recommendations = await recoClient.getUserRecommendations(
        userId, 
        6, 
        cartItems // Exclude items already in cart
    );
    renderRecommendations(recommendations, 'cart-recommendations');
}

/**
 * Example 5: Category Page - Popular in category
 */
async function loadCategoryRecommendations(category) {
    const popular = await recoClient.getPopularItems(20, category);
    renderRecommendations(popular, 'category-popular');
}


/**
 * TRACKING & ANALYTICS
 * =====================
 */

/**
 * Track when user clicks a recommendation
 */
function trackRecommendationClick(itemId) {
    // Send to your analytics service
    if (typeof gtag !== 'undefined') {
        gtag('event', 'recommendation_click', {
            'item_id': itemId,
            'timestamp': new Date().toISOString()
        });
    }
    
    // Also track in your backend
    fetch('/api/track/recommendation-click', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            item_id: itemId,
            timestamp: Date.now()
        })
    });
}

/**
 * Track recommendation impressions
 */
function trackRecommendationImpressions(itemIds) {
    fetch('/api/track/recommendation-impressions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            item_ids: itemIds,
            timestamp: Date.now()
        })
    });
}


/**
 * HELPER FUNCTIONS
 * ================
 */

/**
 * Get user ID from session/cookie
 */
function getCurrentUserId() {
    // Replace with your actual user ID retrieval logic
    const userIdCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('user_id='));
    
    return userIdCookie ? parseInt(userIdCookie.split('=')[1]) : null;
}

/**
 * Add item to cart (implement your logic)
 */
function addToCart(itemId) {
    console.log('Adding item to cart:', itemId);
    // Your cart logic here
}

/**
 * Initialize recommendations on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    const userId = getCurrentUserId();
    
    // Load recommendations based on page type
    if (document.getElementById('homepage-recommendations')) {
        loadHomepageRecommendations();
    }
    
    if (document.getElementById('similar-products')) {
        const productId = parseInt(document.getElementById('current-product-id')?.value);
        if (productId) {
            loadSimilarProducts(productId);
        }
    }
    
    if (document.getElementById('recommended-for-you') && userId) {
        loadPersonalizedRecommendations(userId);
    }
});


/**
 * Clear cache on important events
 */
window.addEventListener('storage', (e) => {
    if (e.key === 'user_logged_in' || e.key === 'cart_updated') {
        recoClient.clearCache();
    }
});
