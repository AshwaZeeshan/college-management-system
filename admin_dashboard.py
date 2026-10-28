"""
admin_dashboard.py  –  Admin-only panel.

Tabs:
  • Statistics  – KPIs + department breakdown
  • Reports     – Export as PDF / Excel / CSV
  • Users       – View all accounts, Enable/Disable, Delete
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os, subprocess, sys
from db import get_connection
import reports as rpt

NAVY   = "#1a2744"
BLUE   = "#2980b9"
GREEN  = "#27ae60"
ORANGE = "#f39c12"
RED    = "#c0392b"
GREY   = "#7f8c8d"
TEAL   = "#16a085"
BG     = "#f4f6f7"
WHITE  = "#ffffff"
LIGHT  = "#eaf0fb"
FONT   = "Helvetica"


def _btn(parent, text, command, color=BLUE, width=20):
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=WHITE, font=(FONT, 9, "bold"),
                     relief="flat", bd=0, cursor="hand2",
                     width=width, pady=7)


def _kpi_card(parent, label, value, color):
    f = tk.Frame(parent, bg=color)
    f.pack(side="left", padx=6, fill="both", expand=True)
    tk.Label(f, text=str(value), font=(FONT, 22, "bold"),
             bg=color, fg=WHITE).pack(pady=(10, 0))
    tk.Label(f, text=label, font=(FONT, 8),
             bg=color, fg=WHITE).pack(pady=(0, 10))


class AdminDashboard(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("Admin Dashboard")
        self.geometry("900x640")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build()

    def _build(self):
        banner = tk.Frame(self, bg=NAVY)
        banner.pack(fill="x")
        tk.Label(banner, text="📊  Admin Dashboard",
                 font=(FONT, 15, "bold"), bg=NAVY, fg=WHITE).pack(pady=14)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=6)

        stats_tab = tk.Frame(nb, bg=BG)
        rep_tab   = tk.Frame(nb, bg=BG)
        users_tab = tk.Frame(nb, bg=BG)

        nb.add(stats_tab, text="  📈 Statistics  ")
        nb.add(rep_tab,   text="  📄 Reports  ")
        nb.add(users_tab, text="  👥 User Accounts  ")

        self._build_stats(stats_tab)
        self._build_reports(rep_tab)
        self._build_users(users_tab)

    # ── Statistics ────────────────────────────────────────────────────────── #

    def _build_stats(self, parent):
        conn  = get_connection()
        stats = dict(conn.execute("SELECT * FROM vw_summary_stats").fetchone())
        dept  = conn.execute(
            "SELECT department, COUNT(*) FROM students GROUP BY department ORDER BY 2 DESC"
        ).fetchall()
        conn.close()

        # KPI strip
        kf = tk.Frame(parent, bg=BG)
        kf.pack(fill="x", padx=10, pady=10)
        cards = [
            ("Active Students",       stats["active_students"],       BLUE),
            ("Active Professors",     stats["active_professors"],     GREEN),
            ("Lab Attendants",        stats["active_lab_attendants"], ORANGE),
            ("Courses",               stats["total_courses"],         TEAL),
            ("Enrollments",           stats["total_enrollments"],     NAVY),
            ("Disabled Accounts",     stats["disabled_users"],        RED),
        ]
        for lbl, val, clr in cards:
            _kpi_card(kf, lbl, val, clr)

        # Secondary
        sf = tk.Frame(parent, bg=LIGHT, padx=20, pady=10)
        sf.pack(fill="x", padx=10, pady=4)
        tk.Label(sf, text=f"Average Student GPA:  {stats['avg_gpa'] or 'N/A'}",
                 font=(FONT, 11), bg=LIGHT, fg=NAVY).pack(anchor="w")
        tk.Label(sf, text=f"Average Professor Salary:  ${(stats['avg_salary'] or 0):,.2f}",
                 font=(FONT, 11), bg=LIGHT, fg=NAVY).pack(anchor="w")

        if dept:
            tk.Label(parent, text="Students per Department",
                     font=(FONT, 11, "bold"), bg=BG, fg=NAVY
                     ).pack(pady=(10, 2), anchor="w", padx=14)
            tf = tk.Frame(parent)
            tf.pack(fill="both", expand=True, padx=10, pady=4)
            tree = ttk.Treeview(tf, columns=["Department","Count"],
                                show="headings", height=8)
            tree.heading("Department", text="Department")
            tree.heading("Count",      text="Count")
            tree.column("Department", width=320, anchor="center")
            tree.column("Count",      width=100, anchor="center")
            for d, c in dept:
                tree.insert("", tk.END, values=(d, c))
            tree.pack(fill="both", expand=True)

    # ── Reports ───────────────────────────────────────────────────────────── #

    def _build_reports(self, parent):
        tk.Label(parent, text="Export Reports",
                 font=(FONT, 12, "bold"), bg=BG, fg=NAVY).pack(pady=(14, 2))
        tk.Label(parent,
                 text="Choose a format then click a report. Files are saved in the reports/ folder.",
                 font=(FONT, 9), bg=BG, fg=GREY).pack()

        # ── Format selector ───────────────────────────────────────────── #
        fmt_frame = tk.Frame(parent, bg=LIGHT, padx=20, pady=10)
        fmt_frame.pack(fill="x", padx=30, pady=(10, 0))
        tk.Label(fmt_frame, text="Export Format:", font=(FONT, 10, "bold"),
                 bg=LIGHT, fg=NAVY).pack(side="left", padx=(0, 12))

        self._fmt = tk.StringVar(value="pdf")
        for fmt_val, fmt_label, clr in [
            ("pdf",   "📄  PDF",   BLUE),
            ("excel", "📊  Excel", GREEN),
            ("csv",   "📋  CSV",   ORANGE),
        ]:
            tk.Radiobutton(fmt_frame, text=fmt_label,
                           variable=self._fmt, value=fmt_val,
                           font=(FONT, 10, "bold"),
                           bg=LIGHT, fg=clr,
                           activebackground=LIGHT,
                           selectcolor=WHITE,
                           cursor="hand2").pack(side="left", padx=10)

        # ── Report buttons ────────────────────────────────────────────── #
        card = tk.Frame(parent, bg=WHITE, padx=30, pady=16,
                        highlightthickness=1, highlightbackground="#c5cfe4")
        card.pack(padx=30, pady=12, fill="x")

        report_defs = [
            ("Student Records",       rpt.generate_students_report,    BLUE),
            ("Professor Records",     rpt.generate_professors_report,  ORANGE),
            ("Course Records",        rpt.generate_courses_report,     TEAL),
            ("Enrollment Records",    rpt.generate_enrollments_report, GREEN),
            ("Lab Attendant Records", rpt.generate_lab_report,         GREY),
            ("System Summary",        rpt.generate_summary_report,     NAVY),
        ]

        for label, fn, color in report_defs:
            def _go(f=fn, l=label):
                fmt = self._fmt.get()
                try:
                    path = f(fmt=fmt)
                    fmt_name = {"pdf":"PDF","excel":"Excel","csv":"CSV"}.get(fmt, fmt)
                    messagebox.showinfo(
                        f"{fmt_name} Saved",
                        f"{l} exported as {fmt_name}:\n\n{path}"
                    )
                    self._open_file(path)
                except Exception as e:
                    messagebox.showerror("Export Error", str(e))

            _btn(card, f"  {label}  ", _go,
                 color=color, width=32).pack(pady=4, anchor="w")

    @staticmethod
    def _open_file(path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception:
            pass

    # ── User accounts ──────────────────────────────────────────────────────── #

    def _build_users(self, parent):
        tk.Label(parent, text="Registered User Accounts",
                 font=(FONT, 12, "bold"), bg=BG, fg=NAVY).pack(pady=(12, 2))
        tk.Label(parent,
                 text="🟢 Active    🔴 Disabled (cannot login)",
                 font=(FONT, 9), bg=BG, fg=GREY).pack()

        tf = tk.Frame(parent)
        tf.pack(fill="both", expand=True, padx=10, pady=6)

        cols   = ["user_id", "email", "role", "status", "created_at"]
        widths = [60, 280, 120, 80, 180]
        tree   = ttk.Treeview(tf, columns=cols, show="headings")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col.replace("_"," ").title())
            tree.column(col, width=w, anchor="center")

        # Tag colours: disabled rows shown in red tint
        tree.tag_configure("active",   foreground="#1a2744")
        tree.tag_configure("disabled", foreground="#c0392b",
                           background="#fde8e8")

        yscroll = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscroll=yscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        def _load():
            for item in tree.get_children():
                tree.delete(item)
            conn = get_connection()
            rows = conn.execute(
                "SELECT user_id, email, role, is_active, created_at "
                "FROM users ORDER BY role, email"
            ).fetchall()
            conn.close()
            for r in rows:
                status = "Active" if r["is_active"] else "Disabled"
                tag    = "active" if r["is_active"] else "disabled"
                tree.insert("", tk.END,
                            values=(r["user_id"], r["email"],
                                    r["role"], status, r["created_at"]),
                            tags=(tag,))

        _load()

        # ── Action buttons ──────────────────────────────────────────── #
        bf = tk.Frame(parent, bg=BG)
        bf.pack(pady=6)

        def _selected():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a user first.")
                return None, None
            vals = tree.item(sel, "values")
            return sel, vals   # (tree_item_id, (user_id, email, role, status, created_at))

        def disable_user():
            sel, vals = _selected()
            if not vals: return
            if vals[2] == "admin":
                messagebox.showerror("Forbidden", "Cannot disable the admin account."); return
            if vals[3] == "Disabled":
                messagebox.showinfo("Already Disabled", f"{vals[1]} is already disabled."); return
            if messagebox.askyesno("Confirm Disable",
                    f"Disable account:\n{vals[1]} ({vals[2]})?\n\n"
                    f"The user will not be able to log in until re-enabled."):
                conn = get_connection()
                try:
                    conn.execute("UPDATE users SET is_active=0 WHERE user_id=?", (vals[0],))
                    conn.commit()
                    messagebox.showinfo("Disabled", f"{vals[1]} has been disabled.")
                    _load()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    conn.close()

        def enable_user():
            sel, vals = _selected()
            if not vals: return
            if vals[3] == "Active":
                messagebox.showinfo("Already Active", f"{vals[1]} is already active."); return
            if messagebox.askyesno("Confirm Enable",
                    f"Re-enable account:\n{vals[1]} ({vals[2]})?"):
                conn = get_connection()
                try:
                    conn.execute("UPDATE users SET is_active=1 WHERE user_id=?", (vals[0],))
                    conn.commit()
                    messagebox.showinfo("Enabled", f"{vals[1]} has been re-enabled.")
                    _load()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    conn.close()

        def delete_user():
            sel, vals = _selected()
            if not vals: return
            if vals[2] == "admin":
                messagebox.showerror("Forbidden", "Cannot delete the admin account."); return
            if messagebox.askyesno("Confirm Delete",
                    f"Permanently delete:\n{vals[1]} ({vals[2]})?\n\n"
                    f"This will also delete all their records (CASCADE)."):
                conn = get_connection()
                try:
                    conn.execute("DELETE FROM users WHERE user_id=?", (vals[0],))
                    conn.commit()
                    messagebox.showinfo("Deleted", "User permanently deleted.")
                    _load()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    conn.close()

        for text, cmd, clr in [
            ("🔴  Disable Account", disable_user, ORANGE),
            ("🟢  Enable Account",  enable_user,  GREEN),
            ("🗑   Delete Account",  delete_user,  RED),
            ("🔄  Refresh",         _load,        BLUE),
        ]:
            _btn(bf, text, cmd, color=clr, width=22).pack(side="left", padx=5)