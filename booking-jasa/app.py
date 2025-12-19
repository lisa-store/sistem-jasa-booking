import streamlit as st
from datetime import date
import pandas as pd
import os, json

# ==========================================================
# USER STORAGE (JSON) - untuk Login/Register
# ==========================================================
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def load_users() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"admin": {"password": "admin123", "role": "admin"}}, f, indent=2)
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def register_user(username: str, password: str):
    username = username.strip()
    if not username:
        return False, "Username tidak boleh kosong."
    if " " in username:
        return False, "Username tidak boleh pakai spasi."
    if len(password) < 4:
        return False, "Password minimal 4 karakter."
    users = load_users()
    if username in users:
        return False, "Username sudah dipakai."
    users[username] = {"password": password, "role": "user"}
    save_users(users)
    return True, "Registrasi berhasil! Silakan login."

def init_auth():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "role" not in st.session_state:
        st.session_state.role = None
    if "username" not in st.session_state:
        st.session_state.username = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# ==========================================================
# OOP Models
# ==========================================================
class Jasa:
    def __init__(self, jasa_id: int, nama: str, kategori: str, harga: int, durasi_menit: int):
        self.jasa_id = jasa_id
        self.nama = nama
        self.kategori = kategori
        self.harga = harga
        self.durasi_menit = durasi_menit

    def label(self) -> str:
        return f"{self.nama} • {self.kategori} • Rp{self.harga:,} • {self.durasi_menit} menit"

class Pelanggan:
    def __init__(self, pelanggan_id: int, nama: str, email: str, no_hp: str, username: str):
        self.pelanggan_id = pelanggan_id
        self.nama = nama
        self.email = email
        self.no_hp = no_hp
        self.username = username  # pemilik booking

class Booking:
    STATUS_MENUNGGU = "Menunggu"
    STATUS_MENUNGGU_VERIF = "Menunggu Verifikasi"
    STATUS_DISETUJUI = "Disetujui"
    STATUS_DITOLAK = "Ditolak"
    STATUS_DIBATALKAN = "Dibatalkan"

    def __init__(self, booking_id: int, pelanggan: Pelanggan, jasa: Jasa, tanggal: date, jam: str, catatan: str = ""):
        self.booking_id = booking_id
        self.pelanggan = pelanggan
        self.jasa = jasa
        self.tanggal = tanggal
        self.jam = jam
        self.catatan = catatan

        # status awal
        self.status = Booking.STATUS_MENUNGGU

        # pembayaran (QRIS)
        self.metode_bayar = "-"
        self.total_bayar = jasa.harga
        self.bukti_bayar = "-"

    def set_status(self, status_baru: str):
        self.status = status_baru

    def ringkas(self) -> dict:
        return {
            "Booking ID": self.booking_id,
            "Tanggal": str(self.tanggal),
            "Jam": self.jam,
            "Status": self.status,
            "Jasa": self.jasa.nama,
            "Kategori": self.jasa.kategori,
            "Harga": self.jasa.harga,
            "Durasi (menit)": self.jasa.durasi_menit,
            "Pelanggan": self.pelanggan.nama,
            "Email": self.pelanggan.email,
            "No HP": self.pelanggan.no_hp,
            "Username": self.pelanggan.username,
            "Metode Bayar": self.metode_bayar,
            "Total Bayar": self.total_bayar,
            "Bukti Bayar": self.bukti_bayar,
            "Catatan": self.catatan,
        }

# ==========================================================
# App State
# ==========================================================
def init_data():
    if "jasa_list" not in st.session_state:
        st.session_state.jasa_list = [
            Jasa(1, "Service AC", "Rumah Tangga", 150_000, 60),
            Jasa(2, "Cuci Sofa", "Rumah Tangga", 250_000, 90),
            Jasa(3, "Fotografi Produk", "Kreatif", 500_000, 120),
            Jasa(4, "Les Matematika", "Edukasi", 120_000, 60),
            Jasa(5, "Makeup Wisuda", "Beauty", 300_000, 90),
            Jasa(6, "Servis Laptop", "Teknologi", 200_000, 60),
        ]
    if "pelanggan_list" not in st.session_state:
        st.session_state.pelanggan_list = []
    if "booking_list" not in st.session_state:
        st.session_state.booking_list = []
    if "next_pelanggan_id" not in st.session_state:
        st.session_state.next_pelanggan_id = 1
    if "next_booking_id" not in st.session_state:
        st.session_state.next_booking_id = 1001

def find_jasa_by_id(jasa_id: int):
    for j in st.session_state.jasa_list:
        if j.jasa_id == jasa_id:
            return j
    return None

