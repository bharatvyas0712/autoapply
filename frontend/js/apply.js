/* ================================================================
   AutoJobApply — Apply/Review Page Script (js/apply.js)
================================================================ */

requireAuth();

let applicationId = null;
let applicationData = null;
let pollingInterval = null;

document.addEventListener('DOMContentLoaded', () => {
  injectSidebar('jobs');
  const params = new URLSearchParams(window.location.search);
  applicationId = params.get('id');
  if (!applicationId) {
    showToast('No application ID specified.', 'error');
    setTimeout(() => window.location.href = 'jobs.html', 2000);
    return;
  }
  loadApplicationData(applicationId);
});

async function loadApplicationData(id) {
  try {
    const res = await api.get(`/applications/${id}`);
    if (!res.success) {
      showToast('Application not found.', 'error');
      setTimeout(() => window.location.href = 'jobs.html', 2000);
      return;
    }
    applicationData = res.application;

    // Populate job banner
    document.getElementById('job-title-display').innerText = applicationData.title || 'Job Application';
    document.getElementById('job-company-display').innerText = applicationData.company || '';
    document.getElementById('job-logo').innerText = (applicationData.company || 'J')[0].toUpperCase();
    document.getElementById('job-url-link').href = applicationData.job_url || '#';

    const badge = document.getElementById('app-status-badge');
    badge.innerText = applicationData.status;
    const badgeMap = { draft: 'badge-gray', review: 'badge-yellow', submitting: 'badge-blue', submitted: 'badge-green', failed: 'badge-red' };
    badge.className = `badge ${badgeMap[applicationData.status] || 'badge-gray'}`;

    // Fill form fields from form_data
    const fd = applicationData.form_data || {};
    document.getElementById('field-first-name').value = fd.first_name || '';
    document.getElementById('field-last-name').value = fd.last_name || '';
    document.getElementById('field-email').value = fd.email || '';
    document.getElementById('field-phone').value = fd.phone || '';
    document.getElementById('field-location').value = fd.location || '';
    document.getElementById('field-linkedin').value = fd.linkedin || '';
    document.getElementById('field-github').value = fd.github || '';
    document.getElementById('field-portfolio').value = fd.portfolio || '';
    document.getElementById('field-experience').value = fd.experience_years || 0;
    document.getElementById('field-notice').value = fd.notice_period || 0;
    document.getElementById('field-curr-sal').value = fd.current_salary || '';
    document.getElementById('field-exp-sal').value = fd.expected_salary || '';
    document.getElementById('field-relocate').value = fd.willing_to_relocate || 'No';
    document.getElementById('field-cover-letter').value = applicationData.cover_letter || '';
    document.getElementById('field-review-notes').value = applicationData.review_notes || '';

    // Resume section
    if (fd.resume_url) {
      document.getElementById('resume-active').style.display = 'block';
      document.getElementById('resume-missing').style.display = 'none';
      const filename = fd.resume_url.substring(fd.resume_url.lastIndexOf('/') + 1);
      document.getElementById('resume-name').innerText = filename;
    }

    // Q&A Items
    renderQAItems(applicationData.custom_qa || []);

    // If already submitting or submitted, show status
    if (applicationData.status === 'submitting') {
      showSubmissionStatus();
      startPolling();
    } else if (applicationData.status === 'submitted') {
      showSuccessModal();
    } else if (applicationData.status === 'failed') {
      showToast(`Previous submission failed: ${applicationData.error_message || 'Unknown error'}`, 'error', 6000);
    }

  } catch (err) {
    console.error(err);
    showToast('Error loading application data.', 'error');
  }
}

