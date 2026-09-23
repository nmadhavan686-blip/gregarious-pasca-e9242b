/**
 * C2T MOBILES - Core Application JS with Auth State Guard & RBAC Header Navigation
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Check User Authentication State
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  const isAuthPage = currentPath === 'login.html' || currentPath === 'register.html';

  let authState = { authenticated: false };
  try {
    authState = await API.getUserMe();
  } catch (e) {
    console.warn("Auth check error");
  }

  // App Startup Flow Enforcement:
  // If user is unauthenticated and NOT on login/register/admin pages, redirect to login.html
  if (!authState.authenticated && !isAuthPage && !window.location.pathname.includes('/admin')) {
    window.location.href = '/login.html';
    return;
  }

  // Render User Profile Menu & Role-Based Navigation in Header
  renderHeaderAuth(authState);

  // 2. Initialize Site Settings (WhatsApp Number & Contact info)
  let siteSettings = { owner_whatsapp: '919994645492', owner_name: 'C2T MOBILES' };
  try {
    siteSettings = await API.getSettings();
  } catch (e) {
    console.warn("Using default fallback settings");
  }

  const defaultWaNum = (siteSettings.owner_whatsapp || '919994645492').replace(/\D/g, '');

  const floatWA = document.getElementById('floatingWA');
  if (floatWA) {
    const genMsg = encodeURIComponent("Hi C2T MOBILES, I would like to know about the available mobiles.");
    floatWA.href = `https://wa.me/${defaultWaNum}?text=${genMsg}`;
    floatWA.target = "_blank";
  }

  const globalWALinks = document.querySelectorAll('.dynamic-wa-link');
  globalWALinks.forEach(link => {
    const genMsg = encodeURIComponent("Hi C2T MOBILES, I would like to know about the available mobiles.");
    link.href = `https://wa.me/${defaultWaNum}?text=${genMsg}`;
    link.target = "_blank";
  });

  // 3. Mobile Drawer Navigation Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const mobileDrawer = document.getElementById('mobileDrawer');
  const drawerOverlay = document.getElementById('drawerOverlay');
  const drawerClose = document.getElementById('drawerClose');

  if (mobileToggle && mobileDrawer && drawerOverlay) {
    const openDrawer = () => {
      mobileDrawer.classList.add('active');
      drawerOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    };

    const closeDrawer = () => {
      mobileDrawer.classList.remove('active');
      drawerOverlay.classList.remove('active');
      document.body.style.overflow = '';
    };

    mobileToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (mobileDrawer.classList.contains('active')) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });

    drawerOverlay.addEventListener('click', closeDrawer);
    if (drawerClose) drawerClose.addEventListener('click', closeDrawer);

    // Auto-close drawer when clicking any link inside drawer
    const drawerLinks = mobileDrawer.querySelectorAll('a, button');
    drawerLinks.forEach(link => {
      link.addEventListener('click', () => {
        closeDrawer();
      });
    });
  }

  // 4. Highlight Active Navigation Item
  const navLinks = document.querySelectorAll('.nav-link, .drawer-nav a, .bottom-nav-item');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
});

function renderHeaderAuth(authState) {
  const container = document.getElementById('userHeaderAuth');
  const drawerAuth = document.getElementById('mobileDrawerAuth');
  const navMenus = document.querySelectorAll('.nav-menu, .nav-links');

  if (!container) return;

  if (authState.authenticated && authState.user) {
    const isOwner = ['owner', 'admin'].includes(authState.user.role);
    const firstName = authState.user.full_name ? authState.user.full_name.split(' ')[0] : 'User';
    const avatarHtml = authState.user.avatar_url 
      ? `<img src="${authState.user.avatar_url}" alt="Avatar" style="width:22px;height:22px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:6px;">`
      : `<span style="margin-right:4px;">👤</span>`;

    // Add Admin Dashboard link for Owner role in main navbar
    if (isOwner) {
      navMenus.forEach(menu => {
        if (!menu.querySelector('.owner-nav-item')) {
          const li = document.createElement('li');
          li.className = 'owner-nav-item';
          li.innerHTML = `<a href="admin/dashboard.html" class="nav-link" style="color:#f59e0b; font-weight:800;">⚡ Admin Dashboard</a>`;
          menu.appendChild(li);
        }
      });
    }

    container.innerHTML = `
      <div class="user-profile-menu">
        <button class="user-profile-btn" onclick="toggleUserDropdown(event)">
          ${avatarHtml} Hi, ${firstName} ${isOwner ? '<span style="background:#f59e0b; color:#0f172a; padding:1px 6px; border-radius:4px; font-size:0.65rem; font-weight:800; margin-left:4px;">OWNER</span>' : ''} 👋
        </button>
        <div class="user-dropdown" id="userDropdownMenu">
          <div style="padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; font-size:0.8rem; color:#64748b;">
            Signed in as <strong>${authState.user.email}</strong>
            ${isOwner ? '<div style="color:#d97706; font-weight:700; margin-top:2px;">Role: Owner / Admin</div>' : ''}
          </div>
          ${isOwner ? '<a href="admin/dashboard.html" style="color:#d97706; font-weight:700;">⚡ Admin Dashboard</a>' : ''}
          <a href="account.html">My Account</a>
          <a href="account.html">My Enquiries</a>
          <button onclick="handleUserLogout()">Logout</button>
        </div>
      </div>
    `;

    if (drawerAuth) {
      drawerAuth.innerHTML = `
        <div style="color:#cbd5e1; font-weight:700; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.5rem;">
          ${avatarHtml} ${authState.user.full_name} ${isOwner ? '<span style="background:#f59e0b; color:#0f172a; padding:1px 6px; border-radius:4px; font-size:0.65rem; font-weight:800;">OWNER</span>' : ''}
        </div>
        ${isOwner ? '<a href="admin/dashboard.html" class="btn btn-warning btn-sm" style="width:100%; margin-bottom:0.5rem; text-align:center; background:#f59e0b; color:#0f172a; font-weight:800;">⚡ Admin Dashboard</a>' : ''}
        <a href="account.html" class="btn btn-outline-light btn-sm" style="width:100%; margin-bottom:0.5rem; text-align:center;">My Account</a>
        <button onclick="handleUserLogout()" class="btn btn-outline-danger btn-sm" style="width:100%;">Logout</button>
      `;
    }
  } else {
    container.innerHTML = `
      <a href="login.html" class="btn btn-outline-light btn-sm" style="font-size:0.85rem; padding:0.4rem 0.9rem;">Login</a>
    `;
    if (drawerAuth) {
      drawerAuth.innerHTML = `
        <a href="login.html" class="btn btn-outline-light" style="width:100%;">Sign In / Register</a>
      `;
    }
  }
}

window.toggleUserDropdown = (e) => {
  e.stopPropagation();
  const dropdown = document.getElementById('userDropdownMenu');
  if (dropdown) dropdown.classList.toggle('active');
};

document.addEventListener('click', () => {
  const dropdown = document.getElementById('userDropdownMenu');
  if (dropdown) dropdown.classList.remove('active');
});

window.handleUserLogout = async () => {
  await API.userLogout();
  window.location.href = '/login.html';
};

/** Helper to format price into Indian Rupees */
function formatINR(price) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(price);
}

/** Global WhatsApp Product Enquiry Handler */
window.handleWaBuyClick = async (event, productId, brandName, modelName) => {
  if (event) event.preventDefault();
  let bName = brandName || '';
  let mName = modelName || '';
  
  if (!bName || !mName) {
    try {
      const prod = await API.getProductDetail(productId);
      if (prod && (prod.product || prod.brand)) {
        const p = prod.product || prod;
        bName = p.brand;
        mName = p.model;
      }
    } catch (e) {}
  }
  
  const title = (bName && mName) ? `${bName} ${mName}` : (mName || 'smartphone');
  const msg = encodeURIComponent(`Hi C2T MOBILES, I'm interested in the ${title}. Please share the details and availability.`);
  
  if (productId) API.recordEnquiry(productId);
  window.open(`https://wa.me/919994645492?text=${msg}`, '_blank');
};
