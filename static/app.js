/* ═══════════════════════════════════════════════════════════════
   TaskFlow — Frontend JavaScript
   Handles: REST API calls, WebSocket, task CRUD, filters, toast
   ═══════════════════════════════════════════════════════════════ */

// ── WebSocket ──────────────────────────────────────────────────
const socket = io();

socket.on('connect', () => {
  updateWsBadge(true);
  showToast('⚡ Real-time connected!', 'info');
});

socket.on('disconnect', () => {
  updateWsBadge(false);
});

socket.on('task_added', (task) => {
  showToast(`✅ New task added: "${task.title}"`, 'success');
  refreshAnalytics();
});

socket.on('task_updated', (task) => {
  showToast(`✏️ Task updated: "${task.title}"`, 'info');
  refreshAnalytics();
});

socket.on('task_deleted', (data) => {
  showToast(`🗑️ Task #${data.id} deleted`, 'info');
  refreshAnalytics();
});

function updateWsBadge(connected) {
  const badge  = document.getElementById('wsBadge');
  const status = document.getElementById('wsStatus');
  if (!badge) return;
  if (connected) {
    badge.classList.add('connected');
    status.textContent = 'Live';
  } else {
    badge.classList.remove('connected');
    status.textContent = 'Disconnected';
  }
}

// ── Modal ──────────────────────────────────────────────────────
function openModal() {
  const modal = document.getElementById('addModal');
  if (!modal) return;
  resetForm();
  document.getElementById('modalTitle').textContent  = 'New Task';
  document.getElementById('btn-submit-task').textContent = 'Add Task';
  modal.classList.remove('hidden');
  document.getElementById('taskTitle').focus();
}

function openEditModal(id, title, description, priority, status) {
  const modal = document.getElementById('addModal');
  if (!modal) return;
  document.getElementById('editTaskId').value       = id;
  document.getElementById('taskTitle').value        = title;
  document.getElementById('taskDesc').value         = description;
  document.getElementById('taskPriority').value     = priority;
  document.getElementById('taskStatus').value       = status;
  document.getElementById('modalTitle').textContent = 'Edit Task';
  document.getElementById('btn-submit-task').textContent = 'Save Changes';
  modal.classList.remove('hidden');
}

function closeModal(event) {
  const modal = document.getElementById('addModal');
  if (!modal) return;
  if (!event || event.target === modal) {
    modal.classList.add('hidden');
    resetForm();
  }
}

function resetForm() {
  const form = document.getElementById('taskForm');
  if (form) form.reset();
  const editId = document.getElementById('editTaskId');
  if (editId) editId.value = '';
}

