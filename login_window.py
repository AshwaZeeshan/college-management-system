"""
login_window.py  –  Authentication UI (Login + Signup) before main app loads.
Maintains the existing colour palette while adding a professional polished look.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import auth

# ── Palette (same as main app) ─────────────────────────────────────────────
BG       = "#f4f6f7"
NAVY     = "#1a2744"
BLUE     = "#2980b9"
GREEN    = "#27ae60"
ORANGE   = "#f39c12"
RED      = "#c0392b"
GREY     = "#7f8c8d"
WHITE    = "#ffffff"
LIGHT    = "#eaf0fb"
FONT     = "Helvetica"


# ═══════════════════════════════════════════════════════════════════════════ #
#  Styled widget helpers                                                       #
# ═══════════════════════════════════════════════════════════════════════════ #

def _label(parent, text, bold=False, size=10, color=NAVY):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, font=(FONT, size, weight),
                    bg=BG, fg=color)


def _entry(parent, show=None, width=28):
    e = tk.Entry(parent, font=(FONT, 10), width=width,
                 relief="flat", bd=0, bg=WHITE,
                 highlightthickness=1,
                 highlightbackground="#c5cfe4",
                 highlightcolor=BLUE,
                 show=show)
    return e


def _btn(parent, text, command, color=BLUE, width=20):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=WHITE, activebackground=NAVY,
        activeforeground=WHITE, font=(FONT, 10, "bold"),
        relief="flat", bd=0, cursor="hand2",
        width=width, pady=6,
    )


def _combo(parent, values, width=26):
    c = ttk.Combobox(parent, values=values, width=width,
                     state="readonly", font=(FONT, 10))
    return c


def _row(parent, label, widget, r):
    _label(parent, label).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=4)
    widget.grid(row=r, column=1, pady=4, sticky="ew")


def _error_label(parent):
    lbl = tk.Label(parent, text="", font=(FONT, 9),
                   bg=BG, fg=RED, wraplength=340)
    return lbl


def _card(parent, title, width=420):
    """Centred white card with drop-shadow illusion."""
    outer = tk.Frame(parent, bg="#d0dcea", bd=0)
    outer.pack(pady=30, padx=40)

    inner = tk.Frame(outer, bg=WHITE, bd=0)
    inner.pack(padx=2, pady=2)

    header = tk.Frame(inner, bg=NAVY, height=52)
    header.pack(fill="x")
    tk.Label(header, text=title, font=(FONT, 14, "bold"),
             bg=NAVY, fg=WHITE).pack(pady=14)

    body = tk.Frame(inner, bg=BG, padx=24, pady=18)
    body.pack(fill="both", expand=True)

    return body


# ═══════════════════════════════════════════════════════════════════════════ #
#  Main Login / Signup window                                                  #
# ═══════════════════════════════════════════════════════════════════════════ #

class AuthWindow:
    """
    Shown before the main app.
    On successful authentication, stores the result in self.result and
    destroys the window, letting the caller read self.result.
    """

    def __init__(self):
        self.result = None          # (user_dict, role_id) after success

        self.root = tk.Tk()
        self.root.title("College Management System – Login")
        self.root.geometry("500x560")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._show_landing()
        self.root.mainloop()

    # ── Landing (choose action) ─────────────────────────────────────────── #

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _banner(self):
        tk.Frame(self.root, bg=NAVY, height=70).pack(fill="x")
        b = tk.Frame(self.root, bg=NAVY)
        # already packed above; use a label inside root temporarily
        for w in self.root.winfo_children():
            if isinstance(w, tk.Frame) and w.cget("bg") == NAVY:
                tk.Label(w, text="🎓  College Management System",
                         font=(FONT, 15, "bold"), bg=NAVY, fg=WHITE
                         ).pack(pady=18)
                break

    def _show_landing(self):
        self._clear()
        self.root.geometry("500x420")

        # Banner
        banner = tk.Frame(self.root, bg=NAVY)
        banner.pack(fill="x")
        tk.Label(banner, text="🎓  College Management System",
                 font=(FONT, 15, "bold"), bg=NAVY, fg=WHITE).pack(pady=18)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=60, pady=20)

        tk.Label(body, text="Welcome! Please choose an option.",
                 font=(FONT, 11), bg=BG, fg=GREY).pack(pady=(0, 20))

        _btn(body, "Login", self._show_login,  color=BLUE,  width=28).pack(pady=6)
        _btn(body, "Sign Up – Student",
             lambda: self._show_signup("student"), color=GREEN, width=28).pack(pady=6)
        _btn(body, "Sign Up – Professor",
             lambda: self._show_signup("professor"), color=ORANGE, width=28).pack(pady=6)
        _btn(body, "Sign Up – Lab Attendant",
             lambda: self._show_signup("lab_attendant"), color=GREY, width=28).pack(pady=6)

    # ── Login form ──────────────────────────────────────────────────────── #

    def _show_login(self):
        self._clear()
        self.root.geometry("500x400")

        banner = tk.Frame(self.root, bg=NAVY)
        banner.pack(fill="x")
        tk.Label(banner, text="🔐  Login", font=(FONT, 14, "bold"),
                 bg=NAVY, fg=WHITE).pack(pady=16)

        body = tk.Frame(self.root, bg=BG, padx=40, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Email", font=(FONT, 10, "bold"),
                 bg=BG, fg=NAVY).grid(row=0, column=0, sticky="w", pady=6)
        email_e = _entry(body)
        email_e.grid(row=0, column=1, pady=6)

        tk.Label(body, text="Password", font=(FONT, 10, "bold"),
                 bg=BG, fg=NAVY).grid(row=1, column=0, sticky="w", pady=6)
        pw_e = _entry(body, show="●")
        pw_e.grid(row=1, column=1, pady=6)

        err_lbl = _error_label(body)
        err_lbl.grid(row=2, column=0, columnspan=2, pady=4)

        def do_login():
            email = email_e.get().strip()
            pw    = pw_e.get()
            if not email or not pw:
                err_lbl.config(text="Please fill in all fields.")
                return
            try:
                user, role_id = auth.login(email, pw)
                self.result = (user, role_id)
                self.root.destroy()
            except auth.AccountDisabledError as e:
                err_lbl.config(
                    fg="#c0392b",
                    text="🚫  " + str(e)
                )
            except ValueError as e:
                err_lbl.config(text=str(e))

        _btn(body, "Login", do_login, color=BLUE, width=22).grid(
            row=3, column=0, columnspan=2, pady=(14, 6))
        _btn(body, "← Back", self._show_landing, color=GREY, width=22).grid(
            row=4, column=0, columnspan=2)

        body.columnconfigure(1, weight=1)

    # ── Signup dispatcher ───────────────────────────────────────────────── #

    def _show_signup(self, role: str):
        self._clear()

        builders = {
            "student":      self._signup_student,
            "professor":    self._signup_professor,
            "lab_attendant": self._signup_lab,
        }
        builders[role]()

    # ── Student signup ──────────────────────────────────────────────────── #

    def _signup_student(self):
        self.root.geometry("520x720")

        banner = tk.Frame(self.root, bg=GREEN)
        banner.pack(fill="x")
        tk.Label(banner, text="📝  Student Signup", font=(FONT, 14, "bold"),
                 bg=GREEN, fg=WHITE).pack(pady=14)

        canvas = tk.Canvas(self.root, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=BG, padx=36, pady=16)
        cw   = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_frame(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cw, width=canvas.winfo_width())
        body.bind("<Configure>", _on_frame)

        fields = {}
        rows   = [
            # student_id is REMOVED — assigned automatically starting at 101
            ("first_name",      "First Name",  None),
            ("last_name",       "Last Name",   None),
            ("age",             "Age",         None),
            ("gender",          "Gender",      ["M", "F"]),
            ("department",      "Department",  ["CS", "EE", "ME", "CE", "BBA", "Physics", "Math", "Other"]),
            ("gpa",             "GPA (0.0–4.0)", None),
            ("city",            "City",         None),
            ("phone",           "Phone",        None),
            ("enrollment_year", "Enrollment Year", None),
            ("email",           "Gmail / Email", None),
            ("password",        "Password",     None),
            ("confirm_pw",      "Confirm Password", None),
        ]

        for i, (key, lbl, opts) in enumerate(rows):
            tk.Label(body, text=lbl, font=(FONT, 9, "bold"),
                     bg=BG, fg=NAVY).grid(row=i, column=0, sticky="w", padx=(0,10), pady=4)
            if opts:
                w = _combo(body, opts)
            elif key in ("password", "confirm_pw"):
                w = _entry(body, show="●")
            else:
                w = _entry(body)
            w.grid(row=i, column=1, pady=4, sticky="ew")
            fields[key] = w

        # Show the user what ID they'll be assigned
        tk.Label(body,
                 text="ℹ  Your Student ID will be auto-assigned starting from 101.",
                 font=(FONT, 8), bg=BG, fg=GREY).grid(
            row=len(rows), column=0, columnspan=2, pady=2)

        err_lbl = _error_label(body)
        err_lbl.grid(row=len(rows)+1, column=0, columnspan=2, pady=4)

        def do_signup():
            data = {k: (w.get() if hasattr(w, "get") else "") for k, w in fields.items()}
            # validate
            errs = []
            e = auth.validate_email(data["email"])
            if e: errs.append(e)
            e = auth.validate_password(data["password"])
            if e: errs.append(e)
            if data["password"] != data["confirm_pw"]:
                errs.append("Passwords do not match.")
            e = auth.validate_age(data["age"], 14)
            if e: errs.append(e)
            e = auth.validate_gpa(data["gpa"])
            if e: errs.append(e)
            e = auth.validate_phone(data["phone"])
            if e: errs.append(e)
            e = auth.validate_year(data["enrollment_year"])
            if e: errs.append(e)
            if not data["first_name"] or not data["last_name"]:
                errs.append("First and last name are required.")
            if errs:
                err_lbl.config(text=" | ".join(errs))
                return
            try:
                auth.signup_student(data)
                messagebox.showinfo("Success",
                    "Student account created!\nYou can now login.")
                self._show_landing()
            except ValueError as ex:
                err_lbl.config(text=str(ex))

        btn_row = len(rows) + 2
        _btn(body, "Create Account", do_signup, color=GREEN, width=24).grid(
            row=btn_row, column=0, columnspan=2, pady=(10, 4))
        _btn(body, "← Back", self._show_landing, color=GREY, width=24).grid(
            row=btn_row+1, column=0, columnspan=2)
        body.columnconfigure(1, weight=1)

    # ── Professor signup ────────────────────────────────────────────────── #

    def _signup_professor(self):
        self.root.geometry("520x700")

        banner = tk.Frame(self.root, bg=ORANGE)
        banner.pack(fill="x")
        tk.Label(banner, text="📝  Professor Signup", font=(FONT, 14, "bold"),
                 bg=ORANGE, fg=WHITE).pack(pady=14)

        canvas   = tk.Canvas(self.root, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=BG, padx=36, pady=16)
        cw   = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_frame(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cw, width=canvas.winfo_width())
        body.bind("<Configure>", _on_frame)

        fields = {}
        rows   = [
            # prof_id is REMOVED — assigned automatically starting at 201
            ("first_name",   "First Name",   None),
            ("last_name",    "Last Name",    None),
            ("age",          "Age",          None),
            ("gender",       "Gender",       ["M", "F"]),
            ("department",   "Department",   ["CS", "EE", "ME", "CE", "BBA", "Physics", "Math", "Other"]),
            ("salary",       "Salary ($)",   None),
            ("city",         "City",         None),
            ("phone",        "Phone",        None),
            ("joining_year", "Joining Year", None),
            ("email",        "Gmail / Email",None),
            ("password",     "Password",     None),
            ("confirm_pw",   "Confirm Password", None),
        ]

        for i, (key, lbl, opts) in enumerate(rows):
            tk.Label(body, text=lbl, font=(FONT, 9, "bold"),
                     bg=BG, fg=NAVY).grid(row=i, column=0, sticky="w", padx=(0,10), pady=4)
            if opts:
                w = _combo(body, opts)
            elif key in ("password", "confirm_pw"):
                w = _entry(body, show="●")
            else:
                w = _entry(body)
            w.grid(row=i, column=1, pady=4, sticky="ew")
            fields[key] = w

        # Info banner
        tk.Label(body,
                 text="ℹ  Your Professor ID will be auto-assigned starting from 201.",
                 font=(FONT, 8), bg=BG, fg=GREY).grid(
            row=len(rows), column=0, columnspan=2, pady=2)

        err_lbl = _error_label(body)
        err_lbl.grid(row=len(rows)+1, column=0, columnspan=2, pady=4)

        def do_signup():
            data = {k: (w.get() if hasattr(w, "get") else "") for k, w in fields.items()}
            errs = []
            e = auth.validate_email(data["email"])
            if e: errs.append(e)
            e = auth.validate_password(data["password"])
            if e: errs.append(e)
            if data["password"] != data["confirm_pw"]:
                errs.append("Passwords do not match.")
            e = auth.validate_age(data["age"], 22)
            if e: errs.append(e)
            e = auth.validate_salary(data["salary"])
            if e: errs.append(e)
            e = auth.validate_phone(data["phone"])
            if e: errs.append(e)
            e = auth.validate_year(data["joining_year"])
            if e: errs.append(e)
            if errs:
                err_lbl.config(text=" | ".join(errs)); return
            try:
                auth.signup_professor(data)
                messagebox.showinfo("Success",
                    "Professor account created!\nYou can now login.")
                self._show_landing()
            except ValueError as ex:
                err_lbl.config(text=str(ex))

        btn_row = len(rows) + 2
        _btn(body, "Create Account", do_signup, color=ORANGE, width=24).grid(
            row=btn_row, column=0, columnspan=2, pady=(10, 4))
        _btn(body, "← Back", self._show_landing, color=GREY, width=24).grid(
            row=btn_row+1, column=0, columnspan=2)
        body.columnconfigure(1, weight=1)

    # ── Lab Attendant signup ────────────────────────────────────────────── #

    def _signup_lab(self):
        self.root.geometry("520x680")

        banner = tk.Frame(self.root, bg=GREY)
        banner.pack(fill="x")
        tk.Label(banner, text="📝  Lab Attendant Signup", font=(FONT, 14, "bold"),
                 bg=GREY, fg=WHITE).pack(pady=14)

        canvas   = tk.Canvas(self.root, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=BG, padx=36, pady=16)
        cw   = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_frame(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cw, width=canvas.winfo_width())
        body.bind("<Configure>", _on_frame)

        fields = {}
        rows   = [
            # lab_id is REMOVED — assigned automatically starting at 301
            ("first_name",   "First Name",   None),
            ("last_name",    "Last Name",    None),
            ("age",          "Age",          None),
            ("gender",       "Gender",       ["M", "F"]),
            ("lab_name",     "Lab Name",     ["Physics Lab","Chemistry Lab","CS Lab",
                                              "Bio Lab","Electronics Lab","Other"]),
            ("shift",        "Shift",        ["Morning","Evening","Night"]),
            ("city",         "City",         None),
            ("phone",        "Phone",        None),
            ("joining_year", "Joining Year", None),
            ("email",        "Gmail / Email",None),
            ("password",     "Password",     None),
            ("confirm_pw",   "Confirm Password", None),
        ]

        for i, (key, lbl, opts) in enumerate(rows):
            tk.Label(body, text=lbl, font=(FONT, 9, "bold"),
                     bg=BG, fg=NAVY).grid(row=i, column=0, sticky="w", padx=(0,10), pady=4)
            if opts:
                w = _combo(body, opts)
            elif key in ("password", "confirm_pw"):
                w = _entry(body, show="●")
            else:
                w = _entry(body)
            w.grid(row=i, column=1, pady=4, sticky="ew")
            fields[key] = w

        # Info banner
        tk.Label(body,
                 text="ℹ  Your Lab Attendant ID will be auto-assigned starting from 301.",
                 font=(FONT, 8), bg=BG, fg=GREY).grid(
            row=len(rows), column=0, columnspan=2, pady=2)

        err_lbl = _error_label(body)
        err_lbl.grid(row=len(rows)+1, column=0, columnspan=2, pady=4)

        def do_signup():
            data = {k: (w.get() if hasattr(w, "get") else "") for k, w in fields.items()}
            errs = []
            e = auth.validate_email(data["email"])
            if e: errs.append(e)
            e = auth.validate_password(data["password"])
            if e: errs.append(e)
            if data["password"] != data["confirm_pw"]:
                errs.append("Passwords do not match.")
            e = auth.validate_age(data["age"], 18)
            if e: errs.append(e)
            e = auth.validate_phone(data["phone"])
            if e: errs.append(e)
            e = auth.validate_year(data["joining_year"])
            if e: errs.append(e)
            if errs:
                err_lbl.config(text=" | ".join(errs)); return
            try:
                auth.signup_lab_attendant(data)
                messagebox.showinfo("Success",
                    "Lab Attendant account created!\nYou can now login.")
                self._show_landing()
            except ValueError as ex:
                err_lbl.config(text=str(ex))

        btn_row = len(rows) + 2
        _btn(body, "Create Account", do_signup, color=GREY, width=24).grid(
            row=btn_row, column=0, columnspan=2, pady=(10, 4))
        _btn(body, "← Back", self._show_landing, color=GREY, width=24).grid(
            row=btn_row+1, column=0, columnspan=2)
        body.columnconfigure(1, weight=1)

    # ── Close ───────────────────────────────────────────────────────────── #

    def _on_close(self):
        if messagebox.askokcancel("Exit", "Exit the application?"):
            self.root.destroy()