def add_pelanggan(nama: str, email: str, no_hp: str, username: str) -> Pelanggan:
    p = Pelanggan(st.session_state.next_pelanggan_id, nama, email, no_hp, username)
    st.session_state.next_pelanggan_id += 1
    st.session_state.pelanggan_list.append(p)
    return p

def bentrok_jadwal(jasa: Jasa, tanggal: date, jam: str) -> bool:
    for b in st.session_state.booking_list:
        if (
            b.jasa.jasa_id == jasa.jasa_id
            and b.tanggal == tanggal
            and b.jam == jam
            and b.status != Booking.STATUS_DIBATALKAN
        ):
            return True
    return False

def buat_booking(pelanggan: Pelanggan, jasa: Jasa, tanggal: date, jam: str, catatan: str) -> Booking:
    b = Booking(st.session_state.next_booking_id, pelanggan, jasa, tanggal, jam, catatan)
    st.session_state.next_booking_id += 1
    st.session_state.booking_list.append(b)
    return b

def bookings_df():
    rows = [b.ringkas() for b in st.session_state.booking_list]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
        "Booking ID","Tanggal","Jam","Status","Jasa","Kategori","Harga","Durasi (menit)",
        "Pelanggan","Email","No HP","Username","Metode Bayar","Total Bayar","Bukti Bayar","Catatan"
    ])

# ==========================================================
# LOGIN / REGISTER PAGE
# ==========================================================
init_auth()

if not st.session_state.logged_in:
    st.set_page_config(page_title="Login - Booking Jasa", page_icon="🔐", layout="centered")
    st.title("🔐 Sistem Booking Jasa")
    st.caption("Silakan login atau buat akun baru.")

    tab_login, tab_reg = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", placeholder="Masukkan username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Masukkan password", key="login_pass")

        if st.button("Login", use_container_width=True, key="btn_login"):
            users = load_users()
            ok = username in users and users[username]["password"] == password
            if ok:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = users[username]["role"]
                st.success("Login berhasil.")
                st.rerun()
            else:
                st.error("Username atau password salah.")

    with tab_reg:
        new_user = st.text_input("Buat Username", placeholder="contoh: budi123", key="reg_user")
        new_pass = st.text_input("Buat Password", type="password", placeholder="minimal 4 karakter", key="reg_pass")

        if st.button("Buat Akun", use_container_width=True, key="btn_reg"):
            ok, msg = register_user(new_user, new_pass)
            if ok:
                st.success(msg)
                st.info("Silakan pindah ke tab Login untuk masuk.")
            else:
                st.error(msg)

    st.stop()

