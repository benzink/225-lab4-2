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
    # Help with NFS: avoid immediate lock failures
    db.execute("PRAGMA busy_timeout = 3000")
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
    # --- POST handlers (PRG pattern) ---
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete':
            contact_id = request.form.get('contact_id')
            if contact_id:
                db = get_db()
                db.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
                db.commit(); db.close()
                flash('Contact deleted successfully.', 'success')
            else:
                flash('Missing contact id.', 'danger')
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

    # --- GET: pagination params ---
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = max(int(request.args.get('per', PER_PAGE_DEFAULT)), 1)
    except ValueError:
        per_page = PER_PAGE_DEFAULT
    offset = (page - 1) * per_page

    # --- Query data ---
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

    # Precompute pagination window to avoid Jinja max/min
    start_page = 1 if page - 2 < 1 else page - 2
    end_page = pages if page + 2 > pages else page + 2

    # --- Render ---
    return render_template_string("""
<!doctype html>
<html lang="en" data-bs-theme="auto" id="html-root">
  <head>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Oswald:wght@400;500;600&family=Source+Serif+Pro:wght@400;600&display=swap" rel="stylesheet">

    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Contacts</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
  body {
    padding-top: 2rem;
    font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
  }
  .card {
    border-radius: 0.8rem;
    border: 1px solid #D7D7D7;
  }
  .btn-primary {
    background-color: #B00B1E !important;
    border-color: #B00B1E !important;
  }
  .btn-primary:hover {
    background-color: #8E0918 !important;
    border-color: #8E0918 !important;
  }
  .btn-outline-secondary {
    color: #B00B1E !important;
    border-color: #B00B1E !important;
  }
  .btn-outline-secondary:hover {
    background-color: #B00B1E !important;
    color: white !important;
  }
  .table thead th {
    background: var(--bs-body-bg);
    border-bottom: 2px solid #B00B1E !important;
  }
  .table-striped tbody tr:nth-of-type(odd) {
    background-color: rgba(176, 11, 30, 0.04);
  }
  /* Dark mode tweaks */
  [data-bs-theme="dark"] .card {
    border: 1px solid #333;
  }
  [data-bs-theme="dark"] .table-striped tbody tr:nth-of-type(odd) {
    background-color: rgba(176, 11, 30, 0.2);
  }
/* Miami Branding Fonts */
.miami-title {
  font-family: 'Oswald', sans-serif;
  font-weight: 600;
  letter-spacing: 1px;
  font-size: 1.9rem;
  line-height: 1.1;
  color: #B00B1E;
  text-transform: uppercase;
}

.miami-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: var(--bs-secondary-color);
}

/* Standard Body Font */
body {
  font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
}

/* Optional: Section Headers Use Oswald */
h1, h2, h3, .h1, .h2, .h3 {
  font-family: 'Oswald', sans-serif;
  font-weight: 500;
}

/* Table and Card Cleanup */
.card {
  border-radius: 0.8rem;
  border: 1px solid #D7D7D7;
}

/* Toggle Dark Mode Button */
.btn-outline-primary,
.btn-outline-primary:focus,
.btn-outline-primary:active {
  color: #B00B1E !important;
  border-color: #B00B1E !important;
}

.btn-outline-primary:hover {
  background-color: #B00B1E !important;
  border-color: #B00B1E !important;
  color: white !important;
}

/* Pagination Controls */
.page-link {
  color: #B00B1E !important;
  border-color: #D7D7D7 !important;
}

.page-link:hover {
  background-color: rgba(176, 11, 30, 0.1) !important;
  border-color: #B00B1E !important;
  color: #8E0918 !important;
}

/* Active page */
.page-item.active .page-link {
  background-color: #B00B1E !important;
  border-color: #B00B1E !important;
  color: white !important;
}

/* Dark mode pagination */
[data-bs-theme="dark"] .page-link {
  color: #FFCDD2 !important; /* Light red tint in dark mode */
}

[data-bs-theme="dark"] .page-item.active .page-link {
  background-color: #B00B1E !important;
  border-color: #B00B1E !important;
  color: white !important;
}

</style>

<header class="mb-4 py-3 border-bottom d-flex align-items-center">
  <img src="https://upload.wikimedia.org/wikipedia/en/thumb/0/0d/Miami_Redhawks_logo.svg/2560px-Miami_Redhawks_logo.svg"
       alt="Miami RedHawks Logo"
       style="height: 56px; width:auto; margin-right: 18px;">
  <div>
    <div class="miami-title">MIAMI UNIVERSITY</div>
    <div class="miami-subtitle">Regionals · Computer & Information Technology</div>
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
          {% for p in range(start_page, end_page + 1) %}
            <li class="page-item {% if p==page %}active{% endif %}">
              <a class="page-link" href="{{ url_for('index', page=p, per=per_page) }}">{{ p }}</a>
            </li>
          {% endfor %}
          <li class="page-item {% if not has_next %}disabled{% endif %}">
            <a class="page-link" href="{{ url_for('index', page=page+1, per=per_page) if has_next else '#' }}">Next</a>
          </li>
        </ul>
      </nav>

      <footer class="py-4 text-center text-secondary small">
  &copy; {{ 2025 }} Miami University Regionals
</footer>
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
    page=page, pages=pages, per_page=per_page,
    has_prev=has_prev, has_next=has_next, total=total,
    start_page=start_page, end_page=end_page)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()
    app.run(debug=True, host='0.0.0.0', port=port)
