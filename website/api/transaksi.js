import mysql from 'mysql2/promise';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  const { id_transaksi, id_pelanggan, id_produk, jumlah } = req.body;

  try {
    const db = await mysql.createConnection({
      host: process.env.DB_HOST,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME
    });

    // 1. Stored Procedure
    await db.query("CALL sp_proses_transaksi(?, ?, @status)", [id_transaksi, id_pelanggan]);
    const [rows] = await db.query("SELECT @status AS status");
    const status = rows[0].status;

    if (status.includes("ERROR")) {
      return res.status(400).json({ message: status });
    }

    // Trigger
    const [produk] = await db.query("SELECT harga FROM produk WHERE id_produk = ?", [id_produk]);
    const harga = produk[0].harga;
    const subtotal = harga * jumlah;

    await db.query(
      "INSERT INTO detail_transaksi (id_transaksi, id_produk, jumlah, subtotal) VALUES (?, ?, ?, ?)",
      [id_transaksi, id_produk, jumlah, subtotal]
    );

    await db.end();
    return res.status(200).json({ message: `${status} Item dibeli. Trigger berjalan.` });

  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
}
