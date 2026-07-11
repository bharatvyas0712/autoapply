/* ================================================================
   AutoJobApply — Profile Wizard Script (js/profile.js)
================================================================ */

requireAuth();

let currentStep = 1;
let skills = [];
let workHistory = [];
let education = [];

document.addEventListener('DOMContentLoaded', () => {
  injectSidebar('profile');
  loadProfileData();

  // Check URL parameters for starting point
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('wizard') === 'resume') {
    goToStep(1);
  }
});

// ── Wizard Step Navigation ────────────────────────────────────
function goToStep(stepNum) {
  if (stepNum < 1 || stepNum > 4) return;
  
  // Validate basic requirements before stepping forward
  if (stepNum > 2 && currentStep === 2) {
    const name = document.getElementById('profile-name').value.trim();
    const phone = document.getElementById('profile-phone').value.trim();
    const location = document.getElementById('profile-location').value.trim();
    if (!name || !phone || !location) {
      showToast('Please fill in Name, Phone, and Location fields.', 'warning');
      return;
    }
  }

  // Toggle active pages
  document.querySelectorAll('.wizard-step').forEach(step => step.style.display = 'none');
  document.getElementById(`step-${stepNum}`).style.display = 'block';

  // Toggle Indicators
  document.querySelectorAll('.step').forEach((step, idx) => {
    step.classList.remove('active', 'done');
    if (idx + 1 < stepNum) step.classList.add('done');
    else if (idx + 1 === stepNum) step.classList.add('active');
  });

  currentStep = stepNum;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Skills Tag Management ─────────────────────────────────────
function handleSkillsKeydown(e) {
  if (e.key === ',' || e.key === 'Enter') {
    e.preventDefault();
    const val = e.target.value.trim().replace(/,$/, '');
    if (val && !skills.includes(val)) {
      skills.push(val);
      renderSkills();
    }
    e.target.value = '';
  }
}

function removeSkill(skill) {
  skills = skills.filter(s => s !== skill);
  renderSkills();
}

function renderSkills() {
  const container = document.getElementById('skills-tags-container');
  container.innerHTML = '';
  skills.forEach(skill => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.style.display = 'inline-flex';
    tag.style.alignItems = 'center';
    tag.style.gap = '5px';
    tag.innerHTML = `
      ${skill}
      <span onclick="removeSkill('${skill}')" style="cursor:pointer; font-weight:bold; color:var(--text-muted);">×</span>
    `;
    container.appendChild(tag);
  });
}

// ── Work History & Education Dynamism ────────────────────────
function addWorkHistoryItem(item = {}) {
  const container = document.getElementById('work-history-list');
  const id = Date.now() + Math.random().toString(36).substr(2, 5);

  const block = document.createElement('div');
  block.className = 'card';
  block.id = `work-${id}`;
  block.style.padding = '16px';
  block.style.position = 'relative';

  block.innerHTML = `
    <button type="button" class="btn btn-ghost btn-sm" onclick="removeWorkItem('${id}')" style="position:absolute; right:10px; top:10px;">✕</button>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:12px;">
      <div>
        <label class="form-label">Job Title</label>
        <input type="text" class="form-control work-title" value="${item.title || ''}" placeholder="Software Engineer">
      </div>
      <div>
        <label class="form-label">Company Name</label>
        <input type="text" class="form-control work-company" value="${item.company || ''}" placeholder="Amazon">
      </div>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; margin-bottom:12px;">
      <div>
        <label class="form-label">Start Date</label>
        <input type="month" class="form-control work-start" value="${item.start || ''}">
      </div>
      <div>
        <label class="form-label">End Date</label>
        <input type="month" class="form-control work-end" value="${item.end || ''}" placeholder="Present">
      </div>
      <div style="display:flex; align-items:center; margin-top:24px;">
        <label class="toggle">
          <input type="checkbox" class="work-current" ${item.current ? 'checked' : ''}>
          <div class="toggle-track" style="width:36px; height:20px;"><div class="toggle-thumb" style="width:14px; height:14px;"></div></div>
          <span class="toggle-label" style="font-size:12px;">Current Role</span>
        </label>
      </div>
    </div>
    <div>
      <label class="form-label">Description / Achievements</label>
      <textarea class="form-control work-desc" placeholder="Developed fullstack API features and migrated server scripts...">${item.description || ''}</textarea>
    </div>
  `;
  container.appendChild(block);
}

function removeWorkItem(id) {
  document.getElementById(`work-${id}`).remove();
}

