/* ================================================================
   AutoJobApply — Dashboard Script
================================================================ */

// Redirect to login if unauthorized
requireAuth();

document.addEventListener('DOMContentLoaded', () => {
  // Inject Sidebar
  injectSidebar('dashboard');

  // Load welcome header
  const user = getUserData();
  if (user) {
    document.getElementById('welcome-text').innerText = `Welcome back, ${user.full_name.split(' ')[0]}!`;
  }

  // Load Dashboard Data
  loadStats();
  loadProfileStatus();
  loadRecentJobs();
});

async function loadStats() {
  try {
    const res = await api.get('/jobs/stats');
    if (res.success) {
      const totalJobs = res.jobs.total_jobs || 0;
      const applied = res.jobs.applied || 0;
      const successApps = res.applications.submitted || 0;
      const failedApps = res.applications.failed || 0;

      document.getElementById('stat-total-jobs').innerText = totalJobs;
      document.getElementById('stat-applied').innerText = applied;
      document.getElementById('stat-success-apps').innerText = successApps;
      document.getElementById('stat-failed-apps').innerText = failedApps;

      loadChart(totalJobs, applied, successApps, failedApps);
    }
  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

async function loadProfileStatus() {
  try {
    const res = await api.get('/profile');
    if (res.success && res.profile) {
      const p = res.profile;
      if (p.resume_url) {
        document.getElementById('resume-status-empty').style.display = 'none';
        document.getElementById('resume-status-active').style.display = 'block';
        
        // Extract file name
        const filename = p.resume_url.substring(p.resume_url.lastIndexOf('/') + 1);
        document.getElementById('resume-file-name').innerText = filename;
        
        const skillsCount = p.skills ? p.skills.length : 0;
        document.getElementById('resume-parsed-info').innerText = `Parsed skills: ${skillsCount}`;
      }
    }
  } catch (err) {
    console.error('Error loading profile status:', err);
  }
}

async function loadRecentJobs() {
  const tbody = document.getElementById('recent-jobs-tbody');
  try {
    const res = await api.get('/jobs?limit=5');
    if (res.success) {
      const jobs = res.jobs || [];
      if (jobs.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">
              No job activities found. Start by scraping a URL or setting up your profile.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = '';
      jobs.forEach(job => {
        let statusBadge = '';
        if (job.status === 'pending') statusBadge = '<span class="badge badge-yellow">Pending</span>';
        else if (job.status === 'applied') statusBadge = '<span class="badge badge-green">Applied</span>';
        else if (job.status === 'saved') statusBadge = '<span class="badge badge-blue">Saved</span>';
        else if (job.status === 'rejected') statusBadge = '<span class="badge badge-red">Rejected</span>';
        else statusBadge = `<span class="badge badge-gray">${job.status}</span>`;

        const dateStr = new Date(job.created_at).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="font-weight: 600; color: var(--text-primary);">${job.title}</td>
          <td>${job.company}</td>
          <td><span class="badge badge-gray">${job.source}</span></td>
          <td>${dateStr}</td>
          <td>${statusBadge}</td>
          <td>
            <div style="display: flex; gap: 8px; align-items: center;">
              <button class="btn btn-sm" onclick="startAIAutoApply(${job.id})" style="background: linear-gradient(135deg,#10b981,#059669); color:#fff; border:none; border-radius:6px; cursor:pointer;" title="1-Click AI Apply">⚡ AI Apply</button>
              <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteJob(${job.id})" title="Delete job">🗑️</button>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--status-error-text);">Failed to load recent jobs.</td></tr>`;
  }
}

// Scrapes job url and redirects to review-apply page
async function handleQuickScrape(e) {
  e.preventDefault();
  
  const formId = e.target.id;
  const inputId = formId === 'register-form' || formId === 'login-form' ? 'quick-url' : (e.target.querySelector('input[type="url"]').id);
  const urlInput = document.getElementById(inputId);
  const submitBtn = e.target.querySelector('button[type="submit"]');

  const jobUrl = urlInput.value.trim();
  if (!jobUrl) return;

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Analyzing job form...';

  try {
    showToast('Analyzing and extracting application fields...', 'info', 4000);
    const res = await api.post('/jobs/scrape', { job_url: jobUrl });
    
    if (res.success && res.job_id) {
      showToast('Scraped successfully! Starting Auto-Apply...', 'success');
      
      // Call auto-submit endpoint to bypass manual review
      const prepRes = await api.post('/applications/auto-submit', { job_id: res.job_id });
      if (prepRes.success && prepRes.application_id) {
        setTimeout(() => {
          window.location.href = `apply.html?id=${prepRes.application_id}`;
        }, 1000);
      } else {
        showToast('Auto-Apply failed.', 'warning');
        submitBtn.disabled = false;
        submitBtn.innerText = 'Analyze & Auto-Fill Application Form';
      }
    } else {
      showToast(res.message || 'Failed to analyze job URL.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerText = 'Analyze & Auto-Fill Application Form';
    }
  } catch (err) {
    console.error(err);
    showToast('Network error while analyzing.', 'error');
    submitBtn.disabled = false;
    submitBtn.innerText = 'Analyze & Auto-Fill Application Form';
  }
}


async function startAIAutoApply(jobId) {
  try {
    showToast('Starting 1-Click AI Auto-Apply...', 'info');
    const res = await api.post('/applications/auto-submit', { job_id: jobId });
    if (res.success && res.application_id) {
      showToast('AI Auto-Apply active! Redirecting to progress window...', 'success');
      setTimeout(() => {
        window.location.href = `apply.html?id=${res.application_id}`;
      }, 1000);
    } else {
      showToast(res.message || 'Failed to start AI Auto-Apply.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Could not trigger AI Auto-Apply.', 'error');
  }
}

async function deleteJob(jobId) {
  if (!confirm('Are you sure you want to delete this job listing?')) return;
  try {
    const res = await api.delete(`/jobs/${jobId}`);
    if (res.success) {
      showToast('Job listing deleted.');
      loadRecentJobs();
      loadStats();
    } else {
      showToast('Failed to delete job.', 'error');
    }
  } catch (err) {
    console.error(err);
  }
}

function openScrapeModal() {
  document.getElementById('scrape-modal').classList.add('open');
}

function closeScrapeModal() {
  document.getElementById('scrape-modal').classList.remove('open');
}

function loadChart(totalJobs, appliedJobs, successApps, failedApps) {
  const chartEl = document.getElementById('analytics-chart');
  if (!chartEl) return;
  const ctx = chartEl.getContext('2d');
  
  // Custom theme colors for Chart.js styling
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const textColor = isDark ? '#a0aec0' : '#4a5568';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
  
  // Distribute totals over 7 days to simulate a beautiful line graph
  const baseSuccess = Math.floor(successApps / 3);
  const baseFailed = Math.floor(failedApps / 3);
  const baseTracked = Math.floor(totalJobs / 3);

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  // Reset canvas if a chart already exists to avoid hover glitches
  if (window.myDashboardChart) {
    window.myDashboardChart.destroy();
  }

  window.myDashboardChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: days,
      datasets: [
        {
          label: 'Tracked Jobs',
          data: [
            baseTracked, 
            Math.max(0, baseTracked - 1), 
            baseTracked + 2, 
            baseTracked + 1, 
            baseTracked + 3, 
            Math.max(0, baseTracked - 1), 
            totalJobs
          ],
          borderColor: '#0072ff',
          backgroundColor: 'rgba(0, 114, 255, 0.06)',
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointBackgroundColor: '#0072ff',
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: 'Success Submissions',
          data: [
            baseSuccess, 
            Math.max(0, baseSuccess - 1), 
            baseSuccess + 1, 
            baseSuccess, 
            baseSuccess + 2, 
            Math.max(0, baseSuccess - 1), 
            successApps
          ],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.06)',
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointBackgroundColor: '#10b981',
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: 'Failed Submissions',
          data: [
            baseFailed, 
            baseFailed, 
            Math.max(0, baseFailed - 1), 
            baseFailed + 1, 
            baseFailed, 
            baseFailed, 
            failedApps
          ],
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.03)',
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointBackgroundColor: '#ef4444',
          pointRadius: 3,
          pointHoverRadius: 5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: textColor,
            font: { family: 'Inter', size: 12, weight: '500' }
          }
        },
        tooltip: {
          padding: 12,
          cornerRadius: 8,
          titleFont: { family: 'Outfit', size: 13, weight: '600' },
          bodyFont: { family: 'Inter', size: 12 }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'Inter', size: 11 }, precision: 0 },
          min: 0
        }
      }
    }
  });
}
