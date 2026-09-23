/**
 * C2T MOBILES - Catalog & Multi-Filter Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const gridContainer = document.getElementById('productGrid');
  const searchInput = document.getElementById('searchInput');
  const sortSelect = document.getElementById('sortSelect');
  const filterForm = document.getElementById('filterForm');
  const resultCount = document.getElementById('resultCount');
  const clearFiltersBtn = document.getElementById('clearFilters');

  if (!gridContainer) return;

  // Check URL params for initial filters (e.g. ?brand=Apple or ?search=iPhone)
  const urlParams = new URLSearchParams(window.location.search);
  let currentFilters = {
    brand: urlParams.get('brand') || '',
    search: urlParams.get('search') || '',
    condition: urlParams.get('condition') || '',
    storage: urlParams.get('storage') || '',
    sort: urlParams.get('sort') || 'newest',
    status: urlParams.get('status') || ''
  };

  if (searchInput && currentFilters.search) {
    searchInput.value = currentFilters.search;
  }
  if (sortSelect && currentFilters.sort) {
    sortSelect.value = currentFilters.sort;
  }

  // Fetch and render products
  async function loadProducts() {
    gridContainer.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <div style="font-size: 1.25rem; font-weight: 700; color: #64748b;">Loading stock...</div>
      </div>
    `;

    try {
      const data = await API.getProducts(currentFilters);
      renderProductGrid(data.products);
      if (resultCount) {
        resultCount.textContent = `${data.count} ${data.count === 1 ? 'Mobile' : 'Mobiles'} Found`;
      }
    } catch (err) {
      gridContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1/-1;">
          <div class="empty-icon">⚠️</div>
          <h3>Unable to load stock</h3>
          <p>Please check your connection and try refreshing.</p>
          <button onclick="location.reload()" class="btn btn-primary btn-sm">Retry</button>
        </div>
      `;
    }
  }

  function renderProductGrid(products) {
    if (!products || products.length === 0) {
      gridContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1/-1;">
          <div class="empty-icon">📱</div>
          <h3>No Mobiles Found</h3>
          <p>We couldn't find any mobiles matching your exact search or filter options.</p>
          <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
            <button id="resetFiltersInner" class="btn btn-secondary btn-sm">Clear Filters</button>
            <a href="https://wa.me/919994645492?text=Hi%20C2T%20MOBILES%2C%20I%20would%20like%20to%20know%20about%20upcoming%20mobile%20stock." target="_blank" class="btn btn-whatsapp btn-sm">Enquire Upcoming Stock on WA</a>
          </div>
        </div>
      `;
      const resetBtn = document.getElementById('resetFiltersInner');
      if (resetBtn) resetBtn.addEventListener('click', resetAllFilters);
      return;
    }

    gridContainer.innerHTML = products.map(product => {
      const isSold = product.status === 'SOLD';
      const badgeText = isSold ? 'SOLD OUT' : (product.badge || (product.featured ? 'FEATURED' : ''));
      const badgeClass = isSold ? 'badge-sold' : (product.badge === 'HOT DEAL' ? 'badge-hot' : 'badge-featured');
      
      const priceFormatted = formatINR(product.price);
      const mrpFormatted = product.mrp_formatted ? formatINR(product.mrp) : '';
      const discountTag = product.discount_percent ? `<span class="discount-badge">${product.discount_percent}% OFF</span>` : '';

      return `
        <div class="product-card">
          ${badgeText ? `<span class="card-badge ${badgeClass}">${badgeText}</span>` : ''}
          
          <a href="product.html?id=${product.slug || product.id}" class="card-image-wrap">
            <img src="${product.primary_image}" alt="${product.brand} ${product.model}" loading="lazy">
          </a>
          
          <div class="card-body">
            <div class="card-brand">${product.brand}</div>
            <h3 class="card-title">
              <a href="product.html?id=${product.slug || product.id}">${product.model}</a>
            </h3>
            
            <div class="card-specs-tags">
              <span class="spec-chip">${product.storage}</span>
              ${product.ram ? `<span class="spec-chip">${product.ram} RAM</span>` : ''}
              <span class="spec-chip highlight">⭐ ${product.condition}</span>
              ${product.battery_health ? `<span class="spec-chip">🔋 ${product.battery_health}</span>` : ''}
            </div>
            
            <div class="card-pricing">
              <span class="current-price">${priceFormatted}</span>
              ${mrpFormatted ? `<span class="mrp-price">${mrpFormatted}</span>` : ''}
              ${discountTag}
            </div>
            
            <div class="card-actions">
              <a href="product.html?id=${product.slug || product.id}" class="btn btn-secondary btn-sm">View Details</a>
              ${isSold 
                ? `<button class="btn btn-secondary btn-sm" disabled style="opacity: 0.6; cursor: not-allowed;">Sold Out</button>`
                : `<button onclick="handleWaBuyClick(event, ${product.id})" class="btn btn-whatsapp btn-sm">Buy on WA</button>`
              }
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Handle WhatsApp Click from product card
  window.handleWaBuyClick = async (event, productId) => {
    event.preventDefault();
    event.stopPropagation();

    try {
      // 1. Record enquiry API analytics
      await API.recordEnquiry(productId);

      // 2. Fetch product detail to get exact WhatsApp message & link
      const product = await API.getProductDetail(productId);
      if (product && product.whatsapp_url) {
        window.open(product.whatsapp_url, '_blank');
      } else {
        alert("Redirecting to WhatsApp...");
      }
    } catch (e) {
      console.error("Error launching WhatsApp:", e);
    }
  };

  // Search input handler
  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        currentFilters.search = e.target.value.trim();
        loadProducts();
      }, 300);
    });
  }

  // Sort selector handler
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      currentFilters.sort = e.target.value;
      loadProducts();
    });
  }

  // Filter sidebar handlers
  if (filterForm) {
    filterForm.addEventListener('change', () => {
      const formData = new FormData(filterForm);
      currentFilters.brand = formData.getAll('brand').join(',');
      currentFilters.condition = formData.getAll('condition').join(',');
      currentFilters.storage = formData.getAll('storage').join(',');
      
      const priceRange = formData.get('priceRange');
      if (priceRange) {
        const [min, max] = priceRange.split('-');
        currentFilters.min_price = min || '';
        currentFilters.max_price = max || '';
      } else {
        delete currentFilters.min_price;
        delete currentFilters.max_price;
      }

      loadProducts();
    });
  }

  function resetAllFilters() {
    currentFilters = { sort: 'newest' };
    if (searchInput) searchInput.value = '';
    if (sortSelect) sortSelect.value = 'newest';
    if (filterForm) filterForm.reset();
    loadProducts();
  }

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', resetAllFilters);
  }

  // Initial load
  loadProducts();
});
