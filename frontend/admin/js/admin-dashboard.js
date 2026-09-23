/**
 * C2T MOBILES - Admin Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
  const kpiTotal = document.getElementById('kpiTotal');
  const kpiAvailable = document.getElementById('kpiAvailable');
  const kpiSold = document.getElementById('kpiSold');
  const kpiEnquiries = document.getElementById('kpiEnquiries');
  const enquiriesTable = document.getElementById('recentEnquiriesTable');
  const recentProductsGrid = document.getElementById('recentProductsGrid');

  if (!kpiTotal) return;

  try {
    const data = await API.getAdminDashboard();
    
    if (kpiTotal) kpiTotal.textContent = data.total_products;
    if (kpiAvailable) kpiAvailable.textContent = data.available_products;
    if (kpiSold) kpiSold.textContent = data.sold_products;
    if (kpiEnquiries) kpiEnquiries.textContent = data.total_enquiries;

    if (enquiriesTable) {
      if (!data.recent_enquiries || data.recent_enquiries.length === 0) {
        enquiriesTable.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 2rem;">No WhatsApp enquiries recorded yet.</td></tr>`;
      } else {
        enquiriesTable.innerHTML = data.recent_enquiries.map(e => `
          <tr>
            <td><strong>${e.product_name}</strong> (${e.product_code || 'N/A'})</td>
            <td>${e.product_price_formatted}</td>
            <td><span class="status-pill status-available">WhatsApp Enquiry</span></td>
            <td>${new Date(e.created_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</td>
          </tr>
        `).join('');
      }
    }

    if (recentProductsGrid) {
      recentProductsGrid.innerHTML = data.recent_products.map(p => `
        <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
          <img src="${p.primary_image}" style="width: 48px; height: 48px; object-fit: contain; background: #f8fafc; border-radius: 6px;">
          <div style="flex-grow: 1;">
            <div style="font-weight: 700; font-size: 0.95rem;">${p.brand} ${p.model}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">${p.product_id} • ${p.price_formatted}</div>
          </div>
          <span class="status-pill ${p.status === 'AVAILABLE' ? 'status-available' : 'status-sold'}">${p.status}</span>
        </div>
      `).join('');
    }

  } catch (err) {
    console.error("Failed to load dashboard statistics:", err);
  }
});
