CREATE TABLE product (
        id INTEGER NOT NULL AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        PRIMARY KEY (id),
        UNIQUE (name)
);
CREATE TABLE location (
        id INTEGER NOT NULL AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        other_details TEXT,
        PRIMARY KEY (id),
        UNIQUE (name)
);
CREATE TABLE product_source (
        p_id INTEGER NOT NULL,
        c_id INTEGER NOT NULL AUTO_INCREMENT,
        c_name VARCHAR(100) NOT NULL,
        p_name VARCHAR(100) NOT NULL,
        PRIMARY KEY (c_id),
        UNIQUE (c_name) FOREIGN KEY(p_id) REFERENCES product (id),
        FOREIGN KEY(p_name) REFERENCES product (name)
);
CREATE TABLE product_movement (
        id INTEGER NOT NULL AUTO_INCREMENT,
        movement_date DATE,
        from_location_id INTEGER,
        to_location_id INTEGER,
        product_id INTEGER NOT NULL,
        qty INTEGER NOT NULL CHECK (qty >= 0),
        PRIMARY KEY (id),
        FOREIGN KEY(from_location_id) REFERENCES location (id),
        FOREIGN KEY(to_location_id) REFERENCES location (id),
        FOREIGN KEY(product_id) REFERENCES product (id)
);
CREATE TABLE product_stock (
        id INTEGER NOT NULL AUTO_INCREMENT,
        location_id INTEGER,
        product_id INTEGER,
        available_stock INTEGER NOT NULL CHECK (available_stock >= 0),
        PRIMARY KEY (id),
        FOREIGN KEY(location_id) REFERENCES location (id),
        FOREIGN KEY(product_id) REFERENCES product (id)
);