# ==========================================================
# MAIN UI
# ==========================================================
init_data()
st.set_page_config(page_title="Booking Jasa", page_icon="📅", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
.small-muted {color: rgba(255,255,255,0.65); font-size: 0.92rem;}
.kpi {padding: 14px 16px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.12);}
.kpi h3 {margin: 0; font-size: 0.95rem; opacity: 0.8; font-weight: 600;}
.kpi p {margin: 2px 0 0; font-size: 1.55rem; font-weight: 750;}
.hr {margin: 0.5rem 0 1rem; opacity: 0.15;}
</style>
""", unsafe_allow_html=True)

left, right = st.columns([1.2, 1])
with left:
    st.title("📅 Sistem Booking Jasa")
    st.markdown('<div class="small-muted">Aplikasi web berbasis OOP (Jasa • Pelanggan • Booking) menggunakan Python + Streamlit</div>', unsafe_allow_html=True)
with right:
    st.markdown("### ")
    st.info("💳 Pembayaran via QRIS + Verifikasi Admin", icon="✅")

st.divider()

# Sidebar
st.sidebar.header("⚙️ Navigasi")
st.sidebar.write(f"👤 User: **{st.session_state.username}**")
st.sidebar.write(f"🔑 Role: **{st.session_state.role}**")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    logout()
    st.rerun()

# Menu berdasarkan role
if st.session_state.role == "admin":
    menu = st.sidebar.radio("Menu", ["Buat Booking", "Booking Saya", "Pembayaran QRIS", "Daftar Booking (Admin)", "Kelola Jasa (Admin)"], index=0)
else:
    menu = st.sidebar.radio("Menu", ["Buat Booking", "Booking Saya", "Pembayaran QRIS"], index=0)

df = bookings_df()

# KPI
c1, c2, c3, c4 = st.columns(4)
total = len(st.session_state.booking_list)
menunggu = int((df["Status"] == Booking.STATUS_MENUNGGU).sum()) if total else 0
verif = int((df["Status"] == Booking.STATUS_MENUNGGU_VERIF).sum()) if total else 0
disetujui = int((df["Status"] == Booking.STATUS_DISETUJUI).sum()) if total else 0

with c1: st.markdown(f'<div class="kpi"><h3>Total Booking</h3><p>{total}</p></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="kpi"><h3>Menunggu</h3><p>{menunggu}</p></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="kpi"><h3>Menunggu Verif</h3><p>{verif}</p></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="kpi"><h3>Disetujui</h3><p>{disetujui}</p></div>', unsafe_allow_html=True)

st.markdown('<div class="hr">---</div>', unsafe_allow_html=True)

# ==========================================================
# MENU: BUAT BOOKING
# ==========================================================
if menu == "Buat Booking":
    st.subheader("➕ Buat Booking Baru")

    colA, colB = st.columns(2)
    with colA:
        st.markdown("#### Data Pelanggan")
        nama = st.text_input("Nama")
        email = st.text_input("Email")
        no_hp = st.text_input("No HP / WhatsApp")

    with colB:
        st.markdown("#### Pilih Jasa & Jadwal")
        jasa_map = {f"{j.jasa_id} — {j.label()}": j.jasa_id for j in st.session_state.jasa_list}
        jasa_key = st.selectbox("Jasa", list(jasa_map.keys()))
        tanggal = st.date_input("Tanggal", value=date.today())
        jam = st.selectbox("Jam", ["09:00","10:00","11:00","13:00","14:00","15:00","16:00","19:00","20:00"])
        catatan = st.text_area("Catatan (opsional)", placeholder="Contoh: alamat lengkap / kebutuhan khusus")

    jasa_obj = find_jasa_by_id(jasa_map[jasa_key])

    st.markdown("#### Ringkasan")
    r1, r2, r3 = st.columns(3)
    r1.metric("Jasa", jasa_obj.nama)
    r2.metric("Harga", f"Rp{jasa_obj.harga:,}")
    r3.metric("Durasi", f"{jasa_obj.durasi_menit} menit")

    if st.button("✅ Konfirmasi Booking", use_container_width=True):
        if not (nama.strip() and email.strip() and no_hp.strip()):
            st.error("Lengkapi data pelanggan (Nama, Email, No HP).")
        elif bentrok_jadwal(jasa_obj, tanggal, jam):
            st.warning("Jadwal bentrok: jasa ini sudah dibooking pada tanggal & jam tersebut. Coba pilih jam lain.")
        else:
            pelanggan = add_pelanggan(nama.strip(), email.strip(), no_hp.strip(), st.session_state.username)
            booking = buat_booking(pelanggan, jasa_obj, tanggal, jam, catatan.strip())
            st.success(f"Booking berhasil dibuat! ID: {booking.booking_id}")
            st.json(booking.ringkas())

# ==========================================================
# MENU: BOOKING SAYA
# ==========================================================
elif menu == "Booking Saya":
    st.subheader("📌 Booking Saya")
    if len(df) == 0:
        st.info("Belum ada booking.")
    else:
        my_df = df[df["Username"] == st.session_state.username].copy()
        if len(my_df) == 0:
            st.info("Belum ada booking atas akun ini.")
        else:
            st.dataframe(my_df, use_container_width=True, hide_index=True)
            csv = my_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV (Booking Saya)", data=csv, file_name="booking_saya.csv", mime="text/csv")

# ==========================================================
# MENU: PEMBAYARAN QRIS
# ==========================================================
elif menu == "Pembayaran QRIS":
    st.subheader("📱 Pembayaran via QRIS")

    if not os.path.exists(os.path.join("assets", "qris.jpg")):
        st.error("File QRIS belum ada. Taruh gambar di: assets/qris.jpg")
        st.stop()

    my_df = df[df["Username"] == st.session_state.username].copy()
    if len(my_df) == 0:
        st.info("Kamu belum punya booking.")
    else:
        st.info("Langkah: Scan QRIS → Bayar sesuai total → Upload bukti → Tunggu verifikasi admin.")
        st.image("assets/qris.jpg", caption="Scan QRIS untuk pembayaran", use_container_width=True)

        pilih_id = st.selectbox("Pilih Booking ID yang mau dibayar", my_df["Booking ID"].tolist())
        bukti = st.file_uploader("Upload bukti pembayaran (JPG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"])

        if st.button("✅ Kirim Bukti Pembayaran", use_container_width=True):
            target = None
            for b in st.session_state.booking_list:
                if b.booking_id == pilih_id and b.pelanggan.username == st.session_state.username:
                    target = b
                    break

            if not target:
                st.error("Booking tidak ditemukan.")
            elif bukti is None:
                st.error("Upload bukti pembayaran dulu.")
            else:
                target.metode_bayar = "QRIS"
                target.total_bayar = target.jasa.harga
                target.bukti_bayar = bukti.name
                target.status = Booking.STATUS_MENUNGGU_VERIF
                st.success("Bukti pembayaran terkirim. Menunggu verifikasi admin.")

# ==========================================================
# MENU: ADMIN - DAFTAR BOOKING
# ==========================================================
elif menu == "Daftar Booking (Admin)":
    if st.session_state.role != "admin":
        st.error("Halaman ini khusus admin.")
        st.stop()

    st.subheader("📋 Daftar Booking (Admin)")
    if len(df) == 0:
        st.info("Belum ada booking.")
        st.stop()

    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV (Semua Booking)", data=csv, file_name="booking_all.csv", mime="text/csv")

    st.divider()
    st.markdown("### Detail & Verifikasi Pembayaran")

    booking_ids = [b.booking_id for b in st.session_state.booking_list]
    pilih_id = st.selectbox("Pilih Booking ID", booking_ids)

    selected = None
    for b in st.session_state.booking_list:
        if b.booking_id == pilih_id:
            selected = b
            break

    if selected:
        st.json(selected.ringkas())

        status_baru = st.selectbox(
            "Update Status Booking",
            [Booking.STATUS_MENUNGGU, Booking.STATUS_MENUNGGU_VERIF, Booking.STATUS_DISETUJUI, Booking.STATUS_DITOLAK, Booking.STATUS_DIBATALKAN],
            index=[Booking.STATUS_MENUNGGU, Booking.STATUS_MENUNGGU_VERIF, Booking.STATUS_DISETUJUI, Booking.STATUS_DITOLAK, Booking.STATUS_DIBATALKAN].index(selected.status),
        )

        if st.button("🔄 Simpan Status", use_container_width=True):
            selected.set_status(status_baru)
            st.success("Status booking berhasil diupdate.")

        st.markdown("#### Verifikasi Pembayaran (QRIS)")
        aksi = st.selectbox("Aksi Verifikasi", ["-", "Verifikasi (Setujui)", "Tolak Pembayaran"])

        if st.button("✅ Proses Verifikasi", use_container_width=True):
            if aksi == "Verifikasi (Setujui)":
                selected.status = Booking.STATUS_DISETUJUI
                st.success("Pembayaran diverifikasi. Booking disetujui.")
            elif aksi == "Tolak Pembayaran":
                selected.status = Booking.STATUS_DITOLAK
                st.warning("Pembayaran ditolak.")
            else:
                st.info("Pilih aksi verifikasi dulu.")

# ==========================================================
# MENU: ADMIN - KELOLA JASA
# ==========================================================
else:
    if st.session_state.role != "admin":
        st.error("Halaman ini khusus admin.")
        st.stop()

    st.subheader("🧰 Kelola Jasa (Admin)")
    st.caption("Tambah jasa baru agar bisa dipilih saat booking.")

    jasa_df = pd.DataFrame([{
        "ID": j.jasa_id,
        "Nama": j.nama,
        "Kategori": j.kategori,
        "Harga": j.harga,
        "Durasi (menit)": j.durasi_menit
    } for j in st.session_state.jasa_list])

    st.dataframe(jasa_df, use_container_width=True, hide_index=True)

    st.markdown("#### Tambah Jasa Baru")
    with st.form("tambah_jasa"):
        c1, c2 = st.columns(2)
        with c1:
            nama_jasa = st.text_input("Nama Jasa")
            kategori = st.text_input("Kategori")
        with c2:
            harga = st.number_input("Harga (Rp)", min_value=0, step=10_000, value=100_000)
            durasi = st.number_input("Durasi (menit)", min_value=10, step=10, value=60)

        submit = st.form_submit_button("➕ Tambahkan", use_container_width=True)
        if submit:
            if not (nama_jasa.strip() and kategori.strip()):
                st.error("Nama jasa dan kategori wajib diisi.")
            else:
                new_id = max([j.jasa_id for j in st.session_state.jasa_list]) + 1
                st.session_state.jasa_list.append(
                    Jasa(new_id, nama_jasa.strip(), kategori.strip(), int(harga), int(durasi))
                )
                st.success("Jasa berhasil ditambahkan. Silakan cek tabel di atas.")


