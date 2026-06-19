import sqlite3, os, markdown, uuid, secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, session
from markupsafe import Markup
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
BASE = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE, 'notes.db')
UPLOAD_DIR = os.path.join(BASE, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'}
MAX_SIZE = 10 * 1024 * 1024
PASSWORD = 'zsj123456'

os.makedirs(UPLOAD_DIR, exist_ok=True)

md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])

EMOJI_ICONS = ['📁','🐳','☸️','☁️','🐧','📝','💻','🔥','⚡','🔧','📚','🎯','🛠️','📊','🗂️','🧪','🚀','💡']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ── Auth ──

@app.before_request
def check_auth():
    if request.endpoint in ('login', 'do_login', None):
        return
    if request.path.startswith('/static/'):
        return
    if not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html', error=None)

@app.route('/login', methods=['POST'])
def do_login():
    pwd = request.form.get('password', '')
    if pwd == PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('index'))
    return render_template('login.html', error='密码错误')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Helpers ──

def render_md(text):
    return Markup(md.convert(text))

def get_tags_for_post(post_id):
    db = get_db()
    rows = db.execute('''SELECT t.name FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        WHERE pt.post_id = ? ORDER BY t.name''', (post_id,)).fetchall()
    return [r['name'] for r in rows]

def save_tags(post_id, tag_string):
    db = get_db()
    db.execute('DELETE FROM post_tags WHERE post_id = ?', (post_id,))
    if tag_string:
        raw = [t.strip().lower() for t in tag_string.split(',') if t.strip()]
        seen = set()
        for name in raw:
            if name in seen: continue
            seen.add(name)
            db.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (name,))
            tag_row = db.execute('SELECT id FROM tags WHERE name = ?', (name,)).fetchone()
            db.execute('INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?,?)',
                       (post_id, tag_row['id']))
    db.commit()

def get_tags_for_category(cat_id):
    db = get_db()
    if cat_id == 0:
        rows = db.execute('''SELECT t.name, COUNT(pt.post_id) as cnt FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            GROUP BY t.id ORDER BY cnt DESC''').fetchall()
    else:
        rows = db.execute('''SELECT t.name, COUNT(pt.post_id) as cnt FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            JOIN posts p ON p.id = pt.post_id
            WHERE p.category_id = ?
            GROUP BY t.id ORDER BY cnt DESC''', (cat_id,)).fetchall()
    return [{'name': r['name'], 'count': r['cnt']} for r in rows]

def get_categories():
    db = get_db()
    return db.execute('''SELECT c.*, COUNT(p.id) as post_count
        FROM categories c LEFT JOIN posts p ON p.category_id = c.id
        GROUP BY c.id ORDER BY c.sort_order''').fetchall()

def get_category(cat_id):
    db = get_db()
    return db.execute('SELECT * FROM categories WHERE id=?', (cat_id,)).fetchone()

app.jinja_env.globals['render_md'] = render_md
app.jinja_env.globals['get_tags'] = get_tags_for_post
app.jinja_env.globals['get_categories'] = get_categories
app.jinja_env.globals['emoji_icons'] = EMOJI_ICONS

# ── Routes ──

@app.route('/')
def index():
    return redirect(url_for('category_view', cat_id=0))

@app.route('/cat/<int:cat_id>')
def category_view(cat_id):
    db = get_db()
    tag_filter = request.args.get('tag', '').strip()
    query = request.args.get('q', '').strip()

    cat = None
    where = []
    params = []

    if cat_id > 0:
        cat = get_category(cat_id)
        if not cat:
            return '分类不存在', 404
        where.append('p.category_id = ?')
        params.append(cat_id)

    if tag_filter:
        where.append('''p.id IN (
            SELECT pt.post_id FROM post_tags pt
            JOIN tags t ON t.id = pt.tag_id WHERE t.name = ?
        )''')
        params.append(tag_filter.lower())

    if query:
        like = f'%{query}%'
        where.append('(p.title LIKE ? OR p.content LIKE ?)')
        params.extend([like, like])

    sql = 'SELECT DISTINCT p.* FROM posts p'
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY p.updated_at DESC'

    posts = db.execute(sql, params).fetchall()
    tags = get_tags_for_category(cat_id)
    categories = get_categories()
    all_count = db.execute('SELECT COUNT(*) FROM posts').fetchone()[0]

    return render_template('index.html',
        posts=posts, tags=tags, categories=categories,
        current_cat=cat, current_cat_id=cat_id,
        current_tag=tag_filter, current_query=query,
        all_count=all_count)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        return '帖子不存在', 404
    cat = get_category(post['category_id']) if post['category_id'] else None
    return render_template('post.html', post=post, cat=cat)

@app.route('/new', methods=['GET', 'POST'])
@app.route('/new/<int:cat_id>', methods=['GET', 'POST'])
def new_post(cat_id=0):
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        tags_str = request.form.get('tags', '').strip()
        cid = request.form.get('category_id', '').strip()
        if title and content:
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            db = get_db()
            cur = db.execute(
                'INSERT INTO posts (title, content, category_id, created_at, updated_at) VALUES (?,?,?,?,?)',
                (title, content, int(cid) if cid else None, now, now))
            save_tags(cur.lastrowid, tags_str)
            return redirect(url_for('category_view', cat_id=int(cid) if cid else 0))
    return render_template('new.html', post=None, preselected_cat=cat_id)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        return '帖子不存在', 404
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        tags_str = request.form.get('tags', '').strip()
        cid = request.form.get('category_id', '').strip()
        if title and content:
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            db.execute('UPDATE posts SET title=?, content=?, category_id=?, updated_at=? WHERE id=?',
                       (title, content, int(cid) if cid else None, now, post_id))
            db.commit()
            save_tags(post_id, tags_str)
            return redirect(url_for('view_post', post_id=post_id))
    return render_template('new.html', post=post, preselected_cat=0)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    db = get_db()
    db.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()
    return redirect(url_for('category_view', cat_id=0))

# ── Category CRUD ──

@app.route('/cat/new', methods=['POST'])
def create_category():
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', '📁').strip()
    if not name:
        return redirect(url_for('category_view', cat_id=0))
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = get_db()
    max_order = db.execute('SELECT MAX(sort_order) FROM categories').fetchone()[0] or 0
    db.execute('INSERT INTO categories (name, icon, sort_order, created_at) VALUES (?,?,?,?)',
               (name, icon, max_order + 1, now))
    db.commit()
    return redirect(url_for('category_view', cat_id=0))

@app.route('/cat/<int:cat_id>/edit', methods=['POST'])
def edit_category(cat_id):
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', '📁').strip()
    if not name:
        return redirect(url_for('category_view', cat_id=0))
    db = get_db()
    db.execute('UPDATE categories SET name=?, icon=? WHERE id=?', (name, icon, cat_id))
    db.commit()
    return redirect(url_for('category_view', cat_id=0))

@app.route('/cat/<int:cat_id>/delete', methods=['POST'])
def delete_category(cat_id):
    db = get_db()
    db.execute('UPDATE posts SET category_id=NULL WHERE category_id=?', (cat_id,))
    db.execute('DELETE FROM categories WHERE id=?', (cat_id,))
    db.commit()
    return redirect(url_for('category_view', cat_id=0))

# ── Image Upload ──

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'ok': False, 'error': 'Empty filename'}), 400
    if not allowed_file(file.filename):
        return jsonify({'ok': False, 'error': f'不支持的文件类型'}), 400
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    url = f"/static/uploads/{filename}"
    md_snippet = f"![{file.filename}]({url})"
    return jsonify({'ok': True, 'url': url, 'markdown': md_snippet})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)