// ── Task CRUD ──────────────────────────────────────────────────
async function submitTask(event) {
  event.preventDefault();
  const editId  = document.getElementById('editTaskId').value;
  const payload = {
    title:       document.getElementById('taskTitle').value.trim(),
    description: document.getElementById('taskDesc').value.trim(),
    priority:    document.getElementById('taskPriority').value,
    status:      document.getElementById('taskStatus').value,
  };

  if (!payload.title) return showToast('Title is required!', 'error');

  try {
    let res, task;
    if (editId) {
      res  = await fetch(`/api/tasks/${editId}`, { method: 'PUT',  headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      task = await res.json();
      if (res.ok) updateTaskCard(task);
    } else {
      res  = await fetch('/api/tasks',           { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      task = await res.json();
      if (res.ok) addTaskCard(task);
    }

    if (!res.ok) { showToast(task.error || 'Something went wrong', 'error'); return; }
    closeModal();
    await refreshAnalytics();
  } catch (err) {
    showToast('Network error — try again', 'error');
  }
}

async function deleteTask(id) {
  if (!confirm('Delete this task?')) return;
  try {
    const res = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
    if (res.ok) {
      const card = document.getElementById(`task-${id}`);
      if (card) { card.style.opacity = '0'; card.style.transform = 'translateX(20px)'; setTimeout(() => card.remove(), 200); }
      await refreshAnalytics();
      showToast('Task deleted', 'info');
    }
  } catch { showToast('Error deleting task', 'error'); }
}

async function toggleStatus(id, currentStatus) {
  const nextStatus = currentStatus === 'completed' ? 'pending' : 'completed';
  try {
    const res  = await fetch(`/api/tasks/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: nextStatus }) });
    const task = await res.json();
    if (res.ok) {
      updateTaskCard(task);
      await refreshAnalytics();
    }
  } catch { showToast('Error updating task', 'error'); }
}

// ── DOM helpers ────────────────────────────────────────────────
function addTaskCard(task) {
  const list  = document.getElementById('taskList');
  const empty = document.getElementById('emptyState');
  if (empty) empty.remove();

  const card = createTaskCardEl(task);
  list.insertBefore(card, list.firstChild);
}

function updateTaskCard(task) {
  const card = document.getElementById(`task-${task.id}`);
  if (!card) return;
  card.dataset.status   = task.status;
  card.dataset.priority = task.priority;

  const titleEl = document.getElementById(`title-${task.id}`);
  const descEl  = document.getElementById(`desc-${task.id}`);
  const checkEl = document.getElementById(`check-${task.id}`);

  if (titleEl) {
    titleEl.textContent = task.title;
    titleEl.className   = 'task-title' + (task.status === 'completed' ? ' strikethrough' : '');
  }
  if (descEl) descEl.textContent = task.description;
  if (checkEl) {
    checkEl.className   = 'task-check' + (task.status === 'completed' ? ' checked' : '');
    checkEl.textContent = task.status === 'completed' ? '✓' : '○';
    checkEl.setAttribute('onclick', `toggleStatus(${task.id}, '${task.status}')`);
  }

  // Refresh badges
  const metaEl = card.querySelector('.task-meta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span class="badge badge-priority-${task.priority}">${task.priority}</span>
      <span class="badge badge-status-${task.status}">${task.status.replace('_',' ')}</span>
      <span class="task-date">${task.created_date}</span>
    `;
  }
}

function createTaskCardEl(task) {
  const div = document.createElement('div');
  div.className    = 'task-card';
  div.id           = `task-${task.id}`;
  div.dataset.id   = task.id;
  div.dataset.status   = task.status;
  div.dataset.priority = task.priority;
  div.innerHTML = `
    <div class="task-left">
      <button class="task-check ${task.status === 'completed' ? 'checked' : ''}"
              onclick="toggleStatus(${task.id}, '${task.status}')"
              id="check-${task.id}">
        ${task.status === 'completed' ? '✓' : '○'}
      </button>
      <div class="task-body">
        <p class="task-title ${task.status === 'completed' ? 'strikethrough' : ''}" id="title-${task.id}">${escHtml(task.title)}</p>
        ${task.description ? `<p class="task-desc" id="desc-${task.id}">${escHtml(task.description)}</p>` : ''}
        <div class="task-meta">
          <span class="badge badge-priority-${task.priority}">${task.priority}</span>
          <span class="badge badge-status-${task.status}">${task.status.replace('_', ' ')}</span>
          <span class="task-date">${task.created_date}</span>
        </div>
      </div>
    </div>
    <div class="task-actions">
      <button class="btn-icon" onclick="openEditModal(${task.id}, '${escAttr(task.title)}', '${escAttr(task.description)}', '${task.priority}', '${task.status}')" id="edit-${task.id}">✏️</button>
      <button class="btn-icon btn-danger" onclick="deleteTask(${task.id})" id="delete-${task.id}">🗑️</button>
    </div>
  `;
  return div;
}

function escHtml(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escAttr(str) {
  return String(str ?? '').replace(/'/g, "\\'");
}

// ── Analytics refresh ──────────────────────────────────────────
async function refreshAnalytics() {
  try {
    const res  = await fetch('/api/analytics');
    const data = await res.json();

    setText('stat-total',      data.total_tasks);
    setText('stat-completed',  data.completed_tasks);
    setText('stat-pending',    data.pending_tasks);
    setText('stat-inprogress', data.in_progress_tasks);
    setText('stat-pct',        data.completion_percentage + '%');
    setText('progress-label',  data.completion_percentage + '%');
    setText('bp-high',         data.priority_breakdown.high);
    setText('bp-medium',       data.priority_breakdown.medium);
    setText('bp-low',          data.priority_breakdown.low);

    const fill = document.getElementById('progressFill');
    if (fill) fill.style.width = data.completion_percentage + '%';
  } catch { /* silent */ }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// ── Filters ────────────────────────────────────────────────────
function filterTasks() {
  const statusFilter   = document.getElementById('filterStatus')?.value   || 'all';
  const priorityFilter = document.getElementById('filterPriority')?.value || 'all';
  const cards = document.querySelectorAll('.task-card');

  cards.forEach(card => {
    const statusOk   = statusFilter   === 'all' || card.dataset.status   === statusFilter;
    const priorityOk = priorityFilter === 'all' || card.dataset.priority === priorityFilter;
    card.style.display = (statusOk && priorityOk) ? '' : 'none';
  });
}

// ── Toast ──────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, type = 'info') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className   = `toast ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add('hidden'), 3500);
}
