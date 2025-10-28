# main.py
import os
import shutil
import mysql.connector
from mysql.connector import errorcode
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel, Canvas
from tkcalendar import Calendar
from PIL import Image, ImageTk, ImageDraw, ImageFont
import qrcode
from datetime import datetime, date

# ---------------- CONFIG (Update your MySQL credentials here) ----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Hawk_Mahip0",   # <-- change
    "database": "cinebook_db"
}
# -----------------------------------------------------------------------------

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTERS_DIR = os.path.join(BASE_DIR, "posters")
ADS_DIR = os.path.join(BASE_DIR, "ads")
os.makedirs(POSTERS_DIR, exist_ok=True)
os.makedirs(ADS_DIR, exist_ok=True)

# ---------------- SAFE IMAGE LOADER ----------------
def load_image_safe(rel_path, size):
    """Load image relative to BASE_DIR; return ImageTk.PhotoImage or None."""
    full = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full):
        print(f"[load_image_safe] Missing: {full}")
        return None
    try:
        img = Image.open(full).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print("Error loading image:", full, e)
        return None

# ---------------- PLACEHOLDER ADS ----------------
def ensure_ads_placeholders():
    files = os.listdir(ADS_DIR)
    if len([f for f in files if f.lower().endswith((".png",".jpg",".jpeg"))]) == 0:
        for i in range(1,4):
            path = os.path.join(ADS_DIR, f"ad{i}.png")
            if not os.path.exists(path):
                img = Image.new("RGB", (980,140), (40+i*30, 70+i*10, 100+i*5))
                d = ImageDraw.Draw(img)
                fnt = ImageFont.load_default()
                d.text((20,60), f"Place your ad in /ads/ad{i}.png", fill="white", font=fnt)
                img.save(path)

# ---------------- MYSQL SETUP ----------------
def ensure_database_and_tables():
    # create database if not present
    try:
        cnx = mysql.connector.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cur = cnx.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cur.close()
        cnx.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Database error", f"Could not ensure database: {e}")
        raise

    # create tables
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cur = cnx.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                description TEXT,
                rating VARCHAR(20),
                tags VARCHAR(255),
                poster_path VARCHAR(255),
                section ENUM('Now Showing','Upcoming'),
                release_date DATE
            ) ENGINE=InnoDB;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                movie_id INT,
                show_date DATE,
                show_time TIME,
                audi INT,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                show_id INT,
                seat_no VARCHAR(10),
                is_booked TINYINT(1) DEFAULT 0,
                FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                show_id INT,
                seat_no VARCHAR(10),
                customer_name VARCHAR(255),
                booked_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        cnx.commit()
        cur.close()
        cnx.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Database error", f"MySQL error: {e}")
        raise

