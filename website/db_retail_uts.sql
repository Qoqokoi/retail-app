-- ========================================================
-- DATABASE: db_retail_uts
-- IMPLEMENTASI STORED PROCEDURE & TRIGGER TRANSACTION
-- ========================================================

CREATE DATABASE IF NOT EXISTS db_retail_uts;
USE db_retail_uts;

--
CREATE TABLE IF NOT EXISTS pelanggan (
    id_pelanggan INT AUTO_INCREMENT PRIMARY KEY,
    nama_pelanggan VARCHAR(100) NOT NULL,
    telepon VARCHAR(20)
);

--
CREATE TABLE IF NOT EXISTS produk (
    id_produk INT AUTO_INCREMENT PRIMARY KEY,
    nama_produk VARCHAR(100) NOT NULL,
    harga DECIMAL(12,2) NOT NULL,
    stok INT NOT NULL DEFAULT 0
);

--
CREATE TABLE IF NOT EXISTS transaksi (
    id_transaksi INT PRIMARY KEY,
    tgl_transaksi DATETIME NOT NULL,
    id_pelanggan INT NOT NULL,
    total_bayar DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
);

--
CREATE TABLE IF NOT EXISTS detail_transaksi (
    id_detail INT AUTO_INCREMENT PRIMARY KEY,
    id_transaksi INT NOT NULL,
    id_produk INT NOT NULL,
    jumlah INT NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (id_transaksi) REFERENCES transaksi(id_transaksi),
    FOREIGN KEY (id_produk) REFERENCES produk(id_produk)
);

--
CREATE TABLE IF NOT EXISTS log_stok (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_produk INT NOT NULL,
    stok_lama INT NOT NULL,
    stok_baru INT NOT NULL,
    waktu DATETIME NOT NULL,
    FOREIGN KEY (id_produk) REFERENCES produk(id_produk)
);

--
INSERT INTO pelanggan (nama_pelanggan, telepon) VALUES
('Ahmad Fauzi', '081234567890'),
('Budi Santoso', '089876543210');

INSERT INTO produk (nama_produk, harga, stok) VALUES
('Laptop Asus Zenbook', 12000000.00, 10),
('Mouse Wireless Logitech', 250000.00, 50),
('Keyboard Mechanical', 750000.00, 25);

--
DELIMITER //

CREATE PROCEDURE sp_proses_transaksi (
    IN p_id_transaksi INT,
    IN p_id_pelanggan INT,
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_pelanggan_ada INT;

    SELECT COUNT(*) INTO v_pelanggan_ada
    FROM pelanggan WHERE id_pelanggan = p_id_pelanggan;

    IF v_pelanggan_ada = 0 THEN
        SET p_status = 'ERROR: Pelanggan tidak ditemukan!';
    ELSE
        INSERT INTO transaksi (id_transaksi, tgl_transaksi, id_pelanggan, total_bayar)
        VALUES (p_id_transaksi, NOW(), p_id_pelanggan, 0);
        SET p_status = 'SUCCESS: Transaksi berhasil dibuka.';
    END IF;
END //

DELIMITER ;

--
DELIMITER //

CREATE TRIGGER trg_setelah_tambah_detail
AFTER INSERT ON detail_transaksi
FOR EACH ROW
BEGIN
    UPDATE produk
    SET stok = stok - NEW.jumlah
    WHERE id_produk = NEW.id_produk;
END //

DELIMITER ;

---
DELIMITER //

CREATE TRIGGER trg_audit_stok_produk
AFTER UPDATE ON produk
FOR EACH ROW
BEGIN
    IF OLD.stok <> NEW.stok THEN
        INSERT INTO log_stok (id_produk, stok_lama, stok_baru, waktu)
        VALUES (NEW.id_produk, OLD.stok, NEW.stok, NOW());
    END IF;
END //

DELIMITER ;
