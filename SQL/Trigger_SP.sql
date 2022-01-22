-- stored procedure start
DELIMITER / / CREATE PROCEDURE ins_stock(IN loc INT, IN pro INT, IN sto INT) BEGIN
SELECT MAX(id) INTO @MAX_ID
FROM product_stock;
SET @MAX_ID := @MAX_ID + 1;
INSERT INTO product_stock
values(@MAX_ID, loc, pro, sto);
END / / DELIMITER;
-- stored procedure end
-- trigger1 start
DELIMITER / / CREATE TRIGGER validate_insert BEFORE
INSERT ON product__source FOR EACH ROW BEGIN IF NEW.c_email NOT LIKE '%_@%_.__%' THEN
SET NEW.c_email = 'INVALID EMAIL-UPDATE ASAP';
END IF;
END / / -- trigger1 end
-- trigger2 start
DELIMITER / / CREATE TRIGGER validate_update BEFORE
UPDATE ON product__source FOR EACH ROW BEGIN IF NEW.c_email NOT LIKE '%_@%_.__%' THEN
SET NEW.c_email = 'INVALID EMAIL-UPDATE ASAP';
END IF;
END / / -- trigger2 end