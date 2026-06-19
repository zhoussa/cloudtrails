"""初始化数据库 — 建表 + 预设分类"""
import sqlite3, os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notes.db')

def init():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '📁',
        sort_order INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS post_tags (
        post_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (post_id, tag_id),
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id)  REFERENCES tags(id)  ON DELETE CASCADE
    )''')

    # 预设分类
    default_cats = [
        ('Docker & 容器', '🐳', 1),
        ('Kubernetes', '☸️', 2),
        ('HCIE 云计算', '☁️', 3),
        ('Linux & 系统', '🐧', 4),
        ('日常总结', '📝', 5),
        ('编程开发', '💻', 6),
    ]
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    for name, icon, order in default_cats:
        c.execute('INSERT OR IGNORE INTO categories (name, icon, sort_order, created_at) VALUES (?,?,?,?)',
                  (name, icon, order, now))

    conn.commit()
    conn.close()
    print('✅ 数据库初始化完成:', DB)

if __name__ == '__main__':
    init()