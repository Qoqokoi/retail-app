from flask import Flask, render_template_string, request, redirect, url_for, flash
import mariadb

app = Flask(__name__)
app.secret_key = 'qoqokoi-secret'

def get_db():
    return mariadb.connect(
        user="root", 
        password="", # Isi password MariaDB lokalmu jika ada
        host="127.0.0.1", 
        port=3306, 
        database="db_retail_uts"
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <title>Kasir Retail - UTS Basis Data 2</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { transition: background-color 0.25s ease, color 0.25s ease; }
        .card { transition: background-color 0.25s ease, border-color 0.25s ease; }
        [data-bs-theme="dark"] .bg-light-subtle-custom { background-color: #2b3035 !important; }
        [data-bs-theme="light"] .bg-light-subtle-custom { background-color: #f8f9fa !important; }
    </style>
    <script>
        //Terapkan tema tersimpan sebelum halaman dirender agar tidak berkedip
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    </script>
</head>
<body class="bg-light-subtle-custom">
    <div class="container py-4">
        
        <!-- HEADER & TOMBOL DARK/LIGHT MODE -->
        <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
            <h2 class="mb-0">POS Retail - Stored Procedure & Trigger</h2>
            <button id="themeToggle" class="btn btn-outline-secondary btn-sm fw-bold px-3" onclick="toggleTheme()">
                🌙 Dark Mode
            </button>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert {{ 'alert-danger' if 'ERROR' in message or 'Gagal' in message or 'DITOLAK' in message else 'alert-success' }} fw-bold">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="row">
            <!-- KOLOM KIRI: FORM TRANSAKSI, PELANGGAN, & RESTOCK -->
            <div class="col-md-4">
                
                <!-- 1. MODUL POS (TRANSAKSI KASIR) -->
                <div class="card shadow-sm mb-3">
                    <div class="card-header bg-primary text-white fw-bold">1. Buka Transaksi (POS)</div>
                    <div class="card-body">
                        <form action="/transaksi" method="POST">
                            <label class="form-label small text-muted mb-1">ID Transaksi (Otomatis)</label>
                            <input type="number" name="id_transaksi" class="form-control form-control-sm mb-2" value="{{ next_trans_id }}" readonly>
                            
                            <label class="form-label small text-muted mb-1">Pilih Pelanggan</label>
                            <select name="id_pelanggan" class="form-select form-select-sm mb-2" required>
                                {% for pel in pelanggan %}
                                <option value="{{ pel[0] }}">ID {{ pel[0] }} - {{ pel[1] }}</option>
                                {% endfor %}
                                <option value="999">-- Tes ID Tidak Terdaftar (Uji Error SP) --</option>
                            </select>

                            <label class="form-label small text-muted mb-1">Pilih Produk</label>
                            <select name="id_produk" class="form-select form-select-sm mb-2" required>
                                {% for p in produk %}
                                <option value="{{ p[0] }}">
                                    {{ p[1] }} (Rp{{ "{:,.0f}".format(p[2]) }}) - Stok: {{ p[3] }} {{ '[HABIS]' if p[3] <= 0 else '' }}
                                </option>
                                {% endfor %}
                            </select>

                            <label class="form-label small text-muted mb-1">Jumlah Beli</label>
                            <input type="number" name="jumlah" class="form-control form-control-sm mb-3" placeholder="Masukkan jumlah beli..." min="1" required>
                            
                            <button type="submit" class="btn btn-success btn-sm w-100 fw-bold">Proses Belanja</button>
                        </form>
                    </div>
                </div>

                <!-- 2. MODUL TAMBAH PELANGGAN (AUTO ID & RESET KE 1 JIKA KOSONG) -->
                <div class="card shadow-sm mb-3">
                    <div class="card-header bg-info text-dark fw-bold">2. Tambah Pelanggan Baru (Auto-ID)</div>
                    <div class="card-body">
                        <form action="/pelanggan/tambah" method="POST">
                            <label class="form-label small text-muted mb-1">ID Pelanggan Otomatis Berikutnya: <strong>#{{ next_pel_id }}</strong></label>
                            <input type="text" name="nama_pelanggan" class="form-control form-control-sm mb-2" placeholder="Ketik Nama Pelanggan..." required>
                            <input type="text" name="telepon" class="form-control form-control-sm mb-2" placeholder="No. Telepon (Contoh: 0812...)" required>
                            <button type="submit" class="btn btn-info btn-sm w-100 fw-bold text-dark">+ Simpan Pelanggan</button>
                        </form>
                    </div>
                </div>

                <!-- 3. MODUL RESTOCK & TAMBAH PRODUK BARU -->
                <div class="card shadow-sm mb-3">
                    <div class="card-header bg-warning text-dark fw-bold">3. Restock & Produk Baru</div>
                    <div class="card-body">
                        <!-- Form Restock -->
                        <form action="/restock" method="POST" class="mb-3 border-bottom pb-3">
                            <label class="form-label small fw-bold mb-1">Restock Produk</label>
                            <select name="id_produk" class="form-select form-select-sm mb-2" required>
                                {% for p in produk %}
                                <option value="{{ p[0] }}">{{ p[1] }} (Sisa Stok: {{ p[3] }})</option>
                                {% endfor %}
                            </select>
                            <div class="input-group input-group-sm">
                                <input type="number" name="jumlah_restock" class="form-control" placeholder="Jumlah Tambah..." min="1" required>
                                <button type="submit" class="btn btn-warning fw-bold text-dark">+ Restock</button>
                            </div>
                        </form>

                        <!-- Form Produk Baru -->
                        <form action="/produk/tambah" method="POST">
                            <label class="form-label small fw-bold mb-1">Tambah Produk Baru (ID Berikutnya: #{{ next_prod_id }})</label>
                            <input type="text" name="nama_produk" class="form-control form-control-sm mb-2" placeholder="Nama Produk..." required>
                            <div class="row g-2 mb-2">
                                <div class="col-7"><input type="number" name="harga" class="form-control form-control-sm" placeholder="Harga (Rp)" min="0" required></div>
                                <div class="col-5"><input type="number" name="stok" class="form-control form-control-sm" placeholder="Stok Awal" min="0" required></div>
                            </div>
                            <button type="submit" class="btn btn-secondary btn-sm w-100 fw-bold">+ Produk Baru</button>
                        </form>
                    </div>
                </div>

            </div>

            <!-- KOLOM KANAN: TABEL MONITORING & FITUR HAPUS -->
            <div class="col-md-8">
                
                <!-- TABEL STOK REAL-TIME (DENGAN TOMBOL HAPUS PRODUK/STOK) -->
                <div class="card shadow-sm mb-3">
                    <div class="card-header bg-dark text-white fw-bold">Kondisi Stok Real-Time (Tabel: produk)</div>
                    <table class="table table-sm table-striped mb-0 align-middle">
                        <thead class="table-secondary"><tr><th>ID</th><th>Produk</th><th>Harga</th><th>Stok</th><th>Aksi</th></tr></thead>
                        <tbody>
                            {% for p in produk %}
                            <tr>
                                <td>{{ p[0] }}</td>
                                <td>{{ p[1] }}</td>
                                <td>Rp{{ "{:,.2f}".format(p[2]) }}</td>
                                <td>
                                    {% if p[3] <= 0 %}
                                        <span class="badge bg-danger">HABIS (0)</span>
                                    {% else %}
                                        <span class="fw-bold text-success">{{ p[3] }}</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <form action="/produk/hapus/{{ p[0] }}" method="POST" onsubmit="return confirm('Hapus produk {{ p[1] }} dari daftar stok beserta riwayatnya?');">
                                        <button type="submit" class="btn btn-outline-danger btn-sm py-0 px-2">Hapus Produk</button>
                                    </form>
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="5" class="text-center text-muted py-2">Belum ada produk terdaftar (ID di-reset ke #1).</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- TABEL PELANGGAN (DENGAN HAPUS USER) & RIWAYAT TRANSAKSI -->
                <div class="row">
                    <div class="col-md-6">
                        <div class="card shadow-sm mb-3">
                            <div class="card-header bg-secondary text-white fw-bold">Daftar Pelanggan (User)</div>
                            <table class="table table-sm mb-0 align-middle">
                                <thead class="table-secondary"><tr><th>ID</th><th>Nama</th><th>Telepon</th><th>Aksi</th></tr></thead>
                                <tbody>
                                    {% for pel in pelanggan %}
                                    <tr>
                                        <td>{{ pel[0] }}</td>
                                        <td>{{ pel[1] }}</td>
                                        <td>{{ pel[2] or '-' }}</td>
                                        <td>
                                            <form action="/pelanggan/hapus/{{ pel[0] }}" method="POST" onsubmit="return confirm('Hapus pelanggan ini beserta riwayat transaksinya?');">
                                                <button type="submit" class="btn btn-outline-danger btn-sm py-0 px-2">Hapus</button>
                                            </form>
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="4" class="text-center text-muted py-2">Kosong (ID kembali ke #1)</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="card shadow-sm mb-3">
                            <div class="card-header bg-success text-white fw-bold">5 Transaksi Terakhir</div>
                            <table class="table table-sm mb-0 align-middle">
                                <thead class="table-secondary"><tr><th>ID</th><th>Pelanggan</th><th>Total Bayar</th></tr></thead>
                                <tbody>
                                    {% for t in transaksi_list %}
                                    <tr><td>#{{ t[0] }}</td><td>{{ t[1] }}</td><td class="fw-bold">Rp{{ "{:,.0f}".format(t[2]) }}</td></tr>
                                    {% else %}
                                    <tr><td colspan="3" class="text-center text-muted py-2">Belum ada transaksi</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- TABEL LOG TRIGGER AUDIT STOK (DENGAN FITUR HAPUS LOG) -->
                <div class="card shadow-sm">
                    <div class="card-header bg-danger text-white d-flex justify-content-between align-items-center">
                        <span class="fw-bold">Log Trigger Audit Stok (Tabel: log_stok)</span>
                        <form action="/log/bersihkan" method="POST" onsubmit="return confirm('Bersihkan seluruh riwayat log stok? ID Log akan diulang dari 1.');">
                            <button type="submit" class="btn btn-light btn-sm py-0 fw-bold text-danger">Bersihkan Semua Log</button>
                        </form>
                    </div>
                    <table class="table table-sm table-hover mb-0 align-middle">
                        <thead class="table-secondary"><tr><th>Log ID</th><th>Produk ID</th><th>Lama</th><th>Baru</th><th>Waktu</th><th>Aksi</th></tr></thead>
                        <tbody>
                            {% for l in log %}
                            <tr>
                                <td>{{ l[0] }}</td>
                                <td>{{ l[1] }}</td>
                                <td>{{ l[2] }}</td>
                                <td class="fw-bold">{{ l[3] }}</td>
                                <td>{{ l[4] }}</td>
                                <td>
                                    <form action="/log/hapus/{{ l[0] }}" method="POST">
                                        <button type="submit" class="btn btn-outline-danger btn-sm py-0 px-2">X</button>
                                    </form>
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="6" class="text-center text-muted py-2">Belum ada riwayat log stok (ID Log mulai dari #1).</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            </div>
        </div>
    </div>

    <!-- SCRIPT LIGHT MODE & DARK MODE -->
    <script>
        function updateButtonLabel(theme) {
            const btn = document.getElementById('themeToggle');
            if (theme === 'dark') {
                btn.innerHTML = '☀️ Light Mode';
                btn.classList.replace('btn-outline-secondary', 'btn-warning');
            } else {
                btn.innerHTML = '🌙 Dark Mode';
                btn.classList.replace('btn-warning', 'btn-outline-secondary');
            }
        }

        function toggleTheme() {
            const htmlEl = document.documentElement;
            const currentTheme = htmlEl.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            htmlEl.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateButtonLabel(newTheme);
        }

        // Inisialisasi label tombol saat halaman selesai dimuat
        document.addEventListener('DOMContentLoaded', () => {
            updateButtonLabel(document.documentElement.getAttribute('data-bs-theme'));
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()
    
    # Pastikan tidak ada stok minus
    cur.execute("UPDATE produk SET stok = 0 WHERE stok < 0")
    conn.commit()

    # Ambil data produk & hitung ID produk berikutnya (Mulai dari 1 jika kosong)
    cur.execute("SELECT id_produk, nama_produk, harga, stok FROM produk ORDER BY id_produk ASC")
    produk = cur.fetchall()
    cur.execute("SELECT COALESCE(MAX(id_produk), 0) + 1 FROM produk")
    next_prod_id = cur.fetchone()[0]
    
    # Ambil data pelanggan & hitung ID pelanggan berikutnya (Mulai dari 1 jika kosong)
    cur.execute("SELECT id_pelanggan, nama_pelanggan, telepon FROM pelanggan ORDER BY id_pelanggan ASC")
    pelanggan = cur.fetchall()
    cur.execute("SELECT COALESCE(MAX(id_pelanggan), 0) + 1 FROM pelanggan")
    next_pel_id = cur.fetchone()[0]

    # Ambil 5 transaksi terakhir & ID Transaksi berikutnya
    cur.execute("""
        SELECT t.id_transaksi, p.nama_pelanggan, t.total_bayar 
        FROM transaksi t 
        JOIN pelanggan p ON t.id_pelanggan = p.id_pelanggan 
        ORDER BY t.id_transaksi DESC LIMIT 5
    """)
    transaksi_list = cur.fetchall()

    cur.execute("SELECT COALESCE(MAX(id_transaksi), 0) + 1 FROM transaksi")
    next_trans_id = cur.fetchone()[0]

    # Ambil data log trigger
    cur.execute("SELECT id_log, id_produk, stok_lama, stok_baru, waktu FROM log_stok ORDER BY id_log DESC")
    log = cur.fetchall()
    
    conn.close()
    return render_template_string(
        HTML_TEMPLATE, 
        produk=produk, 
        pelanggan=pelanggan, 
        transaksi_list=transaksi_list,
        log=log, 
        next_trans_id=next_trans_id,
        next_pel_id=next_pel_id,
        next_prod_id=next_prod_id
    )

@app.route('/transaksi', methods=['POST'])
def transaksi():
    id_trans = int(request.form['id_transaksi'])
    id_pel = int(request.form['id_pelanggan'])
    id_prod = int(request.form['id_produk'])
    jumlah = int(request.form['jumlah'])
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # 1. Validasi ketersediaan stok terlebih dahulu
        cur.execute("SELECT nama_produk, harga, stok FROM produk WHERE id_produk = ?", (id_prod,))
        row_prod = cur.fetchone()
        
        if not row_prod:
            flash("DITOLAK: Produk tidak ditemukan!")
            return redirect(url_for('index'))
            
        nama_prod, harga, stok_tersedia = row_prod
        
        if stok_tersedia <= 0:
            flash(f"TRANSAKSI DITOLAK: Stok '{nama_prod}' sudah HABIS (Stok: 0)! Silakan restock terlebih dahulu.")
            return redirect(url_for('index'))
            
        if jumlah > stok_tersedia:
            flash(f"TRANSAKSI DITOLAK: Jumlah beli ({jumlah}) melebihi sisa stok '{nama_prod}' yang tersedia ({stok_tersedia})!")
            return redirect(url_for('index'))

        # 2. Panggil Stored Procedure sp_proses_transaksi
        cur.execute("CALL sp_proses_transaksi(?, ?, @status)", (id_trans, id_pel))
        cur.execute("SELECT @status")
        status = cur.fetchone()[0]
        
        if status and "ERROR" in status:
            flash(status)
        else:
            subtotal = harga * jumlah
            # 3. Insert ke detail_transaksi (Memicu Trigger pemotongan stok & log audit)
            cur.execute(
                "INSERT INTO detail_transaksi (id_transaksi, id_produk, jumlah, subtotal) VALUES (?, ?, ?, ?)", 
                (id_trans, id_prod, jumlah, subtotal)
            )
            # 4. Update total_bayar pada tabel transaksi
            cur.execute(
                "UPDATE transaksi SET total_bayar = total_bayar + ? WHERE id_transaksi = ?",
                (subtotal, id_trans)
            )
            conn.commit()
            flash(f"{status} Pembelian {jumlah}x {nama_prod} berhasil (Total: Rp{subtotal:,.0f}).")
    except mariadb.Error as e:
        flash(f"SQL Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/pelanggan/tambah', methods=['POST'])
def tambah_pelanggan():
    nama = request.form['nama_pelanggan'].strip()
    telepon = request.form.get('telepon', '').strip()
    
    conn = get_db()
    cur = conn.cursor()
    try:
        # Hitung ID secara eksplisit agar selalu mulai dari 1 jika tabel kosong
        cur.execute("SELECT COALESCE(MAX(id_pelanggan), 0) + 1 FROM pelanggan")
        next_id = cur.fetchone()[0]
        
        cur.execute("INSERT INTO pelanggan (id_pelanggan, nama_pelanggan, telepon) VALUES (?, ?, ?)", (next_id, nama, telepon))
        conn.commit()
        flash(f"Pelanggan '{nama}' berhasil ditambahkan dengan ID #{next_id}!")
    except mariadb.Error as e:
        flash(f"Gagal tambah pelanggan: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/pelanggan/hapus/<int:id_pel>', methods=['POST'])
def hapus_pelanggan(id_pel):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM detail_transaksi 
            WHERE id_transaksi IN (SELECT id_transaksi FROM transaksi WHERE id_pelanggan = ?)
        """, (id_pel,))
        cur.execute("DELETE FROM transaksi WHERE id_pelanggan = ?", (id_pel,))
        cur.execute("DELETE FROM pelanggan WHERE id_pelanggan = ?", (id_pel,))
        conn.commit()
        
        # Reset AUTO_INCREMENT ke 1 (atau nilai maksimum saat ini + 1)
        cur.execute("ALTER TABLE pelanggan AUTO_INCREMENT = 1")
        cur.execute("ALTER TABLE detail_transaksi AUTO_INCREMENT = 1")
        
        flash(f"Pelanggan ID #{id_pel} berhasil dihapus!")
    except mariadb.Error as e:
        flash(f"Gagal menghapus pelanggan: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/produk/tambah', methods=['POST'])
def tambah_produk():
    nama = request.form['nama_produk'].strip()
    harga = float(request.form['harga'])
    stok = int(request.form['stok'])
    
    conn = get_db()
    cur = conn.cursor()
    try:
        # Hitung ID secara eksplisit agar selalu mulai dari 1 jika tabel kosong
        cur.execute("SELECT COALESCE(MAX(id_produk), 0) + 1 FROM produk")
        next_id = cur.fetchone()[0]
        
        cur.execute("INSERT INTO produk (id_produk, nama_produk, harga, stok) VALUES (?, ?, ?, ?)", (next_id, nama, harga, stok))
        conn.commit()
        flash(f"Produk '{nama}' berhasil ditambahkan dengan ID #{next_id}!")
    except mariadb.Error as e:
        flash(f"Gagal tambah produk: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/produk/hapus/<int:id_prod>', methods=['POST'])
def hapus_produk(id_prod):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Hapus riwayat log_stok dan detail_transaksi yang terkait produk ini agar tidak tertahan Foreign Key
        cur.execute("DELETE FROM log_stok WHERE id_produk = ?", (id_prod,))
        cur.execute("DELETE FROM detail_transaksi WHERE id_produk = ?", (id_prod,))
        cur.execute("DELETE FROM produk WHERE id_produk = ?", (id_prod,))
        conn.commit()
        
        # Reset AUTO_INCREMENT agar kembali ke 1 jika seluruh produk dihapus
        cur.execute("ALTER TABLE produk AUTO_INCREMENT = 1")
        cur.execute("ALTER TABLE log_stok AUTO_INCREMENT = 1")
        
        flash(f"Produk ID #{id_prod} berhasil dihapus dari daftar stok!")
    except mariadb.Error as e:
        flash(f"Gagal menghapus produk: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/restock', methods=['POST'])
def restock():
    id_prod = int(request.form['id_produk'])
    jumlah_tambah = int(request.form['jumlah_restock'])
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE produk SET stok = stok + ? WHERE id_produk = ?", (jumlah_tambah, id_prod))
        conn.commit()
        flash(f"Restock berhasil! Stok Produk ID #{id_prod} bertambah +{jumlah_tambah} unit.")
    except mariadb.Error as e:
        flash(f"Gagal restock: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/log/hapus/<int:id_log>', methods=['POST'])
def hapus_log_satuan(id_log):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM log_stok WHERE id_log = ?", (id_log,))
        conn.commit()
        cur.execute("ALTER TABLE log_stok AUTO_INCREMENT = 1")
        flash(f"Log audit ID #{id_log} berhasil dihapus.")
    except mariadb.Error as e:
        flash(f"Gagal hapus log: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/log/bersihkan', methods=['POST'])
def bersihkan_semua_log():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE TABLE log_stok")
        conn.commit()
        flash("Seluruh riwayat Log Trigger berhasil dibersihkan (ID kembali ke #1)!")
    except mariadb.Error as e:
        flash(f"Gagal membersihkan log: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
