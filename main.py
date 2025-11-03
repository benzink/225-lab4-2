from flask import Flask, request, render_template_string, redirect, url_for, flash, get_flashed_messages
import sqlite3
import os
import math

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Database file path
DATABASE = '/nfs/demo.db'
PER_PAGE_DEFAULT = 10

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            );
        ''')
        db.commit()
        db.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    # POST handlers — PRG pattern
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete':
            contact_id = request.form.get('contact_id')
            if contact_id:
                db = get_db()
                db.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
                db.commit(); db.close()
                flash('Contact deleted successfully.', 'success')
            return redirect(url_for('index'))

        if action == 'update':
            contact_id = request.form.get('contact_id')
            name = request.form.get('name')
            phone = request.form.get('phone')
            if contact_id and name and phone:
                db = get_db()
                db.execute('UPDATE contacts SET name=?, phone=? WHERE id=?', (name, phone, contact_id))
                db.commit(); db.close()
                flash('Contact updated.', 'success')
            else:
                flash('Missing fields for update.', 'danger')
            return redirect(url_for('index'))

        # default → add
        name = request.form.get('name')
        phone = request.form.get('phone')
        if name and phone:
            db = get_db()
            db.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
            db.commit(); db.close()
            flash('Contact added successfully.', 'success')
        else:
            flash('Missing name or phone number.', 'danger')
        return redirect(url_for('index'))

    # GET — pagination
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = max(int(request.args.get('per', PER_PAGE_DEFAULT)), 1)
    except ValueError:
        per_page = PER_PAGE_DEFAULT
    offset = (page - 1) * per_page

    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM contacts').fetchone()[0]
    contacts = db.execute(
        'SELECT * FROM contacts ORDER BY id DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    db.close()

    pages = max(1, math.ceil(total / per_page))
    has_prev = page > 1
    has_next = page < pages

    return render_template_string("""
<!doctype html>
<html lang="en" data-bs-theme="auto" id="html-root">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Contacts</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { padding-top: 2rem; }
      .card { border-radius: 1rem; }
      .table thead th { position: sticky; top: 0; background: var(--bs-body-bg); z-index: 1; }
      .form-card { max-width: 780px; }
      .fade-enter { animation: fadeIn .25s ease-in; }
      @keyframes fadeIn { from { opacity: .3 } to { opacity: 1 } }
      .pagination { gap: .25rem; }
      .mode-toggle { white-space: nowrap; }
    </style>
  </head>
  <body>
    <div class="container">
      <header class="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h1 class="h3 mb-1">Contacts</h1>
          <p class="text-secondary mb-0">Add, search, edit, and manage your contacts.</p>
        </div>
        <div class="d-flex align-items-center gap-2">
          <div class="input-group input-group-sm" title="Items per page">
            <span class="input-group-text">Per page</span>
            <input id="per-input" type="number" min="1" class="form-control" value="{{ per_page }}">
            <button id="per-apply" class="btn btn-outline-secondary">Apply</button>
          </div>
          <button id="modeBtn" class="btn btn-sm btn-outline-primary mode-toggle" type="button">Toggle dark mode</button>
        </div>
      </header>

      <!-- Flash messages -->
      {% with msgs = get_flashed_messages(with_categories=True) %}
        {% if msgs %}
          <div class="mb-3">
            {% for category, m in msgs %}
              {% set bs = 'success' if category=='success' else 'danger' if category=='danger' else 'primary' %}
              <div class="alert alert-{{ bs }} alert-dismissible fade show fade-enter" role="alert">
                {{ m }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <!-- Add form -->
      <div class="card shadow-sm form-card mb-4">
        <div class="card-body">
          <h2 class="h5 mb-3">Add Contact</h2>
          <form method="POST" action="{{ url_for('index') }}" class="row g-3">
            <input type="hidden" name="action" value="add">
            <div class="col-md-6">
              <label for="name" class="form-label">Name</label>
              <input class="form-control" id="name" name="name" required>
            </div>
            <div class="col-md-6">
              <label for="phone" class="form-label">Phone</label>
              <input class="form-control" id="phone" name="phone" required placeholder="555-0123"
                     pattern="^[0-9()+\\-\\s]+$" title="Digits, spaces, (), - and + only">
            </div>
            <div class="col-12">
              <button class="btn btn-primary" type="submit">Add Contact</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Search -->
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h2 class="h5 m-0">All Contacts</h2>
        <input id="filter" class="form-control" style="max-width: 280px;" placeholder="Search…">
      </div>

      <!-- Contacts table -->
      <div class="card shadow-sm mb-3">
        <div class="table-responsive">
          <table class="table align-middle mb-0">
            <thead>
              <tr>
                <th style="width: 8ch">ID</th>
                <th style="width: 50%">Name</th>
                <th style="width: 30%">Phone</th>
                <th class="text-end" style="width: 12%">Actions</th>
              </tr>
            </thead>
            <tbody id="rows">
              {% for c in contacts %}
              <tr>
                <td class="id text-secondary">{{ c['id'] }}</td>
                <td class="name">{{ c['name'] }}</td>
                <td class="phone text-nowrap">{{ c['phone'] }}</td>
                <td class="text-end">
                  <div class="d-inline-flex gap-2">
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-secondary"
                      data-bs-toggle="modal"
                      data-bs-target="#editModal"
                      data-id="{{ c['id'] }}"
                      data-name="{{ c['name'] }}"
                      data-phone="{{ c['phone'] }}"
                    >Edit</button>

                    <form method="POST" action="{{ url_for('index') }}" onsubmit="return confirm('Delete this contact?')">
                      <input type="hidden" name="contact_id" value="{{ c['id'] }}">
                      <input type="hidden" name="action" value="delete">
                      <button class="btn btn-sm btn-outline-danger">Delete</button>
                    </form>
                  </div>
                </td>
              </tr>
              {% endfor %}
              {% if not contacts %}
              <tr><td colspan="4" class="text-center text-secondary py-4">No contacts found.</td></tr>
              {% endif %}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <nav aria-label="Contacts pagination" class="d-flex justify-content-between align-items-center">
        <div class="text-secondary small">
          Page <strong>{{ page }}</strong> of <strong>{{ pages }}</strong> · {{ total }} total
        </div>
        <ul class="pagination mb-0">
          <li class="page-item {% if not has_prev %}disabled{% endif %}">
            <a class="page-link" href="{{ url_for('index', page=page-1, per=per_page) if has_prev else '#' }}">Previous</a>
          </li>
          {# show a small window of pages #}
          {% for p in range(max(1, page-2), min(pages, page+2)+1) %}
            <li class="page-item {% if p==page %}active{% endif %}">
              <a class="page-link" href="{{ url_for('index', page=p, per=per_page) }}">{{ p }}</a>
            </li>
          {% endfor %}
          <li class="page-item {% if not has_next %}disabled{% endif %}">
            <a class="page-link" href="{{ url_for('index', page=page+1, per=per_page) if has_next else '#' }}">Next</a>
          </li>
        </ul>
      </nav>

      <footer class="py-4 text-center text-secondary small">Flask Contacts Demo</footer>
    </div>

    <!-- Edit Modal -->
    <div class="modal fade" id="editModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <form method="POST" action="{{ url_for('index') }}" class="modal-content">
          <input type="hidden" name="action" value="update">
          <input type="hidden" name="contact_id" id="edit-id">
          <div class="modal-header">
            <h5 class="modal-title">Edit Contact</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body row g-3">
            <div class="col-12">
              <label class="form-label">Name</label>
              <input class="form-control" name="name" id="edit-name" required>
            </div>
            <div class="col-12">
              <label class="form-label">Phone</label>
              <input class="form-control" name="phone" id="edit-phone" required
                     pattern="^[0-9()+\\-\\s]+$" title="Digits, spaces, (), - and + only">
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Cancel</button>
            <button class="btn btn-primary" type="submit">Save changes</button>
          </div>
        </form>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
      // Dark mode toggle with persistence
      const root = document.getElementById('html-root');
      const modeBtn = document.getElementById('modeBtn');
      const stored = localStorage.getItem('theme');
      if (stored) root.setAttribute('data-bs-theme', stored);
      modeBtn?.addEventListener('click', () => {
        const cur = root.getAttribute('data-bs-theme') || 'light';
        const next = cur === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-bs-theme', next);
        localStorage.setItem('theme', next);
      });

      // Client-side filter
      const filter = document.getElementById('filter');
      const rows = document.getElementById('rows');
      filter?.addEventListener('input', () => {
        const q = filter.value.toLowerCase();
        for (const tr of rows.querySelectorAll('tr')) {
          const name = tr.querySelector('.name')?.textContent.toLowerCase() || '';
          const phone = tr.querySelector('.phone')?.textContent.toLowerCase() || '';
          tr.style.display = (name.includes(q) || phone.includes(q)) ? '' : 'none';
        }
      });

      // Edit modal populate
      const editModal = document.getElementById('editModal');
      editModal?.addEventListener('show.bs.modal', (ev) => {
        const btn = ev.relatedTarget;
        document.getElementById('edit-id').value   = btn.getAttribute('data-id');
        document.getElementById('edit-name').value = btn.getAttribute('data-name');
        document.getElementById('edit-phone').value= btn.getAttribute('data-phone');
      });

      // Per-page apply (reload with new per param)
      document.getElementById('per-apply')?.addEventListener('click', () => {
        const per = document.getElementById('per-input').value || {{ per_page }};
        const url = new URL(window.location);
        url.searchParams.set('per', per);
        url.searchParams.set('page', '1');
        window.location = url;
      });
    </script>
  </body>
</html>
    """,
    get_flashed_messages=get_flashed_messages,
    contacts=contacts,
    page=page, pages=pages, per_page=per_page, has_prev=has_prev, has_next=has_next, total=total)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()
    app.run(debug=True, host='0.0.0.0', port=port)