function renderQAItems(qaList) {
  const container = document.getElementById('qa-review-container');
  container.innerHTML = '';

  if (!qaList || qaList.length === 0) {
    container.innerHTML = '<p style="font-size:13px; color:var(--text-muted);">No standard Q&A detected for this form.</p>';
    return;
  }

  qaList.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'qa-item';
    div.innerHTML = `
      <div class="qa-question">${item.question}</div>
      ${item.type === 'yesno'
        ? `<div class="qa-options" data-idx="${idx}">
             <div class="qa-option ${item.answer === 'Yes' ? 'selected' : ''}" onclick="selectQAOption(this, ${idx}, 'Yes')">Yes</div>
             <div class="qa-option ${item.answer === 'No' ? 'selected' : ''}" onclick="selectQAOption(this, ${idx}, 'No')">No</div>
           </div>`
        : `<input type="text" class="form-control" value="${item.answer || ''}" oninput="updateQAText(${idx}, this.value)" style="margin-top:8px;">`
      }
    `;
    container.appendChild(div);
  });
}

function selectQAOption(el, idx, value) {
  const opts = el.parentElement.querySelectorAll('.qa-option');
  opts.forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  if (applicationData.custom_qa && applicationData.custom_qa[idx]) {
    applicationData.custom_qa[idx].answer = value;
  }
}

function updateQAText(idx, value) {
  if (applicationData.custom_qa && applicationData.custom_qa[idx]) {
    applicationData.custom_qa[idx].answer = value;
  }
}

// Build current form_data from UI
function buildFormData() {
  return {
    first_name: document.getElementById('field-first-name').value.trim(),
    last_name: document.getElementById('field-last-name').value.trim(),
    full_name: `${document.getElementById('field-first-name').value.trim()} ${document.getElementById('field-last-name').value.trim()}`.trim(),
    email: document.getElementById('field-email').value.trim(),
    phone: document.getElementById('field-phone').value.trim(),
    location: document.getElementById('field-location').value.trim(),
    linkedin: document.getElementById('field-linkedin').value.trim(),
    github: document.getElementById('field-github').value.trim(),
    portfolio: document.getElementById('field-portfolio').value.trim(),
    experience_years: document.getElementById('field-experience').value,
    notice_period: document.getElementById('field-notice').value,
    current_salary: document.getElementById('field-curr-sal').value,
    expected_salary: document.getElementById('field-exp-sal').value,
    willing_to_relocate: document.getElementById('field-relocate').value,
    resume_url: applicationData.form_data?.resume_url || ''
  };
}

async function saveReviewEdits() {
  try {
    const res = await api.put(`/applications/${applicationId}`, {
      form_data: buildFormData(),
      custom_qa: applicationData.custom_qa,
      cover_letter: document.getElementById('field-cover-letter').value.trim(),
      review_notes: document.getElementById('field-review-notes').value.trim()
    });
    if (res.success) showToast('Draft saved successfully!', 'success');
    else showToast('Failed to save draft.', 'error');
  } catch (err) {
    showToast('Save error.', 'error');
  }
}

