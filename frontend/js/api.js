/**
 * C2T MOBILES - API Client Module
 */

const API_BASE_URL = '/api';

const API = {
  async getSettings() {
    try {
      const res = await fetch(`${API_BASE_URL}/settings`);
      return await res.json();
    } catch (err) {
      console.error("Error fetching settings:", err);
      return { owner_whatsapp: "919994645492", owner_name: "C2T MOBILES" };
    }
  },

  async getBrands() {
    try {
      const res = await fetch(`${API_BASE_URL}/brands`);
      return await res.json();
    } catch (err) {
      console.error("Error fetching brands:", err);
      return { brands: [], count: 0 };
    }
  },

  async getBrandDetail(identifier) {
    const res = await fetch(`${API_BASE_URL}/brands/${identifier}`);
    if (!res.ok) throw new Error("Brand not found");
    return await res.json();
  },

  async getProducts(filters = {}) {
    const query = new URLSearchParams(filters).toString();
    const res = await fetch(`${API_BASE_URL}/products?${query}`);
    if (!res.ok) throw new Error("Failed to fetch products");
    return await res.json();
  },

  async searchProducts(query) {
    const res = await fetch(`${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error("Search request failed");
    return await res.json();
  },

  async getProductDetail(identifier) {
    const res = await fetch(`${API_BASE_URL}/products/${identifier}`);
    if (!res.ok) throw new Error("Product not found");
    return await res.json();
  },

  async recordEnquiry(productId) {
    try {
      await fetch(`${API_BASE_URL}/enquiries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
      });
    } catch (err) {
      console.warn("Analytics recording issue:", err);
    }
  },

  /* User Authentication Endpoints */
  async userRegister(userData) {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    return data;
  },

  async userLogin(identifier, password) {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    return data;
  },

  async userLogout() {
    await fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST' });
  },

  async googleAuth(payload) {
    const res = await fetch(`${API_BASE_URL}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Google authentication failed");
    return data;
  },

  async appleAuth(payload) {
    const res = await fetch(`${API_BASE_URL}/auth/apple`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Apple authentication failed");
    return data;
  },

  async getUserMe() {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`);
      return await res.json();
    } catch (err) {
      return { authenticated: false };
    }
  },

  async getUserProfile() {
    const res = await fetch(`${API_BASE_URL}/auth/user/profile`);
    if (!res.ok) throw new Error("Failed to fetch profile");
    return await res.json();
  },

  async updateUserProfile(profileData) {
    const res = await fetch(`${API_BASE_URL}/auth/user/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Profile update failed");
    return data;
  },

  /* Admin Endpoints */
  async adminLogin(username, password) {
    const res = await fetch(`${API_BASE_URL}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    return data;
  },

  async adminLogout() {
    await fetch(`${API_BASE_URL}/admin/logout`, { method: 'POST' });
  },

  async checkAdminAuth() {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/check-auth`);
      return await res.json();
    } catch (err) {
      return { authenticated: false };
    }
  },

  async getAdminDashboard() {
    const res = await fetch(`${API_BASE_URL}/admin/dashboard`);
    if (!res.ok) throw new Error("Unauthorized or server error");
    return await res.json();
  },

  async getAdminBrands() {
    const res = await fetch(`${API_BASE_URL}/admin/brands`);
    if (!res.ok) throw new Error("Failed to load brands");
    return await res.json();
  },

  async createBrand(brandData) {
    const res = await fetch(`${API_BASE_URL}/admin/brands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(brandData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Creation failed");
    return data;
  },

  async updateBrand(id, brandData) {
    const res = await fetch(`${API_BASE_URL}/admin/brands/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(brandData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Update failed");
    return data;
  },

  async deleteBrand(id) {
    const res = await fetch(`${API_BASE_URL}/admin/brands/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Delete failed");
    return data;
  },

  async getAdminProducts(filters = {}) {
    const query = new URLSearchParams(filters).toString();
    const res = await fetch(`${API_BASE_URL}/admin/products?${query}`);
    if (!res.ok) throw new Error("Failed to load inventory");
    return await res.json();
  },

  async createProduct(formData) {
    const res = await fetch(`${API_BASE_URL}/admin/products`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Creation failed");
    return data;
  },

  async updateProduct(id, formData) {
    const res = await fetch(`${API_BASE_URL}/admin/products/${id}`, {
      method: 'PUT',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Update failed");
    return data;
  },

  async updateProductStatus(id, status) {
    const res = await fetch(`${API_BASE_URL}/admin/products/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Status update failed");
    return data;
  },

  async deleteProduct(id) {
    const res = await fetch(`${API_BASE_URL}/admin/products/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Delete failed");
    return data;
  },

  async deleteImage(imageId) {
    const res = await fetch(`${API_BASE_URL}/admin/images/${imageId}`, { method: 'DELETE' });
    return await res.json();
  },

  async updateSettings(settingsData) {
    const res = await fetch(`${API_BASE_URL}/admin/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settingsData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Settings update failed");
    return data;
  }
};

// Global exports: Expose both uppercase API and lowercase api to window scope
if (typeof window !== 'undefined') {
  window.API = API;
  window.api = API;
}

