/**
 * C2T MOBILES - Admin Stock Form Handler (Add & Edit Product)
 */

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('productForm');
  const imageInput = document.getElementById('imageInput');
  const imagePreviewGrid = document.getElementById('imagePreviewGrid');
  const formTitle = document.getElementById('formTitle');
  const submitBtn = document.getElementById('submitBtn');

  if (!form) return;

  const urlParams = new URLSearchParams(window.location.search);
  const editId = urlParams.get('id');
  const isEdit = Boolean(editId);

  if (isEdit && formTitle) {
    formTitle.textContent = "Edit Mobile Stock";
    if (submitBtn) submitBtn.textContent = "Update Mobile";
  }

  // Pre-fill form if editing existing device
  if (isEdit) {
    try {
      const prod = await API.getProductDetail(editId);
      populateForm(prod);
    } catch (err) {
      alert("Failed to load device details for editing");
    }
  }

  function populateForm(p) {
    const fields = [
      'product_id', 'brand', 'model', 'price', 'mrp', 'storage', 'ram', 'colour',
      'condition', 'battery_health', 'network', 'sim_type', 'warranty', 'accessories',
      'box_included', 'charger_included', 'purchase_date', 'description', 'specifications',
      'status', 'featured', 'badge', 'display_condition', 'body_condition', 'camera_condition',
      'battery_condition', 'speaker_condition', 'mic_condition', 'charging_port_condition',
      'face_id_condition', 'network_condition', 'wifi_condition', 'bluetooth_condition',
      'buttons_condition', 'repairs', 'repair_details'
    ];

    fields.forEach(field => {
      const input = form.elements[field];
      if (input && p[field] !== undefined) {
        if (input.type === 'checkbox') {
          input.checked = Boolean(p[field]);
        } else {
          input.value = p[field];
        }
      }
    });

    // Render existing images
    if (p.images && imagePreviewGrid) {
      imagePreviewGrid.innerHTML = p.images.map(img => `
        <div class="preview-thumb-box" id="imgBox_${img.id}">
          <img src="${img.image_url}" alt="Product photo">
          <button type="button" class="btn-remove-img" onclick="deleteExistingImg(${img.id})">✕</button>
        </div>
      `).join('');
    }
  }

  // Delete existing image handler
  window.deleteExistingImg = async (imageId) => {
    if (!confirm("Are you sure you want to delete this photo?")) return;
    try {
      await API.deleteImage(imageId);
      const el = document.getElementById(`imgBox_${imageId}`);
      if (el) el.remove();
    } catch (err) {
      alert("Failed to delete photo");
    }
  };

  // Preview newly selected image files
  if (imageInput && imagePreviewGrid) {
    imageInput.addEventListener('change', (e) => {
      const files = Array.from(e.target.files);
      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
          const div = document.createElement('div');
          div.className = 'preview-thumb-box';
          div.innerHTML = `<img src="${event.target.result}"><span style="position:absolute; bottom:2px; right:2px; font-size:9px; background:rgba(0,0,0,0.7); color:white; padding:1px 3px;">NEW</span>`;
          imagePreviewGrid.appendChild(div);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  // Submit form handler
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving...";

    const formData = new FormData(form);

    try {
      if (isEdit) {
        await API.updateProduct(editId, formData);
        alert("Mobile updated successfully!");
      } else {
        await API.createProduct(formData);
        alert("New Mobile added successfully!");
      }
      window.location.href = '/admin/products.html';
    } catch (err) {
      alert("Error saving mobile: " + err.message);
      submitBtn.disabled = false;
      submitBtn.textContent = isEdit ? "Update Mobile" : "Save Mobile";
    }
  });
});
