/**
 * C2T MOBILES - Admin Stock Management Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('productsTableBody');
  const searchInput = document.getElementById('adminSearchInput');
  const statusFilter = document.getElementById('adminStatusFilter');
  const deleteModal = document.getElementById('deleteConfirmModal');
  const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
  const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');

  if (!tableBody) return;

  let currentSearch = '';
  let currentStatus = '';
  let pendingDeleteId = null;

  async function loadAdminInventory() {
    tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem;">Loading inventory...</td></tr>`;

    try {
      const data = await API.getAdminProducts({ search: currentSearch, status: currentStatus });
      renderInventoryTable(data.products);
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem; color: var(--accent-rose);">Failed to load inventory.</td></tr>`;
    }
  }

  function renderInventoryTable(products) {
    if (!products || products.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 3rem;">No products match your criteria.</td></tr>`;
      return;
    }

    tableBody.innerHTML = products.map(p => {
      const isSold = p.status === 'SOLD';
      return `
        <tr>
          <td><img src="${p.primary_image}" class="table-thumb" alt="${p.model}"></td>
          <td><strong>${p.product_id}</strong></td>
          <td>
            <div style="font-weight: 700;">${p.brand} ${p.model}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">${p.storage} ${p.colour ? '• ' + p.colour : ''}</div>
          </td>
          <td><strong>${p.price_formatted}</strong></td>
          <td><span class="spec-chip">${p.condition}</span></td>
          <td>${p.battery_health || 'N/A'}</td>
          <td>
            <span class="status-pill ${isSold ? 'status-sold' : 'status-available'}">${p.status}</span>
          </td>
          <td>${p.featured ? '⭐ Yes' : 'No'}</td>
          <td>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
              <a href="/product.html?id=${p.slug || p.id}" target="_blank" class="btn btn-secondary btn-sm" style="padding: 0.35rem 0.6rem;">View</a>
              <a href="edit-product.html?id=${p.id}" class="btn btn-primary btn-sm" style="padding: 0.35rem 0.6rem;">Edit</a>
              <button onclick="toggleProductStatus(${p.id}, '${isSold ? 'AVAILABLE' : 'SOLD'}')" class="btn btn-secondary btn-sm" style="padding: 0.35rem 0.6rem;">
                Mark ${isSold ? 'Available' : 'Sold'}
              </button>
              <button onclick="openDeleteModal(${p.id})" class="btn btn-sm" style="background: rgba(225,29,72,0.1); color: var(--accent-rose); padding: 0.35rem 0.6rem;">Delete</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  }

  // Toggle status helper
  window.toggleProductStatus = async (id, newStatus) => {
    try {
      await API.updateProductStatus(id, newStatus);
      loadAdminInventory();
    } catch (err) {
      alert("Status update failed: " + err.message);
    }
  };

  // Delete modal helpers
  window.openDeleteModal = (id) => {
    pendingDeleteId = id;
    if (deleteModal) deleteModal.classList.add('active');
  };

  if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener('click', () => {
      pendingDeleteId = null;
      if (deleteModal) deleteModal.classList.remove('active');
    });
  }

  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', async () => {
      if (!pendingDeleteId) return;
      try {
        await API.deleteProduct(pendingDeleteId);
        pendingDeleteId = null;
        if (deleteModal) deleteModal.classList.remove('active');
        loadAdminInventory();
      } catch (err) {
        alert("Delete failed: " + err.message);
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearch = e.target.value.trim();
      loadAdminInventory();
    });
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => {
      currentStatus = e.target.value;
      loadAdminInventory();
    });
  }

  loadAdminInventory();
});