function addEducationItem(item = {}) {
  const container = document.getElementById('education-list');
  const id = Date.now() + Math.random().toString(36).substr(2, 5);

  const block = document.createElement('div');
  block.className = 'card';
  block.id = `edu-${id}`;
  block.style.padding = '16px';
  block.style.position = 'relative';

  block.innerHTML = `
    <button type="button" class="btn btn-ghost btn-sm" onclick="removeEduItem('${id}')" style="position:absolute; right:10px; top:10px;">✕</button>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:12px;">
      <div>
        <label class="form-label">Degree / Certificate</label>
        <input type="text" class="form-control edu-degree" value="${item.degree || ''}" placeholder="Bachelor of Science in CS">
      </div>
      <div>
        <label class="form-label">School / University</label>
        <input type="text" class="form-control edu-school" value="${item.school || ''}" placeholder="MIT">
      </div>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
      <div>
        <label class="form-label">Field of Study</label>
        <input type="text" class="form-control edu-field" value="${item.field || ''}" placeholder="Computer Science">
      </div>
      <div>
        <label class="form-label">Graduation Year</label>
        <input type="number" class="form-control edu-year" value="${item.year || ''}" placeholder="2025">
      </div>
    </div>
  `;
  container.appendChild(block);
}

function removeEduItem(id) {
  document.getElementById(`edu-${id}`).remove();
}

// ── Upload Resume & Parse ─────────────────────────────────────
async function uploadResumeFile(e) {
  const file = e.target.files[0];
  if (!file) return;

  const progressDiv = document.getElementById('resume-upload-progress');
  const successDiv = document.getElementById('resume-success-info');
  const progressFill = document.getElementById('upload-progress-fill');
  const pctText = document.getElementById('upload-pct');
  const statusText = document.getElementById('upload-status-text');

  progressDiv.style.display = 'block';
  successDiv.style.display = 'none';
  progressFill.style.width = '0%';
  pctText.innerText = '0%';
  statusText.innerText = 'Uploading and parsing PDF...';

  // Use XMLHttpRequest to track progress
  const formData = new FormData();
  formData.append('resume', file);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', window.location.origin + '/api/profile/resume', true);
  if (api.token) xhr.setRequestHeader('Authorization', `Bearer ${api.token}`);

  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const percent = Math.round((event.loaded / event.total) * 100);
      progressFill.style.width = `${percent}%`;
      pctText.innerText = `${percent}%`;
    }
  };

  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const res = JSON.parse(xhr.responseText);
        if (res.success) {
          progressFill.style.width = '100%';
          pctText.innerText = '100%';
          statusText.innerText = 'Done!';
          successDiv.style.display = 'flex';
          
          showToast('Resume parsed successfully! Form fields populated.', 'success');

          // Auto-fill parsed details
          if (res.parsed) {
            const p = res.parsed;
            if (p.email) document.getElementById('profile-name').value = p.email.split('@')[0]; // fallback
            if (p.phone) document.getElementById('profile-phone').value = p.phone;
            if (p.skills && p.skills.length) {
              skills = [...new Set([...skills, ...p.skills])];
              renderSkills();
            }
            if (p.experience_years) {
              document.getElementById('profile-exp-years').value = p.experience_years;
            }
          }
          
          setTimeout(() => goToStep(2), 1500);
        } else {
          showToast(res.message || 'Parsing failed.', 'error');
          progressDiv.style.display = 'none';
        }
      } catch (e) {
        showToast('Failed to parse upload response.', 'error');
      }
    } else {
      showToast('Error uploading file.', 'error');
    }
  };

  xhr.onerror = () => {
    showToast('Network error during upload.', 'error');
  };

  xhr.send(formData);
}

// ── Upload Profile Photo ──────────────────────────────────────
async function uploadPhotoFile(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('photo', file);

  try {
    showToast('Uploading profile photo...', 'info');
    const res = await api.upload('/profile/photo', formData);
    if (res.success) {
      showToast('Photo uploaded.');
      document.getElementById('profile-photo-preview').src = res.photo_url;
      document.getElementById('profile-photo-preview').style.display = 'block';
      document.getElementById('profile-photo-placeholder').style.display = 'none';
    } else {
      showToast(res.message || 'Failed to upload photo.', 'error');
    }
  } catch (err) {
    console.error(err);
  }
}

// ── Toggle QA Selectable Options ─────────────────────────────
function toggleQAOption(el, val) {
  const opts = el.parentElement.querySelectorAll('.qa-option');
  opts.forEach(opt => opt.classList.remove('selected'));
  el.classList.add('selected');
}

