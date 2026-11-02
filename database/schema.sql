-- Database schema for AI Salesman
-- SQLite Dialect

CREATE TABLE IF NOT EXISTS retailers (
    id TEXT PRIMARY KEY,
    shop_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    price_group TEXT DEFAULT 'Standard',
    credit_limit REAL DEFAULT 50000.0,
    current_balance REAL DEFAULT 0.0,
    is_demo INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    variant TEXT NOT NULL,
    base_unit TEXT DEFAULT 'piece',
    mrp REAL NOT NULL,
    distributor_price REAL NOT NULL,
    stock_pieces INTEGER NOT NULL DEFAULT 0,
    min_stock_threshold INTEGER NOT NULL DEFAULT 50,
    aliases TEXT NOT NULL, -- comma separated keywords
    image_url TEXT,
    is_demo INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS packaging_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    unit_name TEXT NOT NULL, -- 'carton', 'box', 'dozen', 'piece'
    pieces_per_unit INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    is_allowed INTEGER DEFAULT 1,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    retailer_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    order_source TEXT DEFAULT 'VOICE_AI', -- VOICE_AI, RETAILER_PORTAL, MANUAL
    original_transcript TEXT,
    raw_language TEXT,
    subtotal REAL NOT NULL DEFAULT 0.0,
    discount REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    cancellation_reason TEXT,
    is_demo INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(retailer_id) REFERENCES retailers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    ordered_quantity REAL NOT NULL,
    ordered_unit TEXT NOT NULL,
    pieces_per_unit INTEGER NOT NULL,
    total_pieces INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    item_total REAL NOT NULL,
    is_confirmed INTEGER DEFAULT 1,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    order_id TEXT,
    retailer_id TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_demo INTEGER DEFAULT 1,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(retailer_id) REFERENCES retailers(id)
);

CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    notes TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schemes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    product_id TEXT,
    min_quantity INTEGER NOT NULL,
    free_product_id TEXT,
    free_quantity INTEGER NOT NULL,
    discount_percent REAL DEFAULT 0.0,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(free_product_id) REFERENCES products(id)
);