async function confirmAndSubmit() {
  if (!confirm('Are you sure all details are correct? Playwright will now open a browser and submit this application automatically.')) return;

  const submitBtn = document.getElementById('confirm-submit-btn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Submitting...';

  // Save edits first
  await saveReviewEdits();

  try {
    const res = await api.post(`/applications/${applicationId}/submit`, {});
    if (res.success) {
      showToast('Automation started! Browser is filling the form...', 'info', 5000);
      showSubmissionStatus();
      startPolling();
    } else {
      showToast(res.message || 'Failed to start automation.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '🚀 Confirm & Submit Application';
    }
  } catch (err) {
    showToast('Could not reach automation service.', 'error');
    submitBtn.disabled = false;
    submitBtn.innerHTML = '🚀 Confirm & Submit Application';
  }
}

function showSubmissionStatus() {
  document.getElementById('submission-status').style.display = 'block';
  document.getElementById('confirm-submit-btn').style.display = 'none';
  
  // Animate progress bar
  let pct = 20;
  const interval = setInterval(() => {
    pct = Math.min(pct + Math.random() * 12, 90);
    document.getElementById('submission-progress').style.width = `${pct}%`;
  }, 1500);
  window._progressInterval = interval;
}

function startPolling() {
  pollingInterval = setInterval(async () => {
    try {
      const res = await api.get(`/applications/${applicationId}/status`);
      if (res.status === 'submitted') {
        clearInterval(pollingInterval);
        clearInterval(window._progressInterval);
        document.getElementById('submission-progress').style.width = '100%';
        document.getElementById('status-heading').innerText = 'Application Submitted!';
        document.getElementById('status-message').innerText = 'Your application was successfully submitted. Check your inbox for a confirmation.';
        document.getElementById('status-spinner').style.display = 'none';
        setTimeout(() => showSuccessModal(), 1500);
      } else if (res.status === 'failed') {
        clearInterval(pollingInterval);
        clearInterval(window._progressInterval);
        document.getElementById('status-heading').innerText = 'Submission Failed';
        document.getElementById('status-message').innerText = res.error_message || res.sess_error || 'The automation engine encountered an error.';
        document.getElementById('status-spinner').style.display = 'none';
        showToast('Automation failed. Check the error above.', 'error');
        document.getElementById('confirm-submit-btn').style.display = 'inline-flex';
        document.getElementById('confirm-submit-btn').disabled = false;
        document.getElementById('confirm-submit-btn').innerHTML = '🔄 Retry Submission';
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }, 4000);
}

function showSuccessModal() {
  document.getElementById('success-modal').classList.add('open');
}

async function aiGenerateAnswers() {
  const btn = document.getElementById('ai-fill-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';
  }
  showToast('Groq AI is analyzing the page & resume...', 'info');
  try {
    const res = await api.post(`/applications/${applicationId}/ai-answers`, { regenerate_cover_letter: true });
    if (res.success) {
      showToast('AI answers generated successfully!', 'success');
      // Reload application details to populate generated answers
      await loadApplicationData(applicationId);
    } else {
      showToast(res.message || 'Failed to generate AI answers.', 'error');
    }
  } catch (err) {
    showToast('Error calling AI generation API.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '🔄 Re-generate AI Answers';
    }
  }
}

async function aiAutoSubmit() {
  const aiSubmitBtn = document.getElementById('ai-submit-btn');
  aiSubmitBtn.disabled = true;
  aiSubmitBtn.innerHTML = '<span class="spinner"></span> AI Submitting...';

  try {
    // Generate AI answers first
    showToast('1/2 Generating AI Answers...', 'info');
    const aiRes = await api.post(`/applications/${applicationId}/ai-answers`, { regenerate_cover_letter: true });
    if (!aiRes.success) {
      showToast('Failed to pre-fill answers with AI. Proceeding with existing details.', 'warn');
    } else {
      // Reload UI to show the generated values
      await loadApplicationData(applicationId);
    }

    showToast('2/2 Triggering automatic Playwright submission...', 'info');
    
    // Save draft edits first (including any auto-generated content)
    await saveReviewEdits();

    const res = await api.post(`/applications/${applicationId}/submit`, {});
    if (res.success) {
      showToast('Automation started! Playwright is active.', 'success');
      showSubmissionStatus();
      // Hide other submit buttons during active submission
      const confirmBtn = document.getElementById('confirm-submit-btn');
      if (confirmBtn) confirmBtn.style.display = 'none';
      aiSubmitBtn.style.display = 'none';
      startPolling();
    } else {
      showToast(res.message || 'Failed to start automation.', 'error');
      aiSubmitBtn.disabled = false;
      aiSubmitBtn.innerHTML = '🤖 AI Auto-Submit';
    }
  } catch (err) {
    showToast('Could not reach automation service.', 'error');
    aiSubmitBtn.disabled = false;
    aiSubmitBtn.innerHTML = '🤖 AI Auto-Submit';
  }
}
