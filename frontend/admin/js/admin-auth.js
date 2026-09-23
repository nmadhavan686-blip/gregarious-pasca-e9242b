/**
 * C2T MOBILES - Admin Auth Guard
 */

async function requireAdminAuth() {
  const currentFile = window.location.pathname.split('/').pop();
  if (currentFile === 'login.html') return;

  try {
    const status = await API.checkAdminAuth();
    if (!status.authenticated) {
      window.location.href = '/admin/login.html';
    }
  } catch (err) {
    window.location.href = '/admin/login.html';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  requireAdminAuth();

  const logoutBtn = document.getElementById('adminLogoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      await API.adminLogout();
      window.location.href = '/admin/login.html';
    });
  }
});
