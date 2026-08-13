document.addEventListener('DOMContentLoaded', () => {
  // --- Drag and Drop File Upload Handlers ---
  const setupDropzone = (dropzoneId, inputId, previewId) => {
    const dropzone = document.getElementById(dropzoneId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    if (!dropzone || !input) return;

    dropzone.addEventListener('click', () => input.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        input.files = files;
        updatePreview(files[0], preview);
      }
    });

    input.addEventListener('change', () => {
      if (input.files.length > 0) {
        updatePreview(input.files[0], preview);
      }
    });
  };

  const updatePreview = (file, previewElem) => {
    if (previewElem) {
      previewElem.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      previewElem.style.display = 'inline-block';
    }
  };

  setupDropzone('dropzone-image', 'input-image', 'preview-image');
  setupDropzone('dropzone-xml', 'input-xml', 'preview-xml');

  // --- AJAX Form Processing ---
  const uploadForm = document.getElementById('upload-form');
  const uploadBtn = document.getElementById('submit-btn');
  const errorAlert = document.getElementById('upload-error');

  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (errorAlert) errorAlert.style.display = 'none';

      const formData = new FormData(uploadForm);
      if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Processing Computer Vision Pipeline...';
      }

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (result.success) {
          window.location.href = result.redirect_url;
        } else {
          if (errorAlert) {
            errorAlert.textContent = result.error || 'Failed to process files.';
            errorAlert.style.display = 'block';
          }
          if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Process Attendance';
          }
        }
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = 'An unexpected server error occurred.';
          errorAlert.style.display = 'block';
        }
        if (uploadBtn) {
          uploadBtn.disabled = false;
          uploadBtn.textContent = 'Process Attendance';
        }
      }
    });
  }

  // --- Attendance Record Status Toggle (AJAX) ---
  document.querySelectorAll('.status-badge').forEach(badge => {
    badge.addEventListener('click', async () => {
      const recordId = badge.getAttribute('data-record-id');
      if (!recordId) return;

      try {
        const res = await fetch(`/api/records/${recordId}/toggle`, { method: 'POST' });
        const json = await res.json();

        if (json.success) {
          const newStatus = json.data.new_status;
          badge.setAttribute('data-status', newStatus);

          if (newStatus === 'Present') {
            badge.className = 'status-badge present';
            badge.innerHTML = '✔ Present';
          } else {
            badge.className = 'status-badge absent';
            badge.innerHTML = '✖ Absent';
          }

          // Update header counter badges
          const presentStat = document.getElementById('stat-present');
          const absentStat = document.getElementById('stat-absent');
          if (presentStat) presentStat.textContent = json.data.present_count;
          if (absentStat) absentStat.textContent = json.data.absent_count;
        }
      } catch (e) {
        console.error('Failed to toggle status:', e);
      }
    });
  });

  // --- Image Pipeline Tab Switcher ---
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const activeContent = document.getElementById(`tab-${targetTab}`);
      if (activeContent) activeContent.classList.add('active');
    });
  });

  // --- Signature Crop Image Modal Zoom ---
  const modal = document.getElementById('image-modal');
  const modalImg = document.getElementById('modal-img');

  document.querySelectorAll('.crop-thumb').forEach(img => {
    img.addEventListener('click', () => {
      if (modal && modalImg) {
        modalImg.src = img.src;
        modal.classList.add('active');
      }
    });
  });

  if (modal) {
    modal.addEventListener('click', () => modal.classList.remove('active'));
  }

  // --- Client Table Search Filter ---
  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      document.querySelectorAll('#attendance-table tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }
});
