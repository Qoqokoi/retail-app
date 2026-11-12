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
<html lang="id">
<head>
    <title>Kasir Retail (Local)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-4">
        <h2 class="mb-4 border-bottom pb-2">POS Retail - Stored Procedure & Trigger</h2>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert alert-warning fw-bold">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="row">
            <div class="col-md-4">
                <div class="card shadow-sm mb-4">
                    <div class="card-header bg-primary text-white fw-bold">Buka Transaksi</div>
                    <div class="card-body">
                        <form action="/transaksi" method="POST">
                            <input type="number" name="id_transaksi" class="form-control form-control-sm mb-2" placeholder="ID Transaksi Baru" required>
                            <input type="number" name="id_pelanggan" class="form-control form-control-sm mb-2" placeholder="ID Pelanggan (1 atau 2)" required>
                            <select name="id_produk" class="form-select form-select-sm mb-2">
                                {% for p in produk %}
                                <option value="{{ p[0] }}">{{ p[1] }} (Rp{{ p[2] }}) - Stok: {{ p[3] }}</option>
                                {% endfor %}
                            </select>
                            <input type="number" name="jumlah" class="form-control form-control-sm mb-3" placeholder="Jumlah Beli" required>
                            <button type="submit" class="btn btn-success w-100">Proses Belanja</button>
                        </form>
                    </div>
                </div>
            </div>

            <div class="col-md-8">
                <div class="card shadow-sm mb-4">
                    <div class="card-header bg-dark text-white fw-bold">Kondisi Stok Real-Time</div>
                    <table class="table table-sm mb-0">
                        <thead class="table-secondary"><tr><th>ID</th><th>Produk</th><th>Stok</th></tr></thead>
                        <tbody>
                            {% for p in produk %}
                            <tr><td>{{ p[0] }}</td><td>{{ p[1] }}</td><td class="fw-bold text-danger">{{ p[3] }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <div class="card shadow-sm">
                    <div class="card-header bg-danger text-white fw-bold">Log Trigger Audit Stok</div>
                    <table class="table table-sm mb-0">
                        <thead class="table-secondary"><tr><th>Log ID</th><th>Produk ID</th><th>Lama</th><th>Baru</th><th>Waktu</th></tr></thead>
                        <tbody>
                            {% for l in log %}
                            <tr><td>{{ l[0] }}</td><td>{{ l[1] }}</td><td>{{ l[2] }}</td><td>{{ l[3] }}</td><td>{{ l[4] }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id_produk, nama_produk, harga, stok FROM produk")
    produk = cur.fetchall()
    cur.execute("SELECT id_log, id_produk, stok_lama, stok_baru, waktu FROM log_stok ORDER BY id_log DESC")
    log = cur.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, produk=produk, log=log)

@app.route('/transaksi', methods=['POST'])
def transaksi():
    id_trans = int(request.form['id_transaksi'])
    id_pel = int(request.form['id_pelanggan'])
    id_prod = int(request.form['id_produk'])
    jumlah = int(request.form['jumlah'])
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("CALL sp_proses_transaksi(?, ?, @status)", (id_trans, id_pel))
        cur.execute("SELECT @status")
        status = cur.fetchone()[0]
        
        if "ERROR" in status:
            flash(status)
        else:
            cur.execute("SELECT harga FROM produk WHERE id_produk = ?", (id_prod,))
            harga = cur.fetchone()[0]
            cur.execute("INSERT INTO detail_transaksi (id_transaksi, id_produk, jumlah, subtotal) VALUES (?, ?, ?, ?)", (id_trans, id_prod, jumlah, harga * jumlah))
            conn.commit()
            flash(f"{status} Trigger otomatis memotong stok & mencatat log.")
    except mariadb.Error as e:
        flash(f"SQL Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
