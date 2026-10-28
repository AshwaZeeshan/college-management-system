"""
profile_window.py  –  User self-service profile panel.

Features:
  • Profile photo upload for Students, Professors, and Lab Attendants
  • All personal fields fully editable (ID is read-only / auto-assigned)
  • Change Password tab for every role
  • Courses/Lab tabs removed — already visible on main screen
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import io
import auth
from db import get_connection

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

NAVY   = "#1a2744"
BLUE   = "#2980b9"
GREEN  = "#27ae60"
RED    = "#c0392b"
GREY   = "#7f8c8d"
ORANGE = "#f39c12"
BG     = "#f4f6f7"
WHITE  = "#ffffff"
LIGHT  = "#eaf0fb"
FONT   = "Helvetica"

PIC_SIZE = 110   # profile picture display size in pixels


# ── Widget helpers ────────────────────────────────────────────────────────── #

def _entry(parent, width=24, show=None):
    return tk.Entry(parent, font=(FONT, 10), width=width,
                    relief="flat", bd=0, bg=WHITE,
                    highlightthickness=1,
                    highlightbackground="#c5cfe4",
                    highlightcolor=BLUE, show=show)

def _combo(parent, values, width=22):
    c = ttk.Combobox(parent, values=values, width=width,
                     state="readonly", font=(FONT, 10))
    return c

def _btn(parent, text, command, color=BLUE, width=16):
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=WHITE, font=(FONT, 9, "bold"),
                     relief="flat", bd=0, cursor="hand2",
                     width=width, pady=6)

def _divider(parent, text):
    tk.Label(parent, text=f"  {text}  ", font=(FONT, 9, "bold"),
             bg=LIGHT, fg=NAVY, anchor="w", padx=8, pady=4
             ).pack(fill="x", padx=10, pady=(8, 2))


# ── Shared profile-picture widget ────────────────────────────────────────── #

class _PicWidget:
    """
    Reusable profile-picture panel.
    table_name  : 'students' | 'professors' | 'lab_attendants'
    pk_col      : primary-key column name
    pk_val      : the actual PK value for this record
    """
    def __init__(self, parent, blob, table_name, pk_col, pk_val):
        self._table   = table_name
        self._pk_col  = pk_col
        self._pk_val  = pk_val

        frame = tk.LabelFrame(parent, text="Profile Photo",
                              bg=BG, font=(FONT, 9, "bold"), fg=NAVY)
        frame.pack(side="left", padx=(0, 18), anchor="n")

        self._lbl = tk.Label(frame, bg=LIGHT, width=PIC_SIZE, height=PIC_SIZE,
                             text="No Photo", fg=GREY, font=(FONT, 8))
        self._lbl.pack(padx=8, pady=(8, 4))
        self._load(blob)

        _btn(frame, "📷  Upload", self._upload, color=BLUE, width=12
             ).pack(pady=(0, 8))

    def _load(self, blob):
        if not PIL_OK:
            self._lbl.config(text="PIL needed", image="")
            return
        if blob:
            try:
                img = Image.open(io.BytesIO(blob)).resize(
                    (PIC_SIZE, PIC_SIZE), Image.LANCZOS)
                self._photo = ImageTk.PhotoImage(img)
                self._lbl.config(image=self._photo, text="")
                return
            except Exception:
                pass
        self._lbl.config(text="No Photo", image="", fg=GREY)

    def _upload(self):
        if not PIL_OK:
            messagebox.showwarning("Unavailable",
                                   "Install Pillow (pip install pillow) to enable photos.")
            return
        path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.gif")]
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                blob = f.read()
            conn = get_connection()
            conn.execute(
                f"UPDATE {self._table} SET profile_pic=? WHERE {self._pk_col}=?",
                (blob, self._pk_val)
            )
            conn.commit()
            conn.close()
            self._load(blob)
            messagebox.showinfo("Uploaded", "Profile photo saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ── Change-password panel (shared by all roles) ───────────────────────────── #

def _build_pw_tab(parent, user_id: int, accent: str = BLUE):
    wrapper = tk.Frame(parent, bg=BG, padx=32, pady=20)
    wrapper.pack(fill="both", expand=True)

    tk.Label(wrapper, text="Change Your Password",
             font=(FONT, 12, "bold"), bg=BG, fg=NAVY
             ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

    fields = {}
    for i, (lbl, key) in enumerate([
        ("Current Password",      "cur"),
        ("New Password",          "new"),
        ("Confirm New Password",  "cnf"),
    ], start=1):
        tk.Label(wrapper, text=lbl, font=(FONT, 9, "bold"),
                 bg=BG, fg=NAVY).grid(row=i, column=0, sticky="w",
                                      padx=(0, 12), pady=7)
        e = _entry(wrapper, width=28, show="●")
        e.grid(row=i, column=1, sticky="ew", pady=7)
        fields[key] = e

    tk.Label(wrapper,
             text="Requirements: 8+ chars · uppercase · digit · special char",
             font=(FONT, 8), bg=LIGHT, fg=GREY, padx=10, pady=6
             ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 2))

    err_lbl = tk.Label(wrapper, text="", font=(FONT, 9), bg=BG, fg=RED, wraplength=360)
    err_lbl.grid(row=5, column=0, columnspan=2, pady=2)
    ok_lbl  = tk.Label(wrapper, text="", font=(FONT, 9, "bold"), bg=BG, fg=GREEN)
    ok_lbl.grid(row=6, column=0, columnspan=2)

    def do_change():
        cur_pw = fields["cur"].get()
        new_pw = fields["new"].get()
        cnf_pw = fields["cnf"].get()

        conn = get_connection()
        row  = conn.execute(
            "SELECT password_hash, salt FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
        conn.close()

        if not row:
            err_lbl.config(text="User not found."); return
        if not auth.verify_password(cur_pw, row["password_hash"], row["salt"]):
            err_lbl.config(text="Current password is incorrect."); ok_lbl.config(text=""); return
        err = auth.validate_password(new_pw)
        if err:
            err_lbl.config(text=err); ok_lbl.config(text=""); return
        if new_pw != cnf_pw:
            err_lbl.config(text="New passwords do not match."); ok_lbl.config(text=""); return

        nh, ns = auth.hash_password(new_pw)
        conn2  = get_connection()
        try:
            conn2.execute(
                "UPDATE users SET password_hash=?, salt=? WHERE user_id=?",
                (nh, ns, user_id))
            conn2.commit()
            for w in fields.values():
                w.delete(0, tk.END)
            err_lbl.config(text="")
            ok_lbl.config(text="✔  Password changed successfully!")
        except Exception as ex:
            err_lbl.config(text=str(ex))
        finally:
            conn2.close()

    _btn(wrapper, "🔑  Change Password", do_change,
         color=accent, width=24).grid(row=7, column=0, columnspan=2, pady=(14, 0))
    wrapper.columnconfigure(1, weight=1)


# ── Standalone Change-Password window (used by Admin) ────────────────────── #

class ChangePasswordWindow(tk.Toplevel):
    def __init__(self, master, user: dict):
        super().__init__(master)
        self.title("Change Password")
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(bg=BG)

        banner = tk.Frame(self, bg=NAVY)
        banner.pack(fill="x")
        tk.Label(banner, text="🔑  Change Password",
                 font=(FONT, 13, "bold"), bg=NAVY, fg=WHITE).pack(pady=13)

        _build_pw_tab(self, user["user_id"], accent=RED)


# ══════════════════════════════════════════════════════════════════════════════
#  Main profile window
# ══════════════════════════════════════════════════════════════════════════════

class ProfileWindow(tk.Toplevel):

    def __init__(self, master, user: dict, role_id):
        super().__init__(master)
        self.user    = user
        self.role_id = role_id
        self.role    = user["role"]

        self.title(f"My Profile – {self.role.replace('_',' ').title()}")
        self.geometry("700x600")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        colors = {"student": GREEN, "professor": ORANGE, "lab_attendant": GREY}
        accent = colors.get(self.role, NAVY)

        banner = tk.Frame(self, bg=accent)
        banner.pack(fill="x")
        tk.Label(banner,
                 text=f"👤  {self.role.replace('_',' ').title()} Profile",
                 font=(FONT, 13, "bold"), bg=accent, fg=WHITE).pack(pady=13)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=8)

        info_tab = tk.Frame(nb, bg=BG)
        nb.add(info_tab, text="  My Information  ")

        pw_tab = tk.Frame(nb, bg=BG)
        nb.add(pw_tab, text="  🔑 Change Password  ")

        if self.role == "student":
            self._build_student(info_tab, accent)
        elif self.role == "professor":
            self._build_professor(info_tab, accent)
        elif self.role == "lab_attendant":
            self._build_lab(info_tab, accent)

        _build_pw_tab(pw_tab, self.user["user_id"], accent)

    # ── scrollable body helper ────────────────────────────────────────────── #

    def _scrollable(self, parent):
        canvas = tk.Canvas(parent, bg=BG, bd=0, highlightthickness=0)
        sb     = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=BG, padx=14, pady=8)
        cw   = canvas.create_window((0, 0), window=body, anchor="nw")
        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cw, width=canvas.winfo_width())
        body.bind("<Configure>", _resize)
        return body

    # ── field grid builder ────────────────────────────────────────────────── #

    def _field_grid(self, parent, cols_def, existing_row):
        """
        cols_def: list of (db_key, label, options_or_None)
        Returns dict of {key: widget}
        """
        fields = {}
        grid   = tk.Frame(parent, bg=BG, padx=10)
        grid.pack(fill="x", pady=4)
        for i, (key, lbl, opts) in enumerate(cols_def):
            tk.Label(grid, text=lbl, font=(FONT, 9, "bold"),
                     bg=BG, fg=NAVY).grid(row=i, column=0, sticky="w",
                                          padx=(0, 12), pady=5)
            if opts:
                w = _combo(grid, opts, width=22)
                w.set(str(existing_row[key]) if existing_row[key] is not None else "")
            else:
                w = _entry(grid, width=24)
                w.insert(0, str(existing_row[key]) if existing_row[key] is not None else "")
            w.grid(row=i, column=1, sticky="ew", pady=5)
            fields[key] = w
        grid.columnconfigure(1, weight=1)
        return fields

    # ── save/feedback row ────────────────────────────────────────────────── #

    def _save_row(self, parent, save_fn, accent):
        err = tk.Label(parent, text="", font=(FONT, 9),
                       bg=BG, fg=RED, wraplength=540)
        err.pack()
        ok  = tk.Label(parent, text="", font=(FONT, 9, "bold"),
                       bg=BG, fg=GREEN)
        ok.pack()
        _btn(parent, "💾  Save Changes", lambda: save_fn(err, ok),
             color=accent, width=20).pack(pady=8)

    # ════════════════════════════════════════════════════════════════════════
    #  STUDENT tab
    # ════════════════════════════════════════════════════════════════════════

    def _build_student(self, parent, accent):
        conn = get_connection()
        row  = conn.execute("SELECT * FROM students WHERE student_id=?",
                            (self.role_id,)).fetchone()
        conn.close()
        if not row:
            tk.Label(parent, text="Record not found.", bg=BG, fg=RED,
                     font=(FONT, 10)).pack(pady=40); return

        body = self._scrollable(parent)

        # ── Profile picture + ID banner ───────────────────────────────── #
        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", pady=(0, 6))

        _PicWidget(top, row["profile_pic"],
                   "students", "student_id", self.role_id)

        id_frame = tk.Frame(top, bg=BG)
        id_frame.pack(side="left", anchor="n", pady=4)
        tk.Label(id_frame, text=f"Student ID:  {row['student_id']}",
                 font=(FONT, 11, "bold"), bg=LIGHT, fg=NAVY,
                 padx=12, pady=6).pack(fill="x")
        tk.Label(id_frame,
                 text="Auto-assigned · cannot be changed",
                 font=(FONT, 8), bg=BG, fg=GREY).pack(anchor="w", pady=2)

        # ── Personal fields ───────────────────────────────────────────── #
        _divider(body, "Personal Details")
        cols = [
            ("first_name",      "First Name",       None),
            ("last_name",       "Last Name",         None),
            ("age",             "Age",               None),
            ("gender",          "Gender",            ["M", "F"]),
            ("department",      "Department",        ["CS","EE","ME","CE","BBA",
                                                      "Physics","Math","Other"]),
            ("gpa",             "GPA (0.0 – 4.0)",  None),
            ("city",            "City",              None),
            ("phone",           "Phone",             None),
            ("enrollment_year", "Enrollment Year",   None),
        ]
        fields = self._field_grid(body, cols, row)

        def _save(err_lbl, ok_lbl):
            data = {k: (w.get().strip() if hasattr(w,"get") else "") for k,w in fields.items()}
            errs = []
            for fn in [
                lambda: auth.validate_age(data["age"], 14),
                lambda: auth.validate_gpa(data["gpa"]),
                lambda: auth.validate_phone(data["phone"]),
                lambda: auth.validate_year(data["enrollment_year"]),
            ]:
                e = fn()
                if e: errs.append(e)
            if not data["first_name"]: errs.append("First name required.")
            if not data["last_name"]:  errs.append("Last name required.")
            if errs:
                err_lbl.config(text=" | ".join(errs)); ok_lbl.config(text=""); return
            c = get_connection()
            try:
                c.execute("""UPDATE students SET
                    first_name=?,last_name=?,age=?,gender=?,department=?,
                    gpa=?,city=?,phone=?,enrollment_year=?
                    WHERE student_id=?""",
                    (data["first_name"], data["last_name"],
                     int(data["age"]),   data["gender"],
                     data["department"], float(data["gpa"]),
                     data["city"],       data["phone"],
                     int(data["enrollment_year"]), self.role_id))
                c.commit()
                err_lbl.config(text="")
                ok_lbl.config(text="✔  Saved successfully!")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
            finally:
                c.close()

        self._save_row(body, _save, accent)

    # ════════════════════════════════════════════════════════════════════════
    #  PROFESSOR tab
    # ════════════════════════════════════════════════════════════════════════

    def _build_professor(self, parent, accent):
        conn = get_connection()
        row  = conn.execute("SELECT * FROM professors WHERE prof_id=?",
                            (self.role_id,)).fetchone()
        conn.close()
        if not row:
            tk.Label(parent, text="Record not found.", bg=BG, fg=RED,
                     font=(FONT, 10)).pack(pady=40); return

        body = self._scrollable(parent)

        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", pady=(0, 6))

        _PicWidget(top, row["profile_pic"],
                   "professors", "prof_id", self.role_id)

        id_frame = tk.Frame(top, bg=BG)
        id_frame.pack(side="left", anchor="n", pady=4)
        tk.Label(id_frame, text=f"Professor ID:  {row['prof_id']}",
                 font=(FONT, 11, "bold"), bg=LIGHT, fg=NAVY,
                 padx=12, pady=6).pack(fill="x")
        tk.Label(id_frame, text="Auto-assigned · cannot be changed",
                 font=(FONT, 8), bg=BG, fg=GREY).pack(anchor="w", pady=2)

        _divider(body, "Personal Details")
        cols = [
            ("first_name",   "First Name",   None),
            ("last_name",    "Last Name",    None),
            ("age",          "Age",          None),
            ("gender",       "Gender",       ["M", "F"]),
            ("department",   "Department",   ["CS","EE","ME","CE","BBA",
                                              "Physics","Math","Other"]),
            ("salary",       "Salary ($)",   None),
            ("city",         "City",         None),
            ("phone",        "Phone",        None),
            ("joining_year", "Joining Year", None),
        ]
        fields = self._field_grid(body, cols, row)

        def _save(err_lbl, ok_lbl):
            data = {k: (w.get().strip() if hasattr(w,"get") else "") for k,w in fields.items()}
            errs = []
            for fn in [
                lambda: auth.validate_age(data["age"], 22),
                lambda: auth.validate_salary(data["salary"]),
                lambda: auth.validate_phone(data["phone"]),
                lambda: auth.validate_year(data["joining_year"]),
            ]:
                e = fn()
                if e: errs.append(e)
            if errs:
                err_lbl.config(text=" | ".join(errs)); ok_lbl.config(text=""); return
            c = get_connection()
            try:
                c.execute("""UPDATE professors SET
                    first_name=?,last_name=?,age=?,gender=?,department=?,
                    salary=?,city=?,phone=?,joining_year=?
                    WHERE prof_id=?""",
                    (data["first_name"], data["last_name"],
                     int(data["age"]),   data["gender"],
                     data["department"], float(data["salary"]),
                     data["city"],       data["phone"],
                     int(data["joining_year"]), self.role_id))
                c.commit()
                err_lbl.config(text="")
                ok_lbl.config(text="✔  Saved successfully!")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
            finally:
                c.close()

        self._save_row(body, _save, accent)

    # ════════════════════════════════════════════════════════════════════════
    #  LAB ATTENDANT tab
    # ════════════════════════════════════════════════════════════════════════

    def _build_lab(self, parent, accent):
        conn = get_connection()
        row  = conn.execute("SELECT * FROM lab_attendants WHERE lab_id=?",
                            (self.role_id,)).fetchone()
        conn.close()
        if not row:
            tk.Label(parent, text="Record not found.", bg=BG, fg=RED,
                     font=(FONT, 10)).pack(pady=40); return

        body = self._scrollable(parent)

        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", pady=(0, 6))

        _PicWidget(top, row["profile_pic"],
                   "lab_attendants", "lab_id", self.role_id)

        id_frame = tk.Frame(top, bg=BG)
        id_frame.pack(side="left", anchor="n", pady=4)
        tk.Label(id_frame, text=f"Lab Attendant ID:  {row['lab_id']}",
                 font=(FONT, 11, "bold"), bg=LIGHT, fg=NAVY,
                 padx=12, pady=6).pack(fill="x")
        tk.Label(id_frame, text="Auto-assigned · cannot be changed",
                 font=(FONT, 8), bg=BG, fg=GREY).pack(anchor="w", pady=2)

        _divider(body, "Personal Details")
        cols = [
            ("first_name",   "First Name",  None),
            ("last_name",    "Last Name",   None),
            ("age",          "Age",         None),
            ("gender",       "Gender",      ["M", "F"]),
            ("lab_name",     "Lab Name",    ["Physics Lab","Chemistry Lab",
                                             "CS Lab","Bio Lab",
                                             "Electronics Lab","Other"]),
            ("shift",        "Shift",       ["Morning","Evening","Night"]),
            ("city",         "City",        None),
            ("phone",        "Phone",       None),
            ("joining_year", "Joining Year",None),
        ]
        fields = self._field_grid(body, cols, row)

        def _save(err_lbl, ok_lbl):
            data = {k: (w.get().strip() if hasattr(w,"get") else "") for k,w in fields.items()}
            errs = []
            for fn in [
                lambda: auth.validate_age(data["age"], 18),
                lambda: auth.validate_phone(data["phone"]),
                lambda: auth.validate_year(data["joining_year"]),
            ]:
                e = fn()
                if e: errs.append(e)
            if errs:
                err_lbl.config(text=" | ".join(errs)); ok_lbl.config(text=""); return
            c = get_connection()
            try:
                c.execute("""UPDATE lab_attendants SET
                    first_name=?,last_name=?,age=?,gender=?,lab_name=?,
                    shift=?,city=?,phone=?,joining_year=?
                    WHERE lab_id=?""",
                    (data["first_name"], data["last_name"],
                     int(data["age"]),   data["gender"],
                     data["lab_name"],   data["shift"],
                     data["city"],       data["phone"],
                     int(data["joining_year"]), self.role_id))
                c.commit()
                err_lbl.config(text="")
                ok_lbl.config(text="✔  Saved successfully!")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
            finally:
                c.close()

        self._save_row(body, _save, accent)