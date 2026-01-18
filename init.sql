-- Create read-only user for agent
CREATE USER analytics_readonly WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE analytics_db TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_readonly;

-- Sample tables
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50)
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    unit_price DECIMAL(10, 2)
);

-- Sample data
INSERT INTO products (product_name, category, price) VALUES
('Laptop Pro', 'Electronics', 1299.99),
('Wireless Mouse', 'Electronics', 29.99),
('Office Chair', 'Furniture', 299.99),
('Desk Lamp', 'Furniture', 49.99),
('Notebook Set', 'Stationery', 12.99);

-- More sample data would go here