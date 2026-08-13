document.addEventListener('DOMContentLoaded', () => {
  
  // --- Theme Toggle Switcher ---
  const themeBtn = document.getElementById('theme-toggle');
  const savedTheme = localStorage.getItem('sams_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (themeBtn) {
    themeBtn.textContent = savedTheme === 'light' ? '☀️ Light' : '🌙 Dark';
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('sams_theme', next);
      themeBtn.textContent = next === 'light' ? '☀️ Light' : '🌙 Dark';
    });
  }

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

  // --- AJAX File Upload Processing ---
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

  // --- WebRTC Camera Scanner Stream ---
  const videoElem = document.getElementById('webcam-video');
  const captureBtn = document.getElementById('capture-btn');
  const cameraSelect = document.getElementById('camera-select');
  const scannerAlert = document.getElementById('scanner-alert');

  if (videoElem && captureBtn) {
    let currentStream = null;

    const startCamera = async (deviceId) => {
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
      }

      const constraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'environment' }
      };

      try {
        currentStream = await navigator.mediaDevices.getUserMedia(constraints);
        videoElem.srcObject = currentStream;
      } catch (err) {
        if (scannerAlert) {
          scannerAlert.textContent = 'Unable to access camera. Please allow camera permissions.';
          scannerAlert.style.display = 'block';
        }
      }
    };

    const enumerateCameras = async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        if (cameraSelect) {
          cameraSelect.innerHTML = videoDevices.map((d, i) => `<option value="${d.deviceId}">${d.label || 'Camera ' + (i+1)}</option>`).join('');
          if (videoDevices.length > 0) startCamera(videoDevices[0].deviceId);
        }
      } catch (e) {
        startCamera();
      }
    };

    if (cameraSelect) {
      cameraSelect.addEventListener('change', () => startCamera(cameraSelect.value));
    }

    enumerateCameras();

    // Snapshot Capture Handler
    captureBtn.addEventListener('click', async () => {
      const canvas = document.getElementById('snapshot-canvas');
      if (!canvas || !videoElem.videoWidth) return;

      canvas.width = videoElem.videoWidth;
      canvas.height = videoElem.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoElem, 0, 0);

      const imageDataUrl = canvas.toDataURL('image/jpeg', 0.95);

      captureBtn.disabled = true;
      captureBtn.textContent = 'Processing Live Snapshot...';

      try {
        const payload = {
          image_data: imageDataUrl,
          signature_ratio: parseFloat(document.getElementById('webcam-ratio')?.value || 0.60),
          pixel_threshold: parseInt(document.getElementById('webcam-thresh')?.value || 100)
        };

        const res = await fetch('/api/webcam/process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const json = await res.json();

        if (json.success) {
          window.location.href = json.redirect_url;
        } else {
          if (scannerAlert) {
            scannerAlert.textContent = json.error || 'Failed to analyze snapshot.';
            scannerAlert.style.display = 'block';
          }
          captureBtn.disabled = false;
          captureBtn.textContent = '📸 Capture & Analyze Sheet';
        }
      } catch (err) {
        if (scannerAlert) {
          scannerAlert.textContent = 'Server error processing live snapshot.';
          scannerAlert.style.display = 'block';
        }
        captureBtn.disabled = false;
        captureBtn.textContent = '📸 Capture & Analyze Sheet';
      }
    });
  }

  // --- Student Roster CRUD Handlers ---
  const addStudentForm = document.getElementById('add-student-form');
  if (addStudentForm) {
    addStudentForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(addStudentForm);
      const data = Object.fromEntries(formData.entries());

      try {
        const res = await fetch('/api/students/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const json = await res.json();
        if (json.success) {
          window.location.reload();
        } else {
          alert(json.error || 'Failed to add student');
        }
      } catch (err) {
        alert('Server error adding student');
      }
    });
  }

  document.querySelectorAll('.btn-delete-student').forEach(btn => {
    btn.addEventListener('click', async () => {
      const studentId = btn.getAttribute('data-student-id');
      if (!studentId || !confirm('Are you sure you want to delete this student from roster?')) return;

      try {
        const res = await fetch(`/api/students/${studentId}/delete`, { method: 'POST' });
        const json = await res.json();
        if (json.success) {
          document.getElementById(`student-row-${studentId}`)?.remove();
        }
      } catch (err) {
        alert('Failed to delete student');
      }
    });
  });

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