# ---------------- SEED SAMPLE MOVIES (FORCE UPDATE) ----------------
def seed_sample_movies():
    cnx = mysql.connector.connect(**DB_CONFIG)
    cur = cnx.cursor()
    
    # CLEAR EXISTING DATA
    cur.execute("DELETE FROM bookings")
    cur.execute("DELETE FROM seats")
    cur.execute("DELETE FROM shows")
    cur.execute("DELETE FROM movies")
    
    sample = [
        # Now Showing (Jan–May)
        ("Interstellar", "A team travels through a wormhole to find a new home for humanity.", "95%", "IMAX, Dolby Atmos", os.path.join("posters","interstellar.png"), "Now Showing", "2026-01-15"),
        ("Oppenheimer", "The story of J. Robert Oppenheimer.", "93%", "IMAX, Dolby Vision", os.path.join("posters","oppenheimer.png"), "Now Showing", "2026-02-12"),
        ("KGF", "Rise of a man from poverty to power.", "88%", "Dolby", os.path.join("posters","kgf.png"), "Now Showing", "2026-03-05"),
        ("Fast X", "High-octane car action.", "75%", "IMAX", os.path.join("posters","fast_x.png"), "Now Showing", "2026-03-22"),
        ("Ford v Ferrari", "Racing rivalry drama.", "89%", "Dolby", os.path.join("posters","ford_v_ferrari.png"), "Now Showing", "2026-04-02"),
        ("Avatar: Way of Water", "Return to Pandora.", "90%", "IMAX, Dolby Vision", os.path.join("posters","avatar_way_of_water.png"), "Now Showing", "2026-04-20"),
        ("Hangover", "Comedy of errors.", "80%", "Dolby", os.path.join("posters","hangover.png"), "Now Showing", "2026-05-06"),
        ("Ratatouille", "A rat dreams of being a chef.", "92%", "Dolby 7.1", os.path.join("posters","ratatouille.png"), "Now Showing", "2026-05-18"),
        ("Dishoom", "Action-cop movie.", "74%", "Dolby", os.path.join("posters","dishoom.png"), "Now Showing", "2026-05-26"),
        ("John Wick 4", "Assassin saga continues.", "91%", "Dolby Atmos", os.path.join("posters","johnwick4.png"), "Now Showing", "2026-05-28"),

        # Upcoming (Jun–Dec) - CHANGES MADE HERE
        ("Kung Fu Panda", "Po returns for more adventure.", "N/A", "Dolby Atmos", os.path.join("posters","kung_fu_panda.png"), "Upcoming", "2026-06-10"),
        ("Tron Legacy", "Sam's journey in cyberworld.", "N/A", "IMAX", os.path.join("posters","tron_legacy.png"), "Upcoming", "2026-07-01"),  # MOVED FROM SEPT 25
        ("Aladdin", "A street rat finds a magic lamp.", "N/A", "Dolby Vision", os.path.join("posters","aladdin.png"), "Upcoming", "2026-07-20"),
        ("Cruella", "Origin story of Cruella.", "N/A", "Dolby Vision", os.path.join("posters","cruella.png"), "Upcoming", "2026-08-05"),
        ("Hobbit", "An epic fantasy journey of Bilbo Baggins.", "N/A", "Dolby", os.path.join("posters","hobbit.png"), "Upcoming", "2026-08-25"),  # CHANGED FROM LORD OF THE RINGS
        ("Alien Covenant", "Horror sci-fi returns.", "N/A", "IMAX", os.path.join("posters","alien_covenant.png"), "Upcoming", "2026-09-10"),
        ("Inglorious Bastards", "Jewish soldiers to commit violent acts of retribution against the Nazis.", "N/A", "Dolby 7.1", os.path.join("posters","inglorious_bastards.png"), "Upcoming", "2026-09-25"),  # MOVED FROM JULY 1
        ("Avatar : Fire And Ash", "Pandora saga continues.", "N/A", "IMAX", os.path.join("posters","avatar3.png"), "Upcoming", "2026-10-10"),
    ]

    insert_q = """INSERT INTO movies (title, description, rating, tags, poster_path, section, release_date)
                  VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    cur.executemany(insert_q, sample)
    cnx.commit()
    cur.close()
    cnx.close()
    print("Database updated with new movie list!")

# ---------------- ADMIN: copy poster/ad into folder and return path ----------------
def admin_copy_file_to_folder(src_path, folder):
    if not os.path.exists(src_path):
        return None
    os.makedirs(folder, exist_ok=True)
    fname = os.path.basename(src_path)
    dst = os.path.join(folder, fname)
    # if filename already exists, add suffix
    base, ext = os.path.splitext(fname)
    count = 1
    while os.path.exists(dst):
        dst = os.path.join(folder, f"{base}_{count}{ext}")
        count += 1
    shutil.copyfile(src_path, dst)
    # return relative path from BASE_DIR
    return os.path.relpath(dst, BASE_DIR)

# ---------------- QR + Receipt generator ----------------
def generate_ticket_image(movie_title, date_str, time_str, audi, seats, booking_id):
    # build an image showing the info + a QR code
    w, h = 800, 500
    img = Image.new("RGB", (w, h), (20,20,20))
    d = ImageDraw.Draw(img)
    font_title = ImageFont.load_default()
    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    d.text((30,30), f"CineBook Ticket #{booking_id}", fill="white", font=font_title)
    d.text((30,80), f"Movie: {movie_title}", fill="white", font=font_sub)
    d.text((30,110), f"Date: {date_str}    Time: {time_str}", fill="white", font=font_sub)
    d.text((30,140), f"Audi: {audi}    Seats: {', '.join(seats)}", fill="white", font=font_sub)
    # QR payload: basic text
    qr_payload = f"{movie_title}|{date_str}|{time_str}|{audi}|{','.join(seats)}|ID:{booking_id}"
    qr = qrcode.make(qr_payload)
    qr = qr.resize((200,200))
    img.paste(qr, (w-240, 60))
    return img

# ---------------- GUI App ----------------
class CineBookApp:
    def __init__(self, root):
        self.root = root
        root.title("CineBook — Movie Ticket Booking")
        root.geometry("1200x760")
        root.configure(bg="#0f0f10")

        ensure_ads_placeholders()

        # ad images
        self.ad_images = []
        self.ad_index = 0
        self.load_ads()

        # top bar with Admin
        top = tk.Frame(root, bg="#0f0f10")
        top.pack(fill="x", padx=16, pady=10)
        tk.Label(top, text="CineBook", font=("Helvetica", 26, "bold"), fg="white", bg="#0f0f10").pack(side="left")
        tk.Button(top, text="Admin", command=self.open_admin_panel, bg="#333", fg="white").pack(side="right")

        # ad banner
        self.ad_label = tk.Label(root, bg="#0f0f10")
        self.ad_label.pack(pady=(0,12))
        self.rotate_ads()  # starts rotation via after()

        # main content (scrollable)
        content = tk.Frame(root, bg="#0f0f10")
        content.pack(fill="both", expand=True, padx=12, pady=(0,18))

        self.canvas = Canvas(content, bg="#0f0f10", highlightthickness=0)
        vbar = ttk.Scrollbar(content, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        self.inner = tk.Frame(self.canvas, bg="#0f0f10")
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # sections
        self.build_sections()

    # ---------------- ads ----------------
    def load_ads(self):
        files = [f for f in os.listdir(ADS_DIR) if f.lower().endswith((".png",".jpg",".jpeg"))]
        for f in files:
            rel = os.path.join("ads", f)
            img = load_image_safe(rel, (980,140))
            if img:
                self.ad_images.append(img)

    def rotate_ads(self):
        if self.ad_images:
            img = self.ad_images[self.ad_index % len(self.ad_images)]
            self.ad_label.config(image=img)
            self.ad_label.image = img
            self.ad_index += 1
        else:
            # show a simple text if no ads
            self.ad_label.config(text="Place ad images in /ads/", fg="white", bg="#0f0f10", font=("Arial", 14))
        self.root.after(4000, self.rotate_ads)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # ---------------- content build ----------------
    def build_sections(self):
        # Now Showing
        tk.Label(self.inner, text="NOW SHOWING", font=("Helvetica", 18, "bold"), fg="#ffffff", bg="#0f0f10").pack(anchor="w", pady=(6,8))
        self.populate_movie_grid("Now Showing")

        tk.Label(self.inner, text="UPCOMING", font=("Helvetica", 18, "bold"), fg="#ffffff", bg="#0f0f10").pack(anchor="w", pady=(18,8))
        self.populate_movie_grid("Upcoming")

    def populate_movie_grid(self, section):
        grid = tk.Frame(self.inner, bg="#0f0f10")
        grid.pack(padx=8, pady=6, fill="x")
        cnx = mysql.connector.connect(**DB_CONFIG)
        cur = cnx.cursor()
        cur.execute("SELECT id, title, description, rating, tags, poster_path, section, release_date FROM movies WHERE section=%s", (section,))
        rows = cur.fetchall()
        cur.close()
        cnx.close()

        cols = 4
        for i, row in enumerate(rows):
            mid, title, desc, rating, tags, poster_path, sect, rdate = row
            card = tk.Frame(grid, bg="#141414", bd=0)
            card.grid(row=i//cols, column=i%cols, padx=12, pady=12, sticky="n")

            poster_img = load_image_safe(poster_path, (160,240))
            if poster_img is None:
                # create simple fallback image
                img = Image.new("RGB", (160,240), (30,30,30))
                d = ImageDraw.Draw(img)
                f = ImageFont.load_default()
                d.text((18,110), "No Poster", fill="white", font=f)
                poster_img = ImageTk.PhotoImage(img)
            btn = tk.Button(card, image=poster_img, text=title, compound="top", fg="white", bg="#141414", bd=0,
                            command=lambda m_id=mid: self.open_movie_window(m_id))
            btn.image = poster_img
            btn.pack()
            tk.Label(card, text=title, fg="white", bg="#141414", font=("Helvetica", 11, "bold")).pack(pady=(6,0))
            tk.Label(card, text=f"RT: {rating}", fg="#bdbdbd", bg="#141414").pack()
            tk.Label(card, text=tags, fg="#9aa0a6", bg="#141414", wraplength=160).pack(pady=(4,8))

    # ---------------- movie detail window ----------------
    def open_movie_window(self, movie_id):
        cnx = mysql.connector.connect(**DB_CONFIG)
        cur = cnx.cursor()
        cur.execute("SELECT id, title, description, rating, tags, poster_path, section, release_date FROM movies WHERE id=%s", (movie_id,))
        row = cur.fetchone()
        cur.close()
        cnx.close()
        if not row:
            messagebox.showerror("Error", "Movie not found")
            return
        mid, title, desc, rating, tags, poster_path, section, rdate = row

        win = Toplevel(self.root)
        win.title(title)
        win.geometry("900x620")
        win.configure(bg="#0d0d0d")

        left = tk.Frame(win, bg="#0d0d0d")
        left.pack(side="left", padx=18, pady=18)
        right = tk.Frame(win, bg="#0d0d0d")
        right.pack(side="right", fill="both", expand=True, padx=18, pady=18)

        poster_img = load_image_safe(poster_path, (320,480))
        if poster_img:
            p_lbl = tk.Label(left, image=poster_img, bg="#0d0d0d")
            p_lbl.image = poster_img
            p_lbl.pack()
        else:
            tk.Label(left, text="No Poster", fg="white", bg="#0d0d0d").pack()

        tk.Label(right, text=title, font=("Helvetica", 22, "bold"), fg="white", bg="#0d0d0d").pack(anchor="nw")
        tk.Label(right, text=desc or "No description", fg="#ccc", bg="#0d0d0d", wraplength=420, justify="left").pack(anchor="nw", pady=(8,12))
        tk.Label(right, text=f"Rating (RT): {rating}", fg="#eee", bg="#0d0d0d").pack(anchor="nw", pady=2)
        tk.Label(right, text=f"Tags: {tags}", fg="#eee", bg="#0d0d0d").pack(anchor="nw", pady=2)
        tk.Label(right, text=f"Release: {rdate}", fg="#eee", bg="#0d0d0d").pack(anchor="nw", pady=2)

        # date picker
        tk.Label(right, text="Choose Date:", fg="white", bg="#0d0d0d").pack(anchor="nw", pady=(16,2))
        date_var = tk.StringVar(value="Select date")
        tk.Button(right, textvariable=date_var, width=20, bg="#1f6feb", fg="white",
                  command=lambda: open_calendar_popup(win, section, lambda d: date_var.set(d))).pack(anchor="nw")

        # time picker
        tk.Label(right, text="Choose Time:", fg="white", bg="#0d0d0d").pack(anchor="nw", pady=(12,2))
        times = ["10:00:00", "13:30:00", "16:00:00", "19:30:00", "22:00:00"]
        time_var = tk.StringVar(value=times[0])
        ttk.Combobox(right, textvariable=time_var, values=times, width=18).pack(anchor="nw")

        # audi
        tk.Label(right, text="Audi:", fg="white", bg="#0d0d0d").pack(anchor="nw", pady=(12,2))
        audi_var = tk.StringVar(value="1")
        ttk.Combobox(right, textvariable=audi_var, values=[str(i) for i in range(1,9)], width=18).pack(anchor="nw")

        # button seat selection
        tk.Button(right, text="Open Seats", bg="#ff4b4b", fg="white", width=20,
                  command=lambda: open_seat_window(movie_id, title, section, date_var.get(), time_var.get(), audi_var.get())).pack(anchor="nw", pady=18)

    # ---------------- ADMIN PANEL ----------------
    def open_admin_panel(self):
        win = Toplevel(self.root)
        win.title("Admin Panel")
        win.geometry("700x520")
        win.configure(bg="#121212")

        # left: movie list
        left = tk.Frame(win, bg="#121212", width=300)
        left.pack(side="left", fill="y", padx=10, pady=10)
        right = tk.Frame(win, bg="#121212")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left, text="Movies (editable)", fg="white", bg="#121212", font=("Helvetica", 12, "bold")).pack(anchor="nw")
        listbox = tk.Listbox(left, width=36, height=24)
        listbox.pack(pady=8)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cur = cnx.cursor()
        cur.execute("SELECT id, title FROM movies")
        rows = cur.fetchall()
        for r in rows:
            listbox.insert("end", f"{r[0]}: {r[1]}")
        cur.close()
        cnx.close()

        # right: edit fields
        tk.Label(right, text="Edit / Add Movie", fg="white", bg="#121212", font=("Helvetica", 12, "bold")).pack(anchor="nw")
        f_title = tk.Entry(right, width=48)
        f_title.pack(pady=6)
        f_desc = tk.Text(right, height=6, width=48)
        f_desc.pack(pady=6)
        f_rating = tk.Entry(right, width=20)
        f_rating.pack(pady=6)
        f_tags = tk.Entry(right, width=48)
        f_tags.pack(pady=6)
        f_section = ttk.Combobox(right, values=["Now Showing", "Upcoming"], width=20)
        f_section.pack(pady=6)
        f_release = tk.Entry(right, width=20)
        f_release.pack(pady=6)
        poster_path_var = tk.StringVar(value="")

        def choose_poster():
            p = filedialog.askopenfilename(title="Select Poster Image", filetypes=[("Images","*.png;*.jpg;*.jpeg")])
            if p:
                rel = admin_copy_file_to_folder(p, POSTERS_DIR)
                poster_path_var.set(rel)
                messagebox.showinfo("Poster added", f"Poster copied to {rel}")

        tk.Button(right, text="Choose Poster (copy)", command=choose_poster, bg="#2c7be5", fg="white").pack(pady=4)
        tk.Label(right, textvariable=poster_path_var, fg="white", bg="#121212").pack()

        def on_list_select(evt):
            sel = listbox.curselection()
            if not sel: return
            text = listbox.get(sel[0])
            mid = int(text.split(":")[0])
            cnx = mysql.connector.connect(**DB_CONFIG)
            cur = cnx.cursor()
            cur.execute("SELECT title, description, rating, tags, poster_path, section, release_date FROM movies WHERE id=%s", (mid,))
            r = cur.fetchone()
            cur.close(); cnx.close()
            if r:
                f_title.delete(0,"end"); f_title.insert(0,r[0])
                f_desc.delete("1.0","end"); f_desc.insert("1.0", r[1] or "")
                f_rating.delete(0,"end"); f_rating.insert(0,r[2] or "")
                f_tags.delete(0,"end"); f_tags.insert(0,r[3] or "")
                poster_path_var.set(r[4] or "")
                f_section.set(r[5] or "Now Showing")
                f_release.delete(0,"end"); f_release.insert(0, r[6] or "")

        listbox.bind("<<ListboxSelect>>", on_list_select)

        def save_movie():
            title = f_title.get().strip()
            desc = f_desc.get("1.0","end").strip()
            rating = f_rating.get().strip()
            tags = f_tags.get().strip()
            poster_rel = poster_path_var.get().strip()
            section = f_section.get().strip()
            release = f_release.get().strip() or None
            if not title:
                messagebox.showwarning("Missing", "Title required")
                return
            sel = listbox.curselection()
            cnx = mysql.connector.connect(**DB_CONFIG)
            cur = cnx.cursor()
            if sel:
                mid = int(listbox.get(sel[0]).split(":")[0])
                cur.execute("""UPDATE movies SET title=%s, description=%s, rating=%s, tags=%s, poster_path=%s, section=%s, release_date=%s WHERE id=%s""",
                            (title, desc, rating, tags, poster_rel, section, release, mid))
                messagebox.showinfo("Saved", "Movie updated")
            else:
                cur.execute("""INSERT INTO movies (title, description, rating, tags, poster_path, section, release_date) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                            (title, desc, rating, tags, poster_rel, section, release))
                messagebox.showinfo("Saved", "Movie added")
            cnx.commit()
            cur.close()
            cnx.close()
            win.destroy()
            # refresh main UI
            self.refresh_main()

        def delete_movie():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Select", "Select a movie to delete")
                return
            mid = int(listbox.get(sel[0]).split(":")[0])
            if messagebox.askyesno("Confirm", "Delete movie and all its shows/bookings?"):
                cnx = mysql.connector.connect(**DB_CONFIG)
                cur = cnx.cursor()
                cur.execute("DELETE FROM movies WHERE id=%s", (mid,))
                cnx.commit()
                cur.close(); cnx.close()
                win.destroy()
                self.refresh_main()

        btn_frame = tk.Frame(right, bg="#121212")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Save", command=save_movie, bg="#2ecc71", fg="white").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Delete", command=delete_movie, bg="#ff4b4b", fg="white").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Close", command=win.destroy, bg="#888", fg="white").pack(side="left", padx=6)

    def refresh_main(self):
        # simply redraw the inner area
        for w in self.inner.winfo_children():
            w.destroy()
        self.build_sections()

