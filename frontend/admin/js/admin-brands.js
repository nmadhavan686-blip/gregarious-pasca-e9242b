/**
 * C2T MOBILES - Admin Brand Management Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('brandsTableBody');
  const addForm = document.getElementById('addBrandForm');
  const modal = document.getElementById('brandModal');
  const openModalBtn = document.getElementById('openAddBrandModal');
  const closeModalBtn = document.getElementById('closeBrandModal');

  if (!tableBody) return;

  let isEditing = false;
  let editingId = null;

  async function loadAdminBrands() {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem;">Loading brands...</td></tr>`;

    try {
      const data = await API.getAdminBrands();
      renderBrandsTable(data.brands);
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--accent-rose);">Failed to load brands.</td></tr>`;
    }
  }

  function renderBrandsTable(brands) {
    if (!brands || brands.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem;">No brands configured.</td></tr>`;
      return;
    }

    tableBody.innerHTML = brands.map(b => `
      <tr>
        <td style="font-size: 1.5rem;">${b.logo_icon || '📱'}</td>
        <td><strong>${b.name}</strong></td>
        <td><code>${b.slug}</code></td>
        <td>${b.display_order}</td>
        <td>
          <span class="status-pill ${b.is_active ? 'status-available' : 'status-sold'}">
            ${b.is_active ? 'Active' : 'Disabled'}
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 0.5rem;">
            <button onclick="editBrandModal(${b.id}, '${b.name}', '${b.logo_icon}', '${b.description || ''}', ${b.display_order}, ${b.is_active})" class="btn btn-primary btn-sm" style="padding: 0.35rem 0.6rem;">Edit</button>
            <button onclick="deleteBrandConfirm(${b.id})" class="btn btn-sm" style="background: rgba(225,29,72,0.1); color: var(--accent-rose); padding: 0.35rem 0.6rem;">Delete</button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  window.editBrandModal = (id, name, logo, desc, order, active) => {
    isEditing = true;
    editingId = id;
    document.getElementById('modalTitle').textContent = "Edit Brand";
    document.getElementById('brand_name').value = name;
    document.getElementById('brand_icon').value = logo;
    document.getElementById('brand_desc').value = desc;
    document.getElementById('brand_order').value = order;
    document.getElementById('brand_active').value = active;
    if (modal) modal.classList.add('active');
  };

  window.deleteBrandConfirm = async (id) => {
    if (!confirm("Are you sure you want to delete this brand?")) return;
    try {
      await API.deleteBrand(id);
      loadAdminBrands();
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  };

  if (openModalBtn) {
    openModalBtn.addEventListener('click', () => {
      isEditing = false;
      editingId = null;
      document.getElementById('modalTitle').textContent = "Add New Brand";
      addForm.reset();
      if (modal) modal.classList.add('active');
    });
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      if (modal) modal.classList.remove('active');
    });
  }

  if (addForm) {
    addForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        name: document.getElementById('brand_name').value.trim(),
        logo_icon: document.getElementById('brand_icon').value.trim(),
        description: document.getElementById('brand_desc').value.trim(),
        display_order: parseInt(document.getElementById('brand_order').value || 0),
        is_active: parseInt(document.getElementById('brand_active').value || 1)
      };

      try {
        if (isEditing) {
          await API.updateBrand(editingId, data);
          alert("Brand updated successfully!");
        } else {
          await API.createBrand(data);
          alert("Brand created successfully!");
        }
        if (modal) modal.classList.remove('active');
        loadAdminBrands();
      } catch (err) {
        alert("Error saving brand: " + err.message);
      }
    });
  }

  loadAdminBrands();
});
