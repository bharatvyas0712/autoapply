/* ================================================================
   AutoJobApply — Authentication Operations (js/auth.js)
================================================================ */

// Redirect to dashboard if user already logged in
if (isLoggedIn() && (window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/') || window.location.pathname.includes('register.html'))) {
  window.location.href = 'dashboard.html';
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const submitBtn = document.getElementById('submit-btn');

  if (!email || !password) {
    showToast('Please fill all required fields.', 'error');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Logging in...';

  try {
    const res = await api.post('/auth/login', { email, password });
    if (res.success) {
      api.setToken(res.token);
      setUserData(res.user);
      showToast('Logged in successfully!', 'success');
      
      // Keep theme preference
      if (res.user.theme_pref) {
        localStorage.setItem('theme', res.user.theme_pref);
      }

      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 800);
    } else {
      showToast(res.message || 'Login failed. Invalid credentials.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerText = 'Sign In';
    }
  } catch (err) {
    console.error(err);
    showToast('An unexpected network error occurred.', 'error');
    submitBtn.disabled = false;
    submitBtn.innerText = 'Sign In';
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const full_name = document.getElementById('fullname').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const phone = document.getElementById('phone').value.trim();
  const location = document.getElementById('location').value.trim();
  const submitBtn = document.getElementById('submit-btn');

  if (!full_name || !email || !password) {
    showToast('Please fill all required fields.', 'error');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Creating Account...';

  try {
    const res = await api.post('/auth/register', {
      full_name,
      email,
      password,
      phone: phone || null,
      location: location || null
    });

    if (res.success) {
      api.setToken(res.token);
      setUserData(res.user);
      showToast('Account created successfully!', 'success');
      setTimeout(() => {
        window.location.href = 'profile.html?wizard=start';
      }, 1000);
    } else {
      showToast(res.message || 'Registration failed.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerText = 'Create Account';
    }
  } catch (err) {
    console.error(err);
    showToast('An unexpected error occurred.', 'error');
    submitBtn.disabled = false;
    submitBtn.innerText = 'Create Account';
  }
}
