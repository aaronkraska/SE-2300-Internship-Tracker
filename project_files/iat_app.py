import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

DB_FILE = "internships.db"

STATUSES = [
    "Planned",
    "Applied",
    "Follow-up Needed",
    "Interviewing",
    "Offer",
    "Rejected",
    "Archived",
]


def init_db() -> None:
    """Create the SQLite database and Applications table if they do not exist."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                role_title TEXT NOT NULL,
                date_applied TEXT NOT NULL,
                status TEXT NOT NULL,
                follow_up_date TEXT NOT NULL,
                application_link TEXT,
                location TEXT,
                notes TEXT,
                archived INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        conn.commit()


def parse_date_iso(date_str: str) -> datetime:
    """Parse YYYY-MM-DD. Raise ValueError if invalid."""
    return datetime.strptime(date_str.strip(), "%Y-%m-%d")


def calculate_follow_up(date_applied_iso: str) -> str:
    """Default follow-up is +10 days, returned as YYYY-MM-DD."""
    dt = parse_date_iso(date_applied_iso)
    return (dt + timedelta(days=10)).strftime("%Y-%m-%d")


class AddApplicationWindow(tk.Toplevel):
    def __init__(self, parent, on_saved_callback):
        super().__init__(parent)
        self.title("Add Application")
        self.resizable(False, False)
        self.on_saved_callback = on_saved_callback

        self.company_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Applied")
        self.notes_var = tk.StringVar()

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Company Name (required)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.company_var, width=40).grid(row=0, column=1, **pad)

        ttk.Label(self, text="Role Title (required)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.role_var, width=40).grid(row=1, column=1, **pad)

        ttk.Label(self, text="Date Applied (YYYY-MM-DD) (required)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.date_var, width=40).grid(row=2, column=1, **pad)

        ttk.Label(self, text="Status (required)").grid(row=3, column=0, sticky="w", **pad)
        ttk.Combobox(self, textvariable=self.status_var, values=STATUSES, state="readonly", width=37).grid(
            row=3, column=1, **pad
        )

        ttk.Label(self, text="Notes (optional)").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.notes_var, width=40).grid(row=4, column=1, **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", **pad)

        ttk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Save", command=self.save).grid(row=0, column=1, padx=6)

        # Convenience: set focus to first field
        self.after(50, lambda: self.focus_force())

    def save(self) -> None:
        company = self.company_var.get().strip()
        role = self.role_var.get().strip()
        date_applied = self.date_var.get().strip()
        status = self.status_var.get().strip()
        notes = self.notes_var.get().strip()

        # Basic validation
        if not company:
            messagebox.showerror("Validation Error", "Company name is required.")
            return
        if not role:
            messagebox.showerror("Validation Error", "Role title is required.")
            return
        if not date_applied:
            messagebox.showerror("Validation Error", "Date applied is required.")
            return
        try:
            _ = parse_date_iso(date_applied)
        except ValueError:
            messagebox.showerror("Validation Error", "Date must be in YYYY-MM-DD format (e.g., 2026-02-11).")
            return
        if status not in STATUSES:
            messagebox.showerror("Validation Error", "Status must be one of the allowed categories.")
            return

        follow_up_date = calculate_follow_up(date_applied)

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                """
                INSERT INTO Applications
                (company_name, role_title, date_applied, status, follow_up_date, notes, archived)
                VALUES (?, ?, ?, ?, ?, ?, 0);
                """,
                (company, role, date_applied, status, follow_up_date, notes),
            )
            conn.commit()

        self.on_saved_callback()
        self.destroy()


class IATApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Internship Application Tracker (Prototype)")
        self.geometry("900x420")

        # Top buttons
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Button(top, text="Add Application", command=self.open_add_window).pack(side="left")

        ttk.Button(top, text="Refresh", command=self.load_rows).pack(side="left", padx=8)

        # Table (Treeview)
        columns = ("id", "company", "role", "date_applied", "status", "follow_up", "archived")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)

        self.tree.heading("id", text="ID")
        self.tree.heading("company", text="Company")
        self.tree.heading("role", text="Role")
        self.tree.heading("date_applied", text="Date Applied")
        self.tree.heading("status", text="Status")
        self.tree.heading("follow_up", text="Follow-up Date")
        self.tree.heading("archived", text="Archived")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("company", width=180)
        self.tree.column("role", width=220)
        self.tree.column("date_applied", width=110, anchor="center")
        self.tree.column("status", width=140)
        self.tree.column("follow_up", width=120, anchor="center")
        self.tree.column("archived", width=80, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", padx=10, pady=(0, 8))

        self.load_rows()

    def open_add_window(self) -> None:
        AddApplicationWindow(self, on_saved_callback=self.load_rows)

    def load_rows(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.execute(
                """
                SELECT application_id, company_name, role_title, date_applied, status, follow_up_date, archived
                FROM Applications
                ORDER BY application_id DESC;
                """
            )
            rows = cur.fetchall()

        for (app_id, company, role, date_applied, status, follow_up_date, archived) in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    app_id,
                    company,
                    role,
                    date_applied,
                    status,
                    follow_up_date,
                    "Yes" if archived else "No",
                ),
            )

        self.status_var.set(f"Loaded {len(rows)} application(s).")


if __name__ == "__main__":
    init_db()
    app = IATApp()
    app.mainloop()
