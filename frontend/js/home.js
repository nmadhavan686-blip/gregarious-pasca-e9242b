/**
 * C2T MOBILES - Homepage Renderer with Brand Categories
 */

document.addEventListener('DOMContentLoaded', async () => {
  const brandGrid = document.getElementById('brandGrid');
  const latestGrid = document.getElementById('latestProductsGrid');
  const featuredGrid = document.getElementById('featuredProductsGrid');
  const browseGrid = document.getElementById('browseAllProductsGrid');
  const searchInput = document.getElementById('homeSearchInput');
  const sortSelect = document.getElementById('homeSortSelect');

  // 1. Render Brand Categories ("Shop by Brand") with Vector Logo Assets
  if (brandGrid) {
    try {
      const brandData = await API.getBrands();
      const brands = brandData.brands || [];

      if (brands.length === 0) {
        brandGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:#64748b;">Loading brands...</div>`;
      } else {
        brandGrid.innerHTML = brands.map(b => {
          const logoSrc = b.logo_icon && b.logo_icon.startsWith('/') ? b.logo_icon : `/assets/images/brands/${b.slug}.svg`;
          return `
            <a href="/brand/${b.slug}" class="brand-card">
              <div class="brand-logo-wrap">
                <img src="${logoSrc}" alt="${b.name}" loading="lazy" onerror="this.onerror=null; this.src='/assets/images/brands/other.svg';">
              </div>
              <span class="brand-card-name">${b.name}</span>
              <span class="brand-card-count">${b.product_count || 0} ${b.product_count === 1 ? 'Mobile' : 'Mobiles'}</span>
            </a>
          `;
        }).join('');
      }
    } catch (e) {
      console.error("Error loading brands:", e);
    }
  }

  // Helper to render product cards into a target container
  function renderCards(container, products) {
    if (!container) return;
    if (!products || products.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1/-1; padding: 2rem;">
          <div class="empty-icon">📱</div>
          <h3>No Mobiles Found</h3>
        </div>
      `;
      return;
    }

    container.innerHTML = products.map(product => {
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

  // 2. Render Latest Mobiles Stock
  if (latestGrid) {
    try {
      const data = await API.getProducts({ sort: 'newest', limit: 4 });
      renderCards(latestGrid, data.products);
    } catch (e) {
      console.error("Error loading latest products:", e);
    }
  }

  // 3. Render Featured Mobiles
  if (featuredGrid) {
    try {
      const data = await API.getProducts({ featured: 1, limit: 4 });
      renderCards(featuredGrid, data.products);
    } catch (e) {
      console.error("Error loading featured products:", e);
    }
  }

  // 4. Render Browse All Mobiles
  let browseFilters = { sort: 'newest' };
  async function loadBrowseAll() {
    if (!browseGrid) return;
    try {
      const data = await API.getProducts(browseFilters);
      renderCards(browseGrid, data.products);
    } catch (e) {
      console.error("Error loading browse all products:", e);
    }
  }

  if (searchInput) {
    let timer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        browseFilters.search = e.target.value.trim();
        loadBrowseAll();
      }, 300);
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      browseFilters.sort = e.target.value;
      loadBrowseAll();
    });
  }

  loadBrowseAll();
});