# ---------------- calendar popup (section-aware) ----------------
def open_calendar_popup(parent, section, on_select):
    cal_win = Toplevel(parent)
    cal_win.title("Select Date")
    cal_win.geometry("360x360")
    if section == "Now Showing":
        mind = date(2026,1,1); maxd = date(2026,5,31)
    else:
        mind = date(2026,6,1); maxd = date(2026,12,31)
    cal = Calendar(cal_win, selectmode='day', year=mind.year, month=mind.month, day=mind.day,
                   mindate=mind, maxdate=maxd, date_pattern='yyyy-mm-dd')
    cal.pack(pady=16)
    def confirm():
        on_select(cal.get_date())
        cal_win.destroy()
    tk.Button(cal_win, text="Confirm", command=confirm, bg="#2c7be5", fg="white").pack(pady=10)

# ---------------- seat window, bookings, receipts ----------------
def open_seat_window(movie_id, title, section, chosen_date, chosen_time, audi):
    if not chosen_date or chosen_date == "Select date":
        messagebox.showwarning("No date", "Please select a date first.")
        return
    # create/find show & seats
    cnx = mysql.connector.connect(**DB_CONFIG)
    cur = cnx.cursor()
    cur.execute("SELECT id FROM shows WHERE movie_id=%s AND show_date=%s AND show_time=%s AND audi=%s", (movie_id, chosen_date, chosen_time, int(audi)))
    r = cur.fetchone()
    if r:
        show_id = r[0]
    else:
        cur.execute("INSERT INTO shows (movie_id, show_date, show_time, audi) VALUES (%s,%s,%s,%s)", (movie_id, chosen_date, chosen_time, int(audi)))
        cnx.commit()
        show_id = cur.lastrowid
        for i in range(1,21):
            cur.execute("INSERT INTO seats (show_id, seat_no, is_booked) VALUES (%s,%s,%s)", (show_id, f"S{i:02}", 0))
        cnx.commit()

    cur.execute("SELECT seat_no, is_booked FROM seats WHERE show_id=%s ORDER BY id", (show_id,))
    seat_rows = cur.fetchall()
    cur.close(); cnx.close()

    # UI for seats
    win = Toplevel()
    win.title(f"Seats — {title}")
    win.geometry("720x560")
    win.configure(bg="#0f0f0f")
    tk.Label(win, text=f"{title}", font=("Helvetica", 16, "bold"), fg="white", bg="#0f0f0f").pack(pady=8)
    tk.Label(win, text=f"{chosen_date}  {chosen_time}   Audi {audi}", fg="#ccc", bg="#0f0f0f").pack()

    gridf = tk.Frame(win, bg="#0f0f0f")
    gridf.pack(pady=12)

    buttons = {}
    selected = set()

    def toggle(seat_no):
        cur_btn = buttons[seat_no]
        if cur_btn["bg"] == "red":
            return
        if seat_no in selected:
            cur_btn.config(bg="#333")
            selected.remove(seat_no)
        else:
            cur_btn.config(bg="#2ecc71")
            selected.add(seat_no)

    r = 0; c = 0
    for seat_no, is_booked in seat_rows:
        color = "red" if is_booked else "#333"
        b = tk.Button(gridf, text=f"{seat_no}\n🛋", width=8, height=3, bg=color, fg="white",
                      font=("Arial", 10), command=lambda s=seat_no: toggle(s))
        b.grid(row=r, column=c, padx=10, pady=8)
        buttons[seat_no] = b
        c += 1
        if c >= 5:
            c = 0; r += 1

    def confirm():
        if not selected:
            messagebox.showwarning("No seats", "Select at least one seat.")
            return
        cnx = mysql.connector.connect(**DB_CONFIG)
        cur = cnx.cursor()
        booked = []
        for s in selected:
            cur.execute("SELECT is_booked FROM seats WHERE show_id=%s AND seat_no=%s FOR UPDATE", (show_id, s))
            curval = cur.fetchone()
            if curval and curval[0] == 1:
                messagebox.showwarning("Taken", f"Seat {s} already booked.")
                continue
            cur.execute("UPDATE seats SET is_booked=1 WHERE show_id=%s AND seat_no=%s", (show_id, s))
            cur.execute("INSERT INTO bookings (show_id, seat_no) VALUES (%s,%s)", (show_id, s))
            booked.append(s)
        cnx.commit()
        # get last inserted booking id approx (mysql doesn't give a batch lastid easily) - we'll use max id of bookings for receipt id
        cur.execute("SELECT MAX(id) FROM bookings")
        last_booking_id = cur.fetchone()[0] or 0
        cur.close(); cnx.close()
        if booked:
            messagebox.showinfo("Booked", f"Booked seats: {', '.join(booked)}")
            # show receipt with QR
            receipt_img = generate_ticket_image(title, chosen_date, chosen_time, audi, booked, last_booking_id)
            show_receipt_window(receipt_img)
            win.destroy()
            # refresh main UI to show booked seats reflected next time
            app.refresh_main()
        else:
            messagebox.showwarning("No seats", "No seats booked (maybe already taken).")

    tk.Button(win, text="Confirm Booking", bg="#ff4b4b", fg="white", command=confirm).pack(pady=12)

# ---------------- receipt display/save ----------------
def show_receipt_window(img_pil):
    win = Toplevel()
    win.title("Ticket Receipt")
    win.geometry("820x560")
    win.configure(bg="#222")
    tk.Label(win, text="Ticket Receipt", fg="white", bg="#222", font=("Helvetica", 16, "bold")).pack(pady=8)
    tk_img = ImageTk.PhotoImage(img_pil)
    lbl = tk.Label(win, image=tk_img, bg="#222")
    lbl.image = tk_img
    lbl.pack()
    def save_png():
        fname = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image","*.png")], title="Save Ticket")
        if fname:
            img_pil.save(fname)
            messagebox.showinfo("Saved", f"Ticket saved to {fname}")
    tk.Button(win, text="Save Ticket as PNG", bg="#2ecc71", fg="white", command=save_png).pack(pady=10)

# ---------------- run initial setup and start app ----------------
if __name__ == "__main__":
    try:
        ensure_database_and_tables()
        seed_sample_movies()  # This will now CLEAR and RESEED the database
    except Exception as e:
        print("DB setup error:", e)
        raise

    ensure_ads_placeholders()

    root = tk.Tk()
    app = CineBookApp(root)
    root.mainloop()
