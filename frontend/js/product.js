/**
 * C2T MOBILES - Single Product Detail Logic & Image Gallery Inspector
 */

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('productDetailContent');
  if (!container) return;

  // Extract ID or Slug from query string or path
  const urlParams = new URLSearchParams(window.location.search);
  let identifier = urlParams.get('id');

  if (!identifier) {
    // Check if URL is in /product/slug format
    const pathParts = window.location.pathname.split('/');
    if (pathParts.includes('product')) {
      identifier = pathParts[pathParts.indexOf('product') + 1];
    }
  }

  if (!identifier) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">❌</div>
        <h3>Product Not Specified</h3>
        <p>Please select a mobile device from our catalog.</p>
        <a href="products.html" class="btn btn-primary">Browse All Mobiles</a>
      </div>
    `;
    return;
  }

  try {
    const product = await API.getProductDetail(identifier);
    document.title = `${product.brand} ${product.model} ${product.storage} Used Mobile | C2T MOBILES`;
    renderProductDetails(product);
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📱</div>
        <h3>Mobile Device Not Found</h3>
        <p>This phone may have been sold or removed from inventory.</p>
        <a href="products.html" class="btn btn-primary">Explore Available Stock</a>
      </div>
    `;
  }

  function renderProductDetails(p) {
    const isSold = p.status === 'SOLD';
    const images = p.images || [{ image_url: p.primary_image || '/assets/images/placeholder.jpg' }];

    const html = `
      <div class="product-detail-grid">
        <!-- Gallery Section -->
        <div class="gallery-wrapper">
          <div class="main-image-box" id="mainImgBox">
            <img id="primaryZoomImg" src="${images[0].image_url}" alt="${p.brand} ${p.model}">
          </div>
          
          <div class="thumbnails-row">
            ${images.map((img, idx) => `
              <div class="thumb-item ${idx === 0 ? 'active' : ''}" onclick="switchGalleryImage('${img.image_url}', this)">
                <img src="${img.image_url}" alt="${p.brand} ${p.model} photo ${idx + 1}">
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Details Info Section -->
        <div class="detail-info-box">
          <div class="detail-header">
            <span class="card-brand">${p.brand}</span>
            <h1 class="detail-title">${p.model}</h1>
            <div class="detail-id-tag">Product ID: <strong>${p.product_id}</strong></div>
          </div>

          <div class="detail-price-row">
            <span class="detail-price">${formatINR(p.price)}</span>
            ${p.mrp_formatted ? `<span class="detail-mrp">${formatINR(p.mrp)}</span>` : ''}
            ${p.discount_percent ? `<span class="detail-discount">${p.discount_percent}% OFF</span>` : ''}
          </div>

          <!-- BUY ON WHATSAPP CARD -->
          <div class="wa-buy-card">
            <h3>💬 Talk Directly With C2T MOBILES</h3>
            <p>Communicate personally with our owner to discuss product condition, availability, delivery, and payment before buying.</p>
            
            ${isSold 
              ? `<button class="btn btn-secondary btn-wa-large" disabled style="opacity:0.7; cursor:not-allowed;">SOLD OUT</button>`
              : `<button id="waDetailBuyBtn" class="btn btn-wa-large">BUY ON WHATSAPP</button>`
            }
          </div>

          <!-- Quick Specs Tags -->
          <div style="background: #f8fafc; padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-color); display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.85rem; font-size: 0.9rem;">
            <div>💾 <strong>Storage:</strong> ${p.storage}</div>
            <div>⚡ <strong>RAM:</strong> ${p.ram || 'N/A'}</div>
            <div>🎨 <strong>Colour:</strong> ${p.colour || 'N/A'}</div>
            <div>🔋 <strong>Battery Health:</strong> ${p.battery_health || 'N/A'}</div>
            <div>⭐ <strong>Condition:</strong> ${p.condition}</div>
            <div>📡 <strong>Network:</strong> ${p.network || '5G'}</div>
            <div>🛡️ <strong>Warranty:</strong> ${p.warranty || '3 Months C2T Warranty'}</div>
            <div>📅 <strong>Purchase Date:</strong> ${p.purchase_date || 'N/A'}</div>
          </div>

          <!-- Box & Accessories Included -->
          <div style="background: white; border: 1px solid var(--border-color); padding: 1.25rem; border-radius: var(--radius-md);">
            <h4 style="font-weight: 800; font-size: 1rem; margin-bottom: 0.75rem;">Package & Accessories Included</h4>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.9rem;">
              <div>📦 Original Box: <strong>${p.box_included ? 'Yes ✓' : 'No ✕'}</strong></div>
              <div>🔌 Charger: <strong>${p.charger_included ? 'Yes ✓' : 'No ✕'}</strong></div>
            </div>
            ${p.accessories ? `<div style="font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem;"><strong>Accessories Details:</strong> ${p.accessories}</div>` : ''}
          </div>
        </div>
      </div>

      <!-- Phone Condition Details Inspection Table -->
      <div class="condition-inspection-box">
        <h3 style="font-size: 1.4rem; font-weight: 800; color: var(--text-main);">🔍 Phone Condition Details</h3>
        <p style="color: var(--text-muted); font-size: 0.925rem; margin-bottom: 1rem;">
          Every device sold by C2T MOBILES undergoes a rigorous 30-point quality check.
        </p>

        <table class="inspection-table">
          <tbody>
            <tr>
              <td>Display Condition</td>
              <td><span class="status-check-pass">✓</span> ${p.display_condition || 'Flawless'}</td>
            </tr>
            <tr>
              <td>Body & Frame</td>
              <td><span class="status-check-pass">✓</span> ${p.body_condition || 'Clean'}</td>
            </tr>
            <tr>
              <td>Camera Lens & Sensor</td>
              <td><span class="status-check-pass">✓</span> ${p.camera_condition || 'Clean, full functionality'}</td>
            </tr>
            <tr>
              <td>Battery Health & Status</td>
              <td><span class="status-check-pass">✓</span> ${p.battery_health} (${p.battery_condition || 'Original OEM'})</td>
            </tr>
            <tr>
              <td>Speaker Sound</td>
              <td><span class="status-check-pass">✓</span> ${p.speaker_condition || 'Loud & clear'}</td>
            </tr>
            <tr>
              <td>Microphone</td>
              <td><span class="status-check-pass">✓</span> ${p.mic_condition || 'Tested & working'}</td>
            </tr>
            <tr>
              <td>Charging Port</td>
              <td><span class="status-check-pass">✓</span> ${p.charging_port_condition || 'Clean & tight fit'}</td>
            </tr>
            <tr>
              <td>Face ID / Fingerprint</td>
              <td><span class="status-check-pass">✓</span> ${p.face_id_condition || 'Working perfectly'}</td>
            </tr>
            <tr>
              <td>Network & 5G SIM</td>
              <td><span class="status-check-pass">✓</span> ${p.network_condition || 'All Indian SIMs tested'}</td>
            </tr>
            <tr>
              <td>Wi-Fi & Bluetooth</td>
              <td><span class="status-check-pass">✓</span> ${p.wifi_condition || 'Tested & fast'}</td>
            </tr>
            <tr>
              <td>Physical Buttons</td>
              <td><span class="status-check-pass">✓</span> ${p.buttons_condition || 'Tactile & working'}</td>
            </tr>
            <tr>
              <td>Repairs & Parts</td>
              <td>${p.repairs || 'No major repairs'} ${p.repair_details ? `(${p.repair_details})` : ''}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Description & Specs -->
      ${p.description ? `
        <div style="background: white; border: 1px solid var(--border-color); padding: 1.75rem; border-radius: var(--radius-md); margin-top: 2rem;">
          <h3 style="font-size: 1.25rem; font-weight: 800; margin-bottom: 0.75rem;">Description</h3>
          <p style="color: var(--text-muted); line-height: 1.7; font-size: 0.95rem;">${p.description}</p>
        </div>
      ` : ''}

      <!-- Similar Mobiles -->
      ${p.related_products && p.related_products.length > 0 ? `
        <div style="margin-top: 4rem;">
          <h3 style="font-size: 1.5rem; font-weight: 800; margin-bottom: 1.5rem;">Similar ${p.brand} Mobiles</h3>
          <div class="product-grid">
            ${p.related_products.map(rel => `
              <div class="product-card">
                <a href="product.html?id=${rel.slug || rel.id}" class="card-image-wrap">
                  <img src="${rel.primary_image}" alt="${rel.brand} ${rel.model}">
                </a>
                <div class="card-body">
                  <div class="card-brand">${rel.brand}</div>
                  <h3 class="card-title"><a href="product.html?id=${rel.slug || rel.id}">${rel.model}</a></h3>
                  <div class="card-pricing">
                    <span class="current-price">${formatINR(rel.price)}</span>
                  </div>
                  <a href="product.html?id=${rel.slug || rel.id}" class="btn btn-secondary btn-sm" style="width:100%;">View Details</a>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}
    `;

    container.innerHTML = html;

    // Attach WhatsApp Buy Button Event Handler
    const waBtn = document.getElementById('waDetailBuyBtn');
    if (waBtn) {
      waBtn.addEventListener('click', async () => {
        try {
          await API.recordEnquiry(p.id);
          window.open(p.whatsapp_url, '_blank');
        } catch (e) {
          window.open(p.whatsapp_url, '_blank');
        }
      });
    }
  }

  // Global gallery image switcher helper
  window.switchGalleryImage = (src, thumbEl) => {
    const mainImg = document.getElementById('primaryZoomImg');
    if (mainImg) mainImg.src = src;

    document.querySelectorAll('.thumb-item').forEach(el => el.classList.remove('active'));
    if (thumbEl) thumbEl.classList.add('active');
  };
});
