"""
main.py  –  College Management System (entry point)

Architecture:
  db.py              – database schema & connection
  auth.py            – password hashing, login/signup logic, validation
  login_window.py    – tkinter auth UI (landing / login / signup)
  profile_window.py  – self-service profile (student / professor / lab attendant)
  admin_dashboard.py – statistics + PDF report generation
  reports.py         – ReportLab PDF builders
  main.py            – main window (CRUD tabs, role-based access)

Default admin credentials:
  Email:    admin@college.edu
  Password: Admin@1234
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ── local modules ────────────────────────────────────────────────────────── #
import db as database
from db import get_connection
from login_window   import AuthWindow
from profile_window import ProfileWindow
from admin_dashboard import AdminDashboard

# ── palette (unchanged from original project) ─────────────────────────────── #
BG     = "#f4f6f7"
NAVY   = "#1a2744"
BLUE   = "#2980b9"
GREEN  = "#27ae60"
ORANGE = "#f39c12"
RED    = "#c0392b"
GREY   = "#7f8c8d"
WHITE  = "#ffffff"
LIGHT  = "#eaf0fb"
FONT   = "Helvetica"


# ═══════════════════════════════════════════════════════════════════════════ #
#  MAIN APPLICATION WINDOW                                                     #
# ═══════════════════════════════════════════════════════════════════════════ #

class CollegeApp:

    def __init__(self, user: dict, role_id):
        self.user    = user
        self.role_id = role_id
        self.role    = user["role"]

        self.root = tk.Tk()
        self.root.title("College Management System")
        self.root.geometry("1280x720")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._exit)

        self._apply_styles()
        self._build_topbar()
        self._build_notebook()
        self.root.mainloop()

    # ── ttk style tweaks ─────────────────────────────────────────────────── #

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook",
                         background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                         font=(FONT, 10, "bold"),
                         padding=[14, 6],
                         background=LIGHT,
                         foreground=NAVY)
        style.map("TNotebook.Tab",
                  background=[("selected", NAVY)],
                  foreground=[("selected", WHITE)])

        style.configure("Treeview",
                         font=(FONT, 9),
                         rowheight=24,
                         background=WHITE,
                         fieldbackground=WHITE,
                         foreground="#2c3e50")
        style.configure("Treeview.Heading",
                         font=(FONT, 9, "bold"),
                         background=NAVY,
                         foreground=WHITE)
        style.map("Treeview",
                  background=[("selected", BLUE)],
                  foreground=[("selected", WHITE)])

    # ── Top bar (user info + action buttons) ─────────────────────────────── #

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=NAVY, height=50)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="🎓  College Management System",
                 font=(FONT, 13, "bold"), bg=NAVY, fg=WHITE).pack(
            side="left", padx=16, pady=12)

        # right-side: role badge + buttons
        right = tk.Frame(bar, bg=NAVY)
        right.pack(side="right", padx=12)

        role_colors = {
            "admin": RED, "student": GREEN,
            "professor": ORANGE, "lab_attendant": GREY,
        }
        role_label = self.role.replace("_", " ").upper()
        tk.Label(right,
                 text=f"  {role_label}  ",
                 font=(FONT, 8, "bold"),
                 bg=role_colors.get(self.role, BLUE),
                 fg=WHITE, pady=3).pack(side="left", padx=6)

        tk.Label(right, text=self.user["email"],
                 font=(FONT, 9), bg=NAVY, fg="#a0b8d8").pack(
            side="left", padx=(0, 12))

        if self.role == "admin":
            tk.Button(right, text="📊 Dashboard",
                      bg=BLUE, fg=WHITE, font=(FONT, 9, "bold"),
                      relief="flat", cursor="hand2",
                      command=lambda: AdminDashboard(self.root)
                      ).pack(side="left", padx=4)

        if self.role != "admin":
            tk.Button(right, text="👤 My Profile",
                      bg=GREEN, fg=WHITE, font=(FONT, 9, "bold"),
                      relief="flat", cursor="hand2",
                      command=lambda: ProfileWindow(self.root,
                                                    self.user,
                                                    self.role_id)
                      ).pack(side="left", padx=4)

        tk.Button(right, text="⬑ Logout",
                  bg=GREY, fg=WHITE, font=(FONT, 9, "bold"),
                  relief="flat", cursor="hand2",
                  command=self._logout).pack(side="left", padx=4)

    # ── Notebook tabs ─────────────────────────────────────────────────────── #

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Tabs visible to ADMIN only ──────────────────────────────────── #
        if self.role == "admin":
            self._make_tab(
                "Students", "students",
                ["student_id","first_name","last_name","age","gender",
                 "department","gpa","city","phone","enrollment_year"],
                read_only=["student_id", "user_id"],
                extra_cols=["email"],        # pulled from users
                admin=True,
            )
            self._make_tab(
                "Professors", "professors",
                ["prof_id","first_name","last_name","age","gender",
                 "department","salary","city","phone","joining_year"],
                read_only=["prof_id", "user_id"],
                extra_cols=["email"],
                admin=True,
            )
            self._make_tab(
                "Lab Attendants", "lab_attendants",
                ["lab_id","first_name","last_name","age","gender",
                 "lab_name","shift","city","phone","joining_year"],
                read_only=["lab_id", "user_id"],
                extra_cols=["email"],
                admin=True,
            )
            self._make_courses_tab(admin=True)
            self._make_enrollments_tab()
            self._make_assignments_tab()

        # ── STUDENT sees their info + courses ──────────────────────────── #
        elif self.role == "student":
            self._make_read_only_tab(
                "My Record", "students",
                ["student_id","first_name","last_name","age","gender",
                 "department","gpa","city","phone","enrollment_year"],
                where=("student_id", self.role_id),
            )
            self._make_student_courses_tab()

        # ── PROFESSOR sees their info + courses ────────────────────────── #
        elif self.role == "professor":
            self._make_read_only_tab(
                "My Record", "professors",
                ["prof_id","first_name","last_name","age","gender",
                 "department","salary","city","phone","joining_year"],
                where=("prof_id", self.role_id),
            )
            self._make_prof_courses_tab()

        # ── LAB ATTENDANT sees their info + lab duties ─────────────────── #
        elif self.role == "lab_attendant":
            self._make_read_only_tab(
                "My Record", "lab_attendants",
                ["lab_id","first_name","last_name","age","gender",
                 "lab_name","shift","city","phone","joining_year"],
                where=("lab_id", self.role_id),
            )
            self._make_lab_tab()

    # ══════════════════════════════════════════════════════════════════════ #
    #  Generic CRUD tab builder  (used only by admin)                        #
    # ══════════════════════════════════════════════════════════════════════ #

    def _make_tab(self, tab_name, table_name, db_columns,
                  read_only=None, extra_cols=None, admin=False):
        """
        Full CRUD tab.  extra_cols are appended to the Treeview display
        only (joined from the users table for email).
        The primary key column is shown read-only (auto-assigned, not editable).
        """
        read_only  = read_only or []
        extra_cols = extra_cols or []

        # The first column is always the PK — always treat as read-only display
        pk_col = db_columns[0]
        # Editable columns = everything except the PK
        editable_cols = [c for c in db_columns if c != pk_col]

        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text=tab_name)

        entries             = {}
        current_selected_id = [None]

        # ── Input / form area ─────────────────────────────────────────── #
        frame = tk.LabelFrame(tab, text=f"  {tab_name} Details  ",
                              bg=BG, font=(FONT, 11, "bold"),
                              fg=NAVY, padx=6, pady=6)
        frame.pack(fill="x", padx=10, pady=6)

        combos = {
            "gender": ["M", "F"],
            "shift":  ["Morning", "Evening", "Night"],
            "status": ["Active", "Inactive"],
            "department": ["CS","EE","ME","CE","BBA","Physics","Math","Other"],
        }

        # PK field — read-only, shows auto-assigned value after selection
        tk.Label(frame,
                 text=pk_col.replace("_", " ").title() + " (Auto)",
                 bg=BG, font=(FONT, 8, "bold"), fg=GREY).grid(
            row=0, column=0, padx=6, pady=4, sticky="w")
        pk_entry = tk.Entry(frame, width=14,
                            bg=LIGHT, relief="flat",
                            highlightthickness=1,
                            highlightbackground="#c5cfe4",
                            state="readonly")
        pk_entry.grid(row=0, column=1, padx=6, pady=4)
        entries[pk_col] = pk_entry

        # Editable fields — laid out after the PK
        for i, col in enumerate(editable_cols, start=1):
            lbl_text = col.replace("_", " ").title()
            tk.Label(frame, text=lbl_text, bg=BG,
                     font=(FONT, 8, "bold"), fg=NAVY).grid(
                row=i // 5, column=(i % 5) * 2, padx=6, pady=4, sticky="w")

            if col in combos:
                e = ttk.Combobox(frame, values=combos[col],
                                 width=12, state="readonly")
            else:
                e = tk.Entry(frame, width=14,
                             bg=WHITE, relief="flat",
                             highlightthickness=1,
                             highlightbackground="#c5cfe4",
                             highlightcolor=BLUE)

            e.grid(row=i // 5, column=(i % 5) * 2 + 1, padx=6, pady=4)
            entries[col] = e

        # ── Treeview ─────────────────────────────────────────────────────── #
        display_cols = db_columns + extra_cols

        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        tree = ttk.Treeview(tree_frame, columns=display_cols,
                            show="headings")
        for col in display_cols:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=105, anchor="center")

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical",   command=tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal",  command=tree.xview)
        tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        # ── Row colour-banding ─────────────────────────────────────────── #
        tree.tag_configure("odd",  background=WHITE)
        tree.tag_configure("even", background=LIGHT)

        # ── Functions ────────────────────────────────────────────────────── #

        def clear():
            current_selected_id[0] = None
            # PK field: unlock temporarily to clear, then re-lock
            pk_entry.config(state="normal")
            pk_entry.delete(0, tk.END)
            pk_entry.config(state="readonly")
            for col in editable_cols:
                w = entries[col]
                try:
                    w.delete(0, tk.END)
                except Exception:
                    w.set("")

        def refresh():
            for row in tree.get_children():
                tree.delete(row)

            if extra_cols and "email" in extra_cols:
                col_str = ", ".join(
                    [f"t.{c}" for c in db_columns] + ["u.email"]
                )
                # WHERE u.is_active = 1 → disabled users hidden from table view
                sql = (f"SELECT {col_str} FROM {table_name} t "
                       f"JOIN users u ON t.user_id = u.user_id "
                       f"WHERE u.is_active = 1 "
                       f"ORDER BY t.{pk_col}")
            else:
                col_str = ", ".join(db_columns)
                sql = f"SELECT {col_str} FROM {table_name} ORDER BY {pk_col}"

            conn = get_connection()
            rows = conn.execute(sql).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        def insert():
            """
            Admin inserts a new record.
            The PK (student_id / prof_id / lab_id) is NOT supplied —
            SQLite AUTOINCREMENT assigns the next value automatically.
            """
            vals = [entries[c].get().strip() for c in editable_cols]

            # Basic: require at least first_name
            if not vals[0]:
                messagebox.showerror("Validation", "First name is required.")
                return

            try:
                conn = get_connection()
                import auth as _auth
                # Determine role string for the dummy user
                role_map = {
                    "students":      "student",
                    "professors":    "professor",
                    "lab_attendants":"lab_attendant",
                }
                role_str    = role_map.get(table_name, "student")
                dummy_email = f"admin_direct_{table_name}_{vals[0]}_{vals[1]}@system.local"

                # Create a linked system user (needed for FK)
                existing = conn.execute(
                    "SELECT user_id FROM users WHERE email=?", (dummy_email,)
                ).fetchone()
                if existing:
                    user_id = existing[0]
                else:
                    ph, salt = _auth.hash_password("system_generated")
                    conn.execute(
                        "INSERT INTO users(email,password_hash,salt,role) VALUES(?,?,?,?)",
                        (dummy_email, ph, salt, role_str)
                    )
                    user_id = conn.execute(
                        "SELECT user_id FROM users WHERE email=?", (dummy_email,)
                    ).fetchone()[0]

                # Build INSERT without PK — let AUTOINCREMENT fire
                # editable_cols already excludes the PK
                # We must also include user_id (second column in schema)
                insert_cols = ["user_id"] + editable_cols
                insert_vals = [user_id] + vals
                marks       = ",".join(["?"] * len(insert_vals))
                cols_str    = ",".join(insert_cols)
                conn.execute(
                    f"INSERT INTO {table_name}({cols_str}) VALUES({marks})",
                    insert_vals
                )
                conn.commit()
                conn.close()
                refresh()
                clear()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def delete():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a row.")
                return
            vals = tree.item(selected, "values")
            if messagebox.askyesno("Confirm", "Delete selected record?"):
                try:
                    conn = get_connection()
                    conn.execute(
                        f"DELETE FROM {table_name} WHERE {pk_col}=?",
                        (vals[0],)
                    )
                    conn.commit()
                    conn.close()
                    refresh()
                    clear()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        def update():
            if current_selected_id[0] is None:
                messagebox.showwarning("No Selection", "Please select a row.")
                return
            set_part = ",".join([f"{c}=?" for c in editable_cols])
            vals     = [entries[c].get().strip() for c in editable_cols]
            vals.append(current_selected_id[0])
            try:
                conn = get_connection()
                conn.execute(
                    f"UPDATE {table_name} SET {set_part} WHERE {pk_col}=?",
                    vals
                )
                conn.commit()
                conn.close()
                refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def select_row(event):
            selected = tree.focus()
            if not selected:
                return
            vals = tree.item(selected, "values")
            # Fill PK display
            pk_entry.config(state="normal")
            pk_entry.delete(0, tk.END)
            pk_entry.insert(0, vals[0])
            pk_entry.config(state="readonly")
            # Fill editable fields (vals[0] is PK, vals[1..] are data cols)
            for i, col in enumerate(editable_cols):
                # offset by 1 because vals[0] = PK
                val_idx = i + 1
                if val_idx >= len(vals):
                    break
                w = entries[col]
                try:
                    w.delete(0, tk.END)
                    w.insert(0, vals[val_idx])
                except Exception:
                    try:
                        w.set(vals[val_idx])
                    except Exception:
                        pass
            current_selected_id[0] = vals[0]

        tree.bind("<<TreeviewSelect>>", select_row)

        # ── Search & Sort ─────────────────────────────────────────────────── #
        filter_frame = tk.LabelFrame(tab, text="  Search & Sort  ",
                                     bg=BG, font=(FONT, 10))
        filter_frame.pack(fill="x", padx=10, pady=4)

        tk.Label(filter_frame, text="Column", bg=BG,
                 font=(FONT, 9)).grid(row=0, column=0, padx=6)
        col_combo = ttk.Combobox(filter_frame, values=db_columns,
                                  width=18, state="readonly")
        col_combo.grid(row=0, column=1, padx=4)

        tk.Label(filter_frame, text="Value", bg=BG,
                 font=(FONT, 9)).grid(row=0, column=2, padx=6)
        val_entry = tk.Entry(filter_frame, width=18,
                             highlightthickness=1,
                             highlightbackground="#c5cfe4",
                             highlightcolor=BLUE)
        val_entry.grid(row=0, column=3, padx=4)

        def search():
            col = col_combo.get()
            val = val_entry.get().strip()
            if not col:
                return
            for row in tree.get_children():
                tree.delete(row)

            if extra_cols and "email" in extra_cols:
                col_str = ", ".join(
                    [f"t.{c}" for c in db_columns] + ["u.email"]
                )
                # AND u.is_active = 1 → disabled users excluded from search too
                sql = (f"SELECT {col_str} FROM {table_name} t "
                       f"JOIN users u ON t.user_id = u.user_id "
                       f"WHERE u.is_active = 1 "
                       f"AND CAST(t.{col} AS TEXT) LIKE ?")
            else:
                sql = (f"SELECT {', '.join(db_columns)} FROM {table_name} "
                       f"WHERE CAST({col} AS TEXT) LIKE ?")

            conn = get_connection()
            rows = conn.execute(sql, (f"%{val}%",)).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        tk.Button(filter_frame, text="Search",
                  bg=BLUE, fg=WHITE, font=(FONT, 9, "bold"),
                  relief="flat", cursor="hand2",
                  command=search).grid(row=0, column=4, padx=6)

        tk.Label(filter_frame, text="Sort By", bg=BG,
                 font=(FONT, 9)).grid(row=1, column=0, padx=6, pady=4)
        sort_combo = ttk.Combobox(filter_frame, values=db_columns,
                                   width=18, state="readonly")
        sort_combo.grid(row=1, column=1, padx=4)

        def sort_data():
            col = sort_combo.get()
            if not col:
                return
            for row in tree.get_children():
                tree.delete(row)

            if extra_cols and "email" in extra_cols:
                col_str = ", ".join(
                    [f"t.{c}" for c in db_columns] + ["u.email"]
                )
                # WHERE u.is_active = 1 → disabled users excluded from sorted view
                sql = (f"SELECT {col_str} FROM {table_name} t "
                       f"JOIN users u ON t.user_id = u.user_id "
                       f"WHERE u.is_active = 1 "
                       f"ORDER BY t.{col}")
            else:
                sql = (f"SELECT {', '.join(db_columns)} FROM {table_name} "
                       f"ORDER BY {col}")

            conn = get_connection()
            rows = conn.execute(sql).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        tk.Button(filter_frame, text="Sort",
                  bg=GREEN, fg=WHITE, font=(FONT, 9, "bold"),
                  relief="flat", cursor="hand2",
                  command=sort_data).grid(row=1, column=2, padx=4)

        tk.Button(filter_frame, text="Reset",
                  bg=GREY, fg=WHITE, font=(FONT, 9, "bold"),
                  relief="flat", cursor="hand2",
                  command=refresh).grid(row=1, column=3, padx=4)

        # ── CRUD Buttons ─────────────────────────────────────────────────── #
        btn_frame = tk.Frame(tab, bg=BG)
        btn_frame.pack(pady=8)

        defs = [
            ("Insert",  insert,  GREEN),
            ("Update",  update,  ORANGE),
            ("Refresh", refresh, BLUE),
            ("Clear",   clear,   GREY),
            ("Delete",  delete,  RED),
        ]
        for i, (text, cmd, color) in enumerate(defs):
            tk.Button(btn_frame, text=text, command=cmd,
                      bg=color, fg=WHITE, font=(FONT, 9, "bold"),
                      relief="flat", cursor="hand2",
                      width=14, pady=6).grid(row=0, column=i, padx=5)

        refresh()

    # ══════════════════════════════════════════════════════════════════════ #
    #  Read-only tab  (non-admin users see their own record)                  #
    # ══════════════════════════════════════════════════════════════════════ #

    def _make_read_only_tab(self, tab_name, table_name, db_columns, where):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text=tab_name)

        col_name, col_val = where

        tk.Label(tab, text=f"Your {tab_name}  (read-only view)",
                 font=(FONT, 11, "bold"), bg=BG, fg=NAVY).pack(
            pady=(10, 4), anchor="w", padx=14)

        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=6)

        tree = ttk.Treeview(tree_frame, columns=db_columns, show="headings")
        for col in db_columns:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=110, anchor="center")

        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal",
                                 command=tree.xview)
        tree.configure(xscroll=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        conn = get_connection()
        col_str = ", ".join(db_columns)
        rows = conn.execute(
            f"SELECT {col_str} FROM {table_name} WHERE {col_name}=?",
            (col_val,)
        ).fetchall()
        conn.close()

        for row in rows:
            tree.insert("", tk.END, values=tuple(row))

        tk.Label(tab,
                 text="To edit your information, use  👤 My Profile  button above.",
                 font=(FONT, 9), bg=BG, fg=GREY).pack(pady=6)

    # ══════════════════════════════════════════════════════════════════════ #
    #  Courses tab  (admin – full CRUD)                                       #
    # ══════════════════════════════════════════════════════════════════════ #

    def _make_courses_tab(self, admin=False):
        cols = ["course_id","course_name","credit_hours","semester",
                "department","fee","room_no","timing","status","year"]

        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="Courses")

        entries             = {}
        current_selected_id = [None]

        frame = tk.LabelFrame(tab, text="  Course Details  ",
                              bg=BG, font=(FONT, 11, "bold"), fg=NAVY,
                              padx=6, pady=6)
        frame.pack(fill="x", padx=10, pady=6)

        combos = {
            "status":     ["Active", "Inactive"],
            "department": ["CS","EE","ME","CE","BBA","Physics","Math","Other"],
            "semester":   ["Fall","Spring","Summer"],
            "credit_hours": ["1","2","3","4","5","6"],
        }

        for i, col in enumerate(cols):
            tk.Label(frame, text=col.replace("_"," ").title(),
                     bg=BG, font=(FONT, 8, "bold"), fg=NAVY).grid(
                row=i // 5, column=(i % 5) * 2, padx=6, pady=4, sticky="w")

            if col in combos:
                e = ttk.Combobox(frame, values=combos[col],
                                 width=12, state="readonly")
            elif col == "course_id":
                e = tk.Entry(frame, width=14, bg=LIGHT, relief="flat",
                             highlightthickness=1,
                             highlightbackground="#c5cfe4")
            else:
                e = tk.Entry(frame, width=14, bg=WHITE, relief="flat",
                             highlightthickness=1,
                             highlightbackground="#c5cfe4",
                             highlightcolor=BLUE)
            e.grid(row=i // 5, column=(i % 5) * 2 + 1, padx=6, pady=4)
            entries[col] = e

        # Display tree (with assigned teacher)
        disp_cols = cols + ["Assigned Teacher"]
        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        tree = ttk.Treeview(tree_frame, columns=disp_cols, show="headings")
        for col in disp_cols:
            tree.heading(col, text=col.replace("_"," ").title())
            tree.column(col, width=100, anchor="center")
        tree.column("course_name", width=160)
        tree.column("Assigned Teacher", width=150)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical",   command=tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal",  command=tree.xview)
        tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        tree.tag_configure("odd",  background=WHITE)
        tree.tag_configure("even", background=LIGHT)

        def refresh():
            for row in tree.get_children():
                tree.delete(row)
            conn = get_connection()
            rows = conn.execute(
                """SELECT c.course_id, c.course_name, c.credit_hours,
                          c.semester, c.department, c.fee,
                          c.room_no, c.timing, c.status, c.year,
                          COALESCE(
                              CASE WHEN u.is_active = 1
                                   THEN p.first_name || ' ' || p.last_name
                                   ELSE NULL
                              END, '—') AS teacher
                   FROM courses c
                   LEFT JOIN course_assignments ca ON ca.course_id = c.course_id
                   LEFT JOIN professors p          ON p.prof_id = ca.prof_id
                   LEFT JOIN users u               ON u.user_id = p.user_id
                   ORDER BY c.course_id"""
            ).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        def clear():
            current_selected_id[0] = None
            for w in entries.values():
                try: w.delete(0, tk.END)
                except: w.set("")

        def insert():
            vals = [entries[c].get().strip() for c in cols]
            # course_id can be blank → autoincrement
            if not vals[0]:
                vals[0] = None
            marks = ",".join(["?"] * len(vals))
            try:
                conn = get_connection()
                conn.execute(f"INSERT INTO courses VALUES({marks})", vals)
                conn.commit()
                conn.close()
                refresh(); clear()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def delete():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("No Selection", "Select a row.")
                return
            v = tree.item(sel, "values")
            if messagebox.askyesno("Confirm", "Delete course?"):
                try:
                    conn = get_connection()
                    conn.execute("DELETE FROM courses WHERE course_id=?", (v[0],))
                    conn.commit()
                    conn.close()
                    refresh(); clear()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        def update():
            if current_selected_id[0] is None:
                messagebox.showwarning("No Selection", "Select a row.")
                return
            editable = [c for c in cols if c != "course_id"]
            set_part = ",".join([f"{c}=?" for c in editable])
            vals     = [entries[c].get().strip() for c in editable]
            vals.append(current_selected_id[0])
            try:
                conn = get_connection()
                conn.execute(
                    f"UPDATE courses SET {set_part} WHERE course_id=?", vals)
                conn.commit()
                conn.close()
                refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def select_row(event):
            sel = tree.focus()
            if not sel: return
            vals = tree.item(sel, "values")
            for i, col in enumerate(cols):
                try: entries[col].delete(0, tk.END); entries[col].insert(0, vals[i])
                except: 
                    try: entries[col].set(vals[i])
                    except: pass
            current_selected_id[0] = vals[0]

        tree.bind("<<TreeviewSelect>>", select_row)

        # Search
        sf = tk.LabelFrame(tab, text="  Search & Sort  ",
                           bg=BG, font=(FONT, 10))
        sf.pack(fill="x", padx=10, pady=4)

        tk.Label(sf, text="Column", bg=BG, font=(FONT, 9)).grid(row=0, column=0, padx=6)
        sc = ttk.Combobox(sf, values=cols, width=18, state="readonly")
        sc.grid(row=0, column=1)
        tk.Label(sf, text="Value", bg=BG, font=(FONT, 9)).grid(row=0, column=2, padx=6)
        se = tk.Entry(sf, width=18, highlightthickness=1,
                      highlightbackground="#c5cfe4", highlightcolor=BLUE)
        se.grid(row=0, column=3)

        def search():
            col = sc.get()
            if not col: return
            for row in tree.get_children(): tree.delete(row)
            conn = get_connection()
            rows = conn.execute(
                f"""SELECT c.course_id, c.course_name, c.credit_hours,
                           c.semester, c.department, c.fee,
                           c.room_no, c.timing, c.status, c.year,
                           COALESCE(
                               CASE WHEN u.is_active = 1
                                    THEN p.first_name || ' ' || p.last_name
                                    ELSE NULL
                               END, '—')
                    FROM courses c
                    LEFT JOIN course_assignments ca ON ca.course_id = c.course_id
                    LEFT JOIN professors p          ON p.prof_id = ca.prof_id
                    LEFT JOIN users u               ON u.user_id = p.user_id
                    WHERE CAST(c.{col} AS TEXT) LIKE ?""",
                (f"%{se.get().strip()}%",)
            ).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        tk.Button(sf, text="Search", bg=BLUE, fg=WHITE,
                  font=(FONT, 9, "bold"), relief="flat", cursor="hand2",
                  command=search).grid(row=0, column=4, padx=6)
        tk.Button(sf, text="Reset", bg=GREY, fg=WHITE,
                  font=(FONT, 9, "bold"), relief="flat", cursor="hand2",
                  command=refresh).grid(row=0, column=5, padx=4)

        bf = tk.Frame(tab, bg=BG)
        bf.pack(pady=8)
        for i, (text, cmd, color) in enumerate([
            ("Insert",  insert,  GREEN),
            ("Update",  update,  ORANGE),
            ("Refresh", refresh, BLUE),
            ("Clear",   clear,   GREY),
            ("Delete",  delete,  RED),
        ]):
            tk.Button(bf, text=text, command=cmd,
                      bg=color, fg=WHITE, font=(FONT, 9, "bold"),
                      relief="flat", cursor="hand2",
                      width=14, pady=6).grid(row=0, column=i, padx=5)

        refresh()

    # ══════════════════════════════════════════════════════════════════════ #
    #  Enrollments tab  (admin)                                               #
    # ══════════════════════════════════════════════════════════════════════ #

    def _make_enrollments_tab(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="Enrollments")

        form = tk.LabelFrame(tab, text="  Enroll Student in Course  ",
                             bg=BG, font=(FONT, 11, "bold"), fg=NAVY,
                             padx=10, pady=8)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="Student ID", bg=BG,
                 font=(FONT, 9, "bold"), fg=NAVY).grid(
            row=0, column=0, padx=8, pady=6, sticky="w")
        s_entry = tk.Entry(form, width=14, bg=WHITE, relief="flat",
                           highlightthickness=1, highlightbackground="#c5cfe4",
                           highlightcolor=BLUE)
        s_entry.grid(row=0, column=1, padx=4)

        tk.Label(form, text="Course ID", bg=BG,
                 font=(FONT, 9, "bold"), fg=NAVY).grid(
            row=0, column=2, padx=8, sticky="w")
        c_entry = tk.Entry(form, width=14, bg=WHITE, relief="flat",
                           highlightthickness=1, highlightbackground="#c5cfe4",
                           highlightcolor=BLUE)
        c_entry.grid(row=0, column=3, padx=4)

        tk.Label(form, text="Grade", bg=BG,
                 font=(FONT, 9, "bold"), fg=NAVY).grid(
            row=0, column=4, padx=8, sticky="w")
        g_combo = ttk.Combobox(form,
                                values=["A+","A","A-","B+","B","B-",
                                        "C+","C","C-","D","F","—"],
                                width=6, state="readonly")
        g_combo.set("—")
        g_combo.grid(row=0, column=5, padx=4)

        err_e = tk.Label(form, text="", font=(FONT, 9), bg=BG, fg=RED)
        err_e.grid(row=1, column=0, columnspan=6, pady=4)

        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        e_cols = ["enrollment_id","student_id","student_name",
                  "course_id","course_name","grade","enrolled_at"]
        tree = ttk.Treeview(tree_frame, columns=e_cols, show="headings")
        for col in e_cols:
            tree.heading(col, text=col.replace("_"," ").title())
            tree.column(col, width=120, anchor="center")
        tree.column("student_name", width=160)
        tree.column("course_name",  width=160)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        tree.tag_configure("odd",  background=WHITE)
        tree.tag_configure("even", background=LIGHT)

        def refresh():
            for row in tree.get_children(): tree.delete(row)
            conn = get_connection()
            rows = conn.execute(
                """SELECT e.enrollment_id,
                          e.student_id,
                          s.first_name||' '||s.last_name,
                          e.course_id,
                          c.course_name,
                          COALESCE(e.grade,'—'),
                          e.enrolled_at
                   FROM enrollments e
                   JOIN students s ON s.student_id = e.student_id
                   JOIN courses  c ON c.course_id  = e.course_id
                   ORDER BY e.enrollment_id DESC"""
            ).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        def enroll():
            s_id = s_entry.get().strip()
            c_id = c_entry.get().strip()
            grade = g_combo.get().strip() or None
            if not s_id or not c_id:
                err_e.config(text="Student ID and Course ID are required.")
                return
            try:
                conn = get_connection()
                conn.execute(
                    "INSERT INTO enrollments(student_id,course_id,grade) VALUES(?,?,?)",
                    (int(s_id), int(c_id), grade)
                )
                conn.commit()
                conn.close()
                s_entry.delete(0, tk.END)
                c_entry.delete(0, tk.END)
                err_e.config(text="")
                refresh()
            except sqlite3.IntegrityError:
                err_e.config(text="Already enrolled, or invalid ID.")
            except Exception as ex:
                err_e.config(text=str(ex))

        def remove_enrollment():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("No Selection", "Select a row.")
                return
            vals = tree.item(sel, "values")
            if messagebox.askyesno("Confirm", "Remove this enrollment?"):
                conn = get_connection()
                conn.execute("DELETE FROM enrollments WHERE enrollment_id=?",
                             (vals[0],))
                conn.commit()
                conn.close()
                refresh()

        def update_grade():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("No Selection", "Select a row.")
                return
            vals  = tree.item(sel, "values")
            grade = g_combo.get()
            conn  = get_connection()
            conn.execute("UPDATE enrollments SET grade=? WHERE enrollment_id=?",
                         (grade, vals[0]))
            conn.commit()
            conn.close()
            refresh()

        bf = tk.Frame(tab, bg=BG)
        bf.pack(pady=6)
        for text, cmd, color in [
            ("Enroll",        enroll,            GREEN),
            ("Update Grade",  update_grade,      ORANGE),
            ("Remove",        remove_enrollment, RED),
            ("Refresh",       refresh,           BLUE),
        ]:
            tk.Button(bf, text=text, command=cmd,
                      bg=color, fg=WHITE, font=(FONT, 9, "bold"),
                      relief="flat", cursor="hand2",
                      width=14, pady=6).pack(side="left", padx=5)

        refresh()

    # ══════════════════════════════════════════════════════════════════════ #
    #  Course-Professor Assignments tab  (admin)                              #
    # ══════════════════════════════════════════════════════════════════════ #

    def _make_assignments_tab(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="Course Assignments")

        form = tk.LabelFrame(tab, text="  Assign Professor to Course  ",
                             bg=BG, font=(FONT, 11, "bold"), fg=NAVY,
                             padx=10, pady=8)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="Course ID", bg=BG,
                 font=(FONT, 9, "bold"), fg=NAVY).grid(row=0, column=0, padx=8)
        ci = tk.Entry(form, width=14, bg=WHITE, relief="flat",
                      highlightthickness=1, highlightbackground="#c5cfe4",
                      highlightcolor=BLUE)
        ci.grid(row=0, column=1, padx=4)

        tk.Label(form, text="Professor ID", bg=BG,
                 font=(FONT, 9, "bold"), fg=NAVY).grid(row=0, column=2, padx=8)
        pi = tk.Entry(form, width=14, bg=WHITE, relief="flat",
                      highlightthickness=1, highlightbackground="#c5cfe4",
                      highlightcolor=BLUE)
        pi.grid(row=0, column=3, padx=4)

        err_a = tk.Label(form, text="", font=(FONT, 9), bg=BG, fg=RED)
        err_a.grid(row=1, column=0, columnspan=4)

        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        a_cols = ["assignment_id","course_id","course_name","prof_id","professor","assigned_at"]
        tree = ttk.Treeview(tree_frame, columns=a_cols, show="headings")
        for col in a_cols:
            tree.heading(col, text=col.replace("_"," ").title())
            tree.column(col, width=130, anchor="center")
        tree.column("course_name", width=180)
        tree.column("professor",   width=160)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=yscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        tree.tag_configure("odd",  background=WHITE)
        tree.tag_configure("even", background=LIGHT)

        def refresh():
            for row in tree.get_children(): tree.delete(row)
            conn = get_connection()
            rows = conn.execute(
                """SELECT ca.assignment_id, ca.course_id, c.course_name,
                          ca.prof_id, p.first_name||' '||p.last_name, ca.assigned_at
                   FROM course_assignments ca
                   JOIN courses    c ON c.course_id = ca.course_id
                   JOIN professors p ON p.prof_id   = ca.prof_id
                   ORDER BY ca.assignment_id DESC"""
            ).fetchall()
            conn.close()
            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", tk.END, values=tuple(row), tags=(tag,))

        def assign():
            c_id = ci.get().strip()
            p_id = pi.get().strip()
            if not c_id or not p_id:
                err_a.config(text="Both IDs are required."); return
            try:
                conn = get_connection()
                conn.execute(
                    "INSERT INTO course_assignments(course_id,prof_id) VALUES(?,?)",
                    (int(c_id), int(p_id))
                )
                conn.commit()
                conn.close()
                ci.delete(0, tk.END); pi.delete(0, tk.END)
                err_a.config(text="")
                refresh()
            except sqlite3.IntegrityError:
                err_a.config(text="Assignment already exists or invalid ID.")
            except Exception as ex:
                err_a.config(text=str(ex))

        def remove():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("No Selection", "Select a row."); return
            vals = tree.item(sel, "values")
            if messagebox.askyesno("Confirm", "Remove this assignment?"):
                conn = get_connection()
                conn.execute("DELETE FROM course_assignments WHERE assignment_id=?",
                             (vals[0],))
                conn.commit()
                conn.close()
                refresh()

        bf = tk.Frame(tab, bg=BG)
        bf.pack(pady=6)
        for text, cmd, color in [
            ("Assign",  assign,  GREEN),
            ("Remove",  remove,  RED),
            ("Refresh", refresh, BLUE),
        ]:
            tk.Button(bf, text=text, command=cmd,
                      bg=color, fg=WHITE, font=(FONT, 9, "bold"),
                      relief="flat", cursor="hand2",
                      width=14, pady=6).pack(side="left", padx=5)

        refresh()

    # ══════════════════════════════════════════════════════════════════════ #
    #  Non-admin course views                                                  #
    # ══════════════════════════════════════════════════════════════════════ #

    def _make_student_courses_tab(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="My Courses")

        tk.Label(tab, text="Your Enrolled Courses",
                 font=(FONT, 11, "bold"), bg=BG, fg=NAVY).pack(
            pady=(10, 4), anchor="w", padx=14)

        tf = tk.Frame(tab)
        tf.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ["Course ID","Course","Teacher","Credits","Semester",
                "Department","Fee","Room","Timing","Status","Grade"]
        tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        tree.column("Course", width=160)
        tree.column("Teacher", width=150)

        xscroll = ttk.Scrollbar(tf, orient="horizontal", command=tree.xview)
        yscroll = ttk.Scrollbar(tf, orient="vertical",   command=tree.yview)
        tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        conn = get_connection()
        rows = conn.execute(
            """SELECT c.course_id, c.course_name,
                      COALESCE(p.first_name||' '||p.last_name,'—'),
                      c.credit_hours, c.semester, c.department,
                      c.fee, c.room_no, c.timing, c.status, e.grade
               FROM enrollments e
               JOIN courses c ON c.course_id = e.course_id
               LEFT JOIN course_assignments ca ON ca.course_id = c.course_id
               LEFT JOIN professors p ON p.prof_id = ca.prof_id
               WHERE e.student_id=?""",
            (self.role_id,)
        ).fetchall()
        conn.close()

        for row in rows:
            tree.insert("", tk.END, values=tuple(row))

        if not rows:
            tk.Label(tab, text="You are not enrolled in any courses yet.",
                     font=(FONT, 10), bg=BG, fg=GREY).pack(pady=10)

    def _make_prof_courses_tab(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="My Courses")

        tk.Label(tab, text="Courses Assigned to You",
                 font=(FONT, 11, "bold"), bg=BG, fg=NAVY).pack(
            pady=(10, 4), anchor="w", padx=14)

        tf = tk.Frame(tab)
        tf.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ["Course ID","Course","Credits","Semester",
                "Department","Fee","Room","Timing","Status"]
        tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")
        tree.column("Course", width=180)

        yscroll = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscroll=yscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        conn = get_connection()
        rows = conn.execute(
            """SELECT c.course_id, c.course_name, c.credit_hours,
                      c.semester, c.department, c.fee,
                      c.room_no, c.timing, c.status
               FROM course_assignments ca
               JOIN courses c ON c.course_id = ca.course_id
               WHERE ca.prof_id=?""",
            (self.role_id,)
        ).fetchall()
        conn.close()
        for row in rows:
            tree.insert("", tk.END, values=tuple(row))

        if not rows:
            tk.Label(tab, text="No courses assigned to you yet.",
                     font=(FONT, 10), bg=BG, fg=GREY).pack(pady=10)

    def _make_lab_tab(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="My Lab")

        tk.Label(tab, text="Your Lab Assignments",
                 font=(FONT, 11, "bold"), bg=BG, fg=NAVY).pack(
            pady=(10, 4), anchor="w", padx=14)

        tf = tk.Frame(tab)
        tf.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ["ID","Lab Name","Responsibilities","Assigned At"]
        tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor="center")
        tree.column("Responsibilities", width=280)

        yscroll = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscroll=yscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        conn = get_connection()
        rows = conn.execute(
            "SELECT la_id,lab_name,responsibilities,assigned_at "
            "FROM lab_assignments WHERE lab_id=?",
            (self.role_id,)
        ).fetchall()
        conn.close()
        for row in rows:
            tree.insert("", tk.END, values=tuple(row))

        if not rows:
            tk.Label(tab, text="No lab assignments yet.",
                     font=(FONT, 10), bg=BG, fg=GREY).pack(pady=10)

    # ── Exit / Logout ─────────────────────────────────────────────────────── #

    def _exit(self):
        if messagebox.askokcancel("Exit", "Exit the application?"):
            self.root.destroy()

    def _logout(self):
        if messagebox.askokcancel("Logout", "Log out and return to login screen?"):
            self.root.destroy()
            app()          # restart the auth flow


# ═══════════════════════════════════════════════════════════════════════════ #
#  Entry point                                                                 #
# ═══════════════════════════════════════════════════════════════════════════ #

def app():
    # 1. Initialise DB (creates tables + default admin if absent)
    database.init_db()

    # 2. Show authentication window
    auth_win = AuthWindow()

    # 3. If user closed without logging in → exit
    if auth_win.result is None:
        sys.exit(0)

    user, role_id = auth_win.result

    # 4. Launch main app window
    CollegeApp(user, role_id)


if __name__ == "__main__":
    app()