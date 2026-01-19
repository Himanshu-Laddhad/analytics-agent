-- Create read-only user for agent (CRITICAL FOR SAFETY)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_readonly'
   ) THEN
      CREATE USER analytics_readonly WITH PASSWORD 'readonly_pass_change_in_prod';
   END IF;
END
$do$;

-- Grant minimal permissions
GRANT CONNECT ON DATABASE analytics_db TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;

-- Tables will be created by admin, then we grant SELECT to readonly user

-- Sample tables with realistic e-commerce data
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    country VARCHAR(100),
    signup_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2),
    stock_quantity INT DEFAULT 0
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- Sample data: Customers
INSERT INTO customers (customer_name, email, country, signup_date) VALUES
('Alice Johnson', 'alice@example.com', 'USA', '2024-01-15'),
('Bob Smith', 'bob@example.com', 'Canada', '2024-02-20'),
('Carol White', 'carol@example.com', 'UK', '2024-03-10'),
('David Brown', 'david@example.com', 'Australia', '2024-01-25'),
('Eve Davis', 'eve@example.com', 'USA', '2024-04-05'),
('Frank Wilson', 'frank@example.com', 'Germany', '2024-02-14'),
('Grace Lee', 'grace@example.com', 'Singapore', '2024-03-22'),
('Henry Taylor', 'henry@example.com', 'USA', '2024-01-30');

-- Sample data: Products
INSERT INTO products (product_name, category, price, stock_quantity) VALUES
('Laptop Pro 15', 'Electronics', 1299.99, 50),
('Wireless Mouse', 'Electronics', 29.99, 200),
('USB-C Hub', 'Electronics', 49.99, 150),
('Office Chair Premium', 'Furniture', 399.99, 30),
('Standing Desk', 'Furniture', 599.99, 25),
('Desk Lamp LED', 'Furniture', 45.99, 100),
('Notebook Set', 'Stationery', 12.99, 500),
('Pen Set Premium', 'Stationery', 24.99, 300),
('Mechanical Keyboard', 'Electronics', 129.99, 75),
('Monitor 27 inch', 'Electronics', 349.99, 40),
('Webcam HD', 'Electronics', 79.99, 120),
('Headphones Wireless', 'Electronics', 199.99, 90),
('Backpack Laptop', 'Accessories', 59.99, 80),
('Water Bottle', 'Accessories', 19.99, 250),
('Desk Organizer', 'Furniture', 34.99, 150);

-- Sample data: Orders (mix of dates for time series)
INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, '2025-01-05', 1329.98, 'completed'),
(2, '2025-01-06', 449.98, 'completed'),
(3, '2025-01-07', 599.99, 'completed'),
(1, '2025-01-08', 79.98, 'completed'),
(4, '2025-01-09', 1849.96, 'completed'),
(5, '2025-01-10', 29.99, 'completed'),
(6, '2025-01-11', 629.98, 'completed'),
(7, '2025-01-12', 154.98, 'completed'),
(2, '2025-01-13', 399.99, 'shipped'),
(3, '2025-01-14', 249.97, 'shipped'),
(8, '2025-01-15', 1299.99, 'processing'),
(1, '2025-01-16', 59.99, 'processing'),
(4, '2025-01-17', 199.99, 'pending'),
(5, '2025-01-18', 524.96, 'pending');

-- Sample data: Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
-- Order 1 (Alice, Jan 5)
(1, 1, 1, 1299.99),  -- Laptop
(1, 2, 1, 29.99),    -- Mouse
-- Order 2 (Bob, Jan 6)
(2, 4, 1, 399.99),   -- Chair
(2, 6, 1, 45.99),    -- Lamp
-- Order 3 (Carol, Jan 7)
(3, 5, 1, 599.99),   -- Standing Desk
-- Order 4 (Alice, Jan 8)
(4, 7, 2, 12.99),    -- Notebooks
(4, 8, 2, 24.99),    -- Pens
-- Order 5 (David, Jan 9)
(5, 1, 1, 1299.99),  -- Laptop
(5, 9, 1, 129.99),   -- Keyboard
(5, 10, 1, 349.99),  -- Monitor
-- Order 6 (Eve, Jan 10)
(6, 2, 1, 29.99),    -- Mouse
-- Order 7 (Frank, Jan 11)
(7, 5, 1, 599.99),   -- Desk
(7, 2, 1, 29.99),    -- Mouse
-- Order 8 (Grace, Jan 12)
(8, 11, 1, 79.99),   -- Webcam
(8, 8, 3, 24.99),    -- Pens
-- Order 9 (Bob, Jan 13)
(9, 4, 1, 399.99),   -- Chair
-- Order 10 (Carol, Jan 14)
(10, 12, 1, 199.99), -- Headphones
(10, 6, 1, 45.99),   -- Lamp
-- Order 11 (Henry, Jan 15)
(11, 1, 1, 1299.99), -- Laptop
-- Order 12 (Alice, Jan 16)
(12, 13, 1, 59.99),  -- Backpack
-- Order 13 (David, Jan 17)
(13, 12, 1, 199.99), -- Headphones
-- Order 14 (Eve, Jan 18)
(14, 10, 1, 349.99), -- Monitor
(14, 3, 1, 49.99),   -- USB Hub
(14, 9, 1, 129.99);  -- Keyboard

-- Grant SELECT permissions to readonly user
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO analytics_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_readonly;

-- Verify setup
SELECT 'Setup complete! Total orders: ' || COUNT(*) FROM orders;
SELECT 'Total revenue: $' || SUM(total_amount) FROM orders;