// ── Load Existing Profile Data ────────────────────────────────
async function loadProfileData() {
  try {
    const res = await api.get('/profile');
    if (res.success && res.user) {
      const u = res.user;
      const p = res.profile || {};

      // Fill user data
      document.getElementById('profile-name').value = u.full_name || '';
      document.getElementById('profile-phone').value = u.phone || '';
      document.getElementById('profile-location').value = u.location || '';

      if (u.profile_photo) {
        document.getElementById('profile-photo-preview').src = u.profile_photo;
        document.getElementById('profile-photo-preview').style.display = 'block';
        document.getElementById('profile-photo-placeholder').style.display = 'none';
      }

      // Fill profile wizard values
      document.getElementById('profile-headline').value = p.headline || '';
      document.getElementById('profile-summary').value = p.summary || '';
      document.getElementById('profile-linkedin').value = p.linkedin_url || '';
      document.getElementById('profile-github').value = p.github_url || '';
      document.getElementById('profile-portfolio').value = p.portfolio_url || '';
      document.getElementById('profile-exp-years').value = p.experience_years || 0;
      document.getElementById('profile-curr-sal').value = p.current_salary || '';
      document.getElementById('profile-exp-sal').value = p.expected_salary || '';
      document.getElementById('pref-job-types').value = p.job_type_pref || 'full-time';
      document.getElementById('pref-notice').value = p.notice_period_days || 0;
      document.getElementById('pref-relocate').checked = !!p.willing_to_relocate;

      // Populate skills tags
      if (p.skills) {
        skills = p.skills;
        renderSkills();
      }

      // Populate work history list
      if (p.work_history && Array.isArray(p.work_history)) {
        p.work_history.forEach(w => addWorkHistoryItem(w));
      } else {
        addWorkHistoryItem(); // one blank input template
      }

      // Populate education list
      if (p.education && Array.isArray(p.education)) {
        p.education.forEach(e => addEducationItem(e));
      } else {
        addEducationItem(); // one blank input template
      }

      // Populate Q&A options
      if (p.custom_answers) {
        const qa = p.custom_answers;
        for (const [key, val] of Object.entries(qa)) {
          const optContainer = document.querySelector(`.qa-options[data-qa-key="${key}"]`);
          if (optContainer) {
            const opts = optContainer.querySelectorAll('.qa-option');
            opts.forEach(opt => {
              if (opt.innerText.trim() === val) opt.classList.add('selected');
              else opt.classList.remove('selected');
            });
          }
        }
      }
    }
  } catch (err) {
    console.error('Error loading profile details:', err);
  }
}

// ── Save Form Data to Database ────────────────────────────────
async function saveAllProfileData(e) {
  e.preventDefault();

  const name = document.getElementById('profile-name').value.trim();
  const phone = document.getElementById('profile-phone').value.trim();
  const location = document.getElementById('profile-location').value.trim();

  if (!name || !phone || !location) {
    showToast('Name, Phone, and Location are mandatory details.', 'error');
    return;
  }

  // Extract Work History Array
  const workItems = [];
  document.querySelectorAll('#work-history-list > div').forEach(div => {
    const title = div.querySelector('.work-title').value.trim();
    const company = div.querySelector('.work-company').value.trim();
    if (title || company) {
      workItems.push({
        title,
        company,
        start: div.querySelector('.work-start').value,
        end: div.querySelector('.work-end').value,
        current: div.querySelector('.work-current').checked,
        description: div.querySelector('.work-desc').value.trim()
      });
    }
  });

  // Extract Education Array
  const eduItems = [];
  document.querySelectorAll('#education-list > div').forEach(div => {
    const degree = div.querySelector('.edu-degree').value.trim();
    const school = div.querySelector('.edu-school').value.trim();
    if (degree || school) {
      eduItems.push({
        degree,
        school,
        field: div.querySelector('.edu-field').value.trim(),
        year: div.querySelector('.edu-year').value
      });
    }
  });

  // Extract QA Answers object
  const customAnswers = {};
  document.querySelectorAll('.qa-options').forEach(optContainer => {
    const key = optContainer.getAttribute('data-qa-key');
    const selected = optContainer.querySelector('.qa-option.selected');
    if (key && selected) {
      customAnswers[key] = selected.innerText.trim();
    }
  });

  const payload = {
    full_name: name,
    phone,
    location,
    headline: document.getElementById('profile-headline').value.trim(),
    summary: document.getElementById('profile-summary').value.trim(),
    linkedin_url: document.getElementById('profile-linkedin').value.trim(),
    github_url: document.getElementById('profile-github').value.trim(),
    portfolio_url: document.getElementById('profile-portfolio').value.trim(),
    skills,
    experience_years: parseFloat(document.getElementById('profile-exp-years').value) || 0,
    current_salary: parseFloat(document.getElementById('profile-curr-sal').value) || null,
    expected_salary: parseFloat(document.getElementById('profile-exp-sal').value) || null,
    work_history: workItems,
    education: eduItems,
    job_type_pref: document.getElementById('pref-job-types').value,
    notice_period_days: parseInt(document.getElementById('pref-notice').value) || 0,
    willing_to_relocate: document.getElementById('pref-relocate').checked ? 1 : 0,
    custom_answers: customAnswers
  };

  try {
    const res = await api.put('/profile', payload);
    if (res.success) {
      showToast('Profile configuration saved successfully!', 'success');
      
      // Update sidebar avatar user session cache
      const cachedUser = getUserData();
      if (cachedUser) {
        cachedUser.full_name = name;
        cachedUser.phone = phone;
        cachedUser.location = location;
        setUserData(cachedUser);
      }
      
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 1200);
    } else {
      showToast(res.message || 'Failed to update profile.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Database error during update.', 'error');
  }
}
