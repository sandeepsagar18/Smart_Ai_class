import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import customtkinter as ctk
import sqlite3
from datetime import datetime
from pathlib import Path
import threading
import pandas as pd
import pickle

from src.database import (
    init_db, authenticate_teacher, register_teacher_secure,
    verify_teacher_password, change_teacher_password, get_all_teachers,
    delete_teacher_secure, add_subject, get_subjects_by_teacher,
    get_all_subjects, delete_subject_secure, get_students_by_class,
    get_attendance_for_subject_date, delete_student_secure,
    get_all_students_master, update_student_details, admin_reset_teacher_password,
    update_teacher_role, reassign_subject_teacher, get_system_diagnostics,
    get_attendance_audit_logs, delete_attendance_log,
    unlock_teacher_account, verify_admin_master_key, get_admin_master_key,
    update_admin_master_key, generate_file_checksum, verify_file_integrity,
    get_security_audit_logs, create_database_backup, get_backup_list, log_security_event
)
from utils.config import BASE_DIR, ATTENDANCE_DIR, UNKNOWN_FACES_DIR
import time

DB_PATH = BASE_DIR / "data" / "smartclass.db"
EMB_PATH = BASE_DIR / "data" / "embeddings.pkl"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# CUSTOM SLEEK MODAL DIALOG (ALWAYS STAYS ON TOP OF ACTIVE WINDOW)
class CTkAlert(ctk.CTkToplevel):
    def __init__(self, parent, title, message, alert_type="info", is_confirm=False):
        super().__init__(parent)
        self.result = False if is_confirm else None
        self.title(title)
        self.geometry("450x230")
        self.resizable(False, False)

        self.update_idletasks()
        try:
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            x = px + (pw - 450) // 2
            y = py + (ph - 230) // 2
            self.geometry(f"+{max(20, x)}+{max(20, y)}")
        except Exception:
            pass

        self.transient(parent)
        self.lift()
        self.attributes('-topmost', True)
        self.focus_force()
        self.grab_set()

        colors = {
            "success": ("#00ffcc", "✅"),
            "error": ("#ff4444", "❌"),
            "warning": ("#ffcc00", "⚠️"),
            "info": ("#00a8cc", "ℹ️"),
            "question": ("#00ffcc", "❓")
        }
        color, icon = colors.get(alert_type, ("#00ffcc", "ℹ️"))

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 8))

        ctk.CTkLabel(header_frame, text=f"{icon}  {title}", font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=color).pack(anchor="center")

        msg_box = ctk.CTkFrame(self, fg_color="transparent")
        msg_box.pack(fill="both", expand=True, padx=25, pady=4)

        ctk.CTkLabel(msg_box, text=message, font=ctk.CTkFont(size=13),
                     wraplength=390, justify="center").pack(expand=True)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(8, 18))

        if is_confirm:
            def on_yes():
                self.result = True
                self.destroy()

            def on_no():
                self.result = False
                self.destroy()

            ctk.CTkButton(btn_row, text="Confirm", width=120, height=34, fg_color="#8b0000",
                          hover_color="#a52a2a", font=ctk.CTkFont(weight="bold"), command=on_yes).pack(side="left", padx=30)
            ctk.CTkButton(btn_row, text="Cancel", width=120, height=34, fg_color="#404040",
                          hover_color="#505050", command=on_no).pack(side="right", padx=30)
            self.bind("<Return>", lambda e: on_yes())
            self.bind("<Escape>", lambda e: on_no())
        else:
            def on_ok():
                self.destroy()

            ctk.CTkButton(btn_row, text="OK", width=140, height=34, fg_color="#006400",
                          hover_color="#008000", font=ctk.CTkFont(weight="bold"), command=on_ok).pack(anchor="center")
            self.bind("<Return>", lambda e: on_ok())
            self.bind("<Escape>", lambda e: on_ok())


# CUSTOM INPUT PROMPT DIALOG
class CTkPrompt(ctk.CTkToplevel):
    def __init__(self, parent, title, prompt_text, is_password=False):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.geometry("420x210")
        self.resizable(False, False)

        self.update_idletasks()
        try:
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            x = px + (pw - 420) // 2
            y = py + (ph - 210) // 2
            self.geometry(f"+{max(20, x)}+{max(20, y)}")
        except Exception:
            pass

        self.transient(parent)
        self.lift()
        self.attributes('-topmost', True)
        self.focus_force()
        self.grab_set()

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(self, text=prompt_text, font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 10))

        show_char = "*" if is_password else ""
        self.entry = ctk.CTkEntry(self, show=show_char, width=280)
        self.entry.pack(pady=5)
        self.entry.focus()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=15)

        def on_ok():
            self.result = self.entry.get()
            self.destroy()

        def on_cancel():
            self.result = None
            self.destroy()

        ctk.CTkButton(btn_row, text="Submit", width=110, fg_color="#006400", hover_color="#008000",
                      command=on_ok).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="Cancel", width=110, fg_color="#404040", hover_color="#505050",
                      command=on_cancel).pack(side="right", padx=10)

        self.bind("<Return>", lambda e: on_ok())
        self.bind("<Escape>", lambda e: on_cancel())


class SmartClassApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        init_db()

        self.title("SmartClass Vision v0.2")
        self.geometry("1200x780")
        self.resizable(False, False)

        # Elevate window on startup
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.focus_force()

        self.active_modal = None
        self.current_user = None
        self.last_user_activity = time.time()
        self.is_terminal_locked = False

        # Reset idle timer on any user interaction
        self.bind_all("<Key>", lambda e: self._on_user_action())
        self.bind_all("<Button>", lambda e: self._on_user_action())

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # LEFT SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SmartClass Vision", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(24, 2))
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="v0.2 • Production", font=ctk.CTkFont(size=12),
                                           text_color="#64748b")
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 16))

        # DYNAMIC ROLE-BASED SIDEBAR ACTION CONTAINER (Approach A View Isolation)
        self.sidebar_actions = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_actions.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Dynamic button references for state manipulation
        self.btn_attendance = None
        self.btn_teacher = None
        self.btn_admin = None
        self.btn_train = None

        # RIGHT MAIN AREA
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=15)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # TOP BAR: Security & Session Status
        self.session_bar = ctk.CTkFrame(self.main_frame, height=45, corner_radius=10, fg_color="#1a1c24")
        self.session_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.lbl_session = ctk.CTkLabel(self.session_bar, text="● Standby — Authentication Required",
                                        font=ctk.CTkFont(size=13, weight="bold"), text_color="#94a3b8")
        self.lbl_session.pack(side="left", padx=15, pady=8)

        self.btn_auth = ctk.CTkButton(self.session_bar, text="Faculty Login", width=120, height=28,
                                      fg_color="#1f538d", hover_color="#14375e", command=self.open_auth_window)
        self.btn_auth.pack(side="right", padx=10, pady=8)

        self.btn_lock = ctk.CTkButton(self.session_bar, text="🔒 Lock", width=75, height=28,
                                      fg_color="#4a4e69", hover_color="#22223b", command=self.lock_terminal)

        self.btn_change_pass = ctk.CTkButton(self.session_bar, text="Change Password", width=120, height=28,
                                             fg_color="#3d5a80", hover_color="#293241", command=self.open_change_password_window)

        # HEADER: Clock & Date
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=1, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.time_label = ctk.CTkLabel(self.header_frame, text="--:--:--", font=ctk.CTkFont(size=22, weight="bold"),
                                       text_color="#00a8cc")
        self.time_label.grid(row=0, column=1, sticky="e")
        self.date_label = ctk.CTkLabel(self.header_frame, text="----", font=ctk.CTkFont(size=13), text_color="gray")
        self.date_label.grid(row=1, column=1, sticky="e", pady=(0, 8))

        # STANDBY KIOSK HERO FRAME (Classroom Kiosk mode when logged out)
        self.standby_frame = ctk.CTkFrame(self.main_frame, corner_radius=16, fg_color="#181822")
        self._build_standby_kiosk()

        # TABVIEW (System Overview & Live Roster - mounted when logged in)
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tab_overview = self.tabview.add("System Overview")
        self.tab_roster = self.tabview.add("Today's Roster")

        # TAB 1: SYSTEM OVERVIEW
        self.tab_overview.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_students = ctk.CTkFrame(self.tab_overview, height=110, corner_radius=15)
        self.card_students.grid(row=0, column=0, padx=10, pady=15, sticky="nsew")
        ctk.CTkLabel(self.card_students, text="Total Students Registered", font=ctk.CTkFont(size=14, weight="bold")).pack(
            pady=(15, 4))
        self.lbl_total_students = ctk.CTkLabel(self.card_students, text="0", font=ctk.CTkFont(size=34, weight="bold"),
                                               text_color="#00ffcc")
        self.lbl_total_students.pack()

        self.card_teachers = ctk.CTkFrame(self.tab_overview, height=110, corner_radius=15)
        self.card_teachers.grid(row=0, column=1, padx=10, pady=15, sticky="nsew")
        ctk.CTkLabel(self.card_teachers, text="Faculty Profiles", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 4))
        self.lbl_total_teachers = ctk.CTkLabel(self.card_teachers, text="0", font=ctk.CTkFont(size=34, weight="bold"),
                                              text_color="#00a8cc")
        self.lbl_total_teachers.pack()

        self.card_attendance = ctk.CTkFrame(self.tab_overview, height=110, corner_radius=15)
        self.card_attendance.grid(row=0, column=2, padx=10, pady=15, sticky="nsew")
        ctk.CTkLabel(self.card_attendance, text="Attendance Sheets", font=ctk.CTkFont(size=14, weight="bold")).pack(
            pady=(15, 4))
        self.lbl_sheets = ctk.CTkLabel(self.card_attendance, text="0 Generated",
                                       font=ctk.CTkFont(size=22, weight="bold"), text_color="#ffcc00")
        self.lbl_sheets.pack()

        self.progress_frame = ctk.CTkFrame(self.tab_overview, corner_radius=15)
        self.progress_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=15, sticky="nsew")
        ctk.CTkLabel(self.progress_frame, text="Today's Attendance Progress",
                      font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        self.lbl_progress_text = ctk.CTkLabel(self.progress_frame, text="0 / 0 Present", font=ctk.CTkFont(size=13),
                                              text_color="gray")
        self.lbl_progress_text.pack()
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=580, height=18, progress_color="#00ffcc")
        self.progress_bar.pack(pady=12)
        self.progress_bar.set(0)

        # TAB 2: LIVE ROSTER
        self.tab_roster.grid_rowconfigure(1, weight=1)
        self.tab_roster.grid_columnconfigure(0, weight=1)

        self.roster_ctrl_frame = ctk.CTkFrame(self.tab_roster, fg_color="transparent")
        self.roster_ctrl_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(self.roster_ctrl_frame, text="Select Subject & Section:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(5, 10))

        self.roster_subject_var = ctk.StringVar(value="All Registered Students")
        self.roster_subject_menu = ctk.CTkOptionMenu(
            self.roster_ctrl_frame, variable=self.roster_subject_var,
            values=["All Registered Students"], width=380, command=lambda _: self.populate_roster()
        )
        self.roster_subject_menu.pack(side="left")

        # Reset button is only rendered for Admin role
        self.btn_reset_attendance = ctk.CTkButton(
            self.roster_ctrl_frame, text="RESET Today's Attendance", command=self.reset_attendance,
            fg_color="#8b0000", hover_color="#a52a2a", width=180
        )
        ctk.CTkButton(self.roster_ctrl_frame, text="Refresh", command=self.refresh_dashboard_metrics, width=80).pack(
            side="right")

        self.table_frame = ctk.CTkScrollableFrame(self.tab_roster)
        self.table_frame.grid(row=1, column=0, sticky="nsew")
        self.table_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.update_clock()
        self.refresh_dashboard_metrics()

    # DIALOG HELPERS
    def get_top_window(self):
        if self.active_modal and self.active_modal.winfo_exists():
            return self.active_modal
        return self

    def show_info(self, title, message, parent=None):
        p = parent or self.get_top_window()
        diag = CTkAlert(p, title, message, alert_type="success")
        diag.wait_window()

    def show_error(self, title, message, parent=None):
        p = parent or self.get_top_window()
        diag = CTkAlert(p, title, message, alert_type="error")
        diag.wait_window()

    def show_warning(self, title, message, parent=None):
        p = parent or self.get_top_window()
        diag = CTkAlert(p, title, message, alert_type="warning")
        diag.wait_window()

    def ask_confirm(self, title, message, parent=None):
        p = parent or self.get_top_window()
        diag = CTkAlert(p, title, message, alert_type="question", is_confirm=True)
        diag.wait_window()
        return diag.result

    def prompt_input(self, title, message, parent=None, is_password=False):
        p = parent or self.get_top_window()
        diag = CTkPrompt(p, title, message, is_password=is_password)
        diag.wait_window()
        return diag.result

    def _on_user_action(self):
        self.last_user_activity = time.time()

    def update_clock(self):
        now = datetime.now()
        self.time_label.configure(text=now.strftime("%I:%M:%S %p"))
        self.date_label.configure(text=now.strftime("%A, %B %d, %Y"))

        # Inactivity auto-lock (10 minutes = 600 seconds)
        if self.current_user and not self.is_terminal_locked:
            if time.time() - self.last_user_activity > 600:
                self.lock_terminal()

        self.after(1000, self.update_clock)

    def _build_standby_kiosk(self):
        center_card = ctk.CTkFrame(self.standby_frame, corner_radius=20, fg_color="#151722", border_width=1, border_color="#232738")
        center_card.place(relx=0.5, rely=0.5, anchor="center")

        content = ctk.CTkFrame(center_card, fg_color="transparent")
        content.pack(padx=60, pady=50)

        ctk.CTkLabel(content, text="SmartClass Vision",
                     font=ctk.CTkFont(size=28, weight="bold"), text_color="#ffffff").pack(pady=(0, 4))
        ctk.CTkLabel(content, text="Automated Face Recognition Attendance System",
                     font=ctk.CTkFont(size=13), text_color="#94a3b8").pack(pady=(0, 24))

        status_pill = ctk.CTkFrame(content, corner_radius=20, fg_color="#1e2232")
        status_pill.pack(pady=(0, 24), padx=20)
        ctk.CTkLabel(status_pill, text="●  Standby Mode  —  Authentication Required",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#cbd5e1").pack(padx=24, pady=8)

        ctk.CTkButton(content, text="Sign In to Begin Class",
                      command=self.open_auth_window, height=44, width=280,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#1f538d", hover_color="#14375e").pack(pady=(0, 22))

        ctk.CTkLabel(content, text="Version 0.2 • Production Build",
                     font=ctk.CTkFont(size=11), text_color="#475569").pack()

    def render_role_interface(self):
        for widget in self.sidebar_actions.winfo_children():
            widget.destroy()

        self.btn_attendance = None
        self.btn_teacher = None
        self.btn_admin = None
        self.btn_train = None

        if hasattr(self, 'btn_reset_attendance'):
            self.btn_reset_attendance.pack_forget()

        if not self.current_user:
            # === STATE 1: STANDBY KIOSK (LOGGED OUT) ===
            self.tabview.grid_forget()
            self.standby_frame.grid(row=2, column=0, sticky="nsew", pady=(8, 0))

            standby_box = ctk.CTkFrame(self.sidebar_actions, corner_radius=12, fg_color="#161822")
            standby_box.pack(fill="x", padx=6, pady=(8, 12))
            ctk.CTkLabel(standby_box, text="System Standby", font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#94a3b8").pack(pady=(14, 4))
            ctk.CTkLabel(standby_box, text="Classroom attendance and student management are locked. Please sign in to proceed.",
                         font=ctk.CTkFont(size=11), text_color="#64748b", wraplength=200, justify="center").pack(padx=12, pady=(0, 14))

            ctk.CTkButton(self.sidebar_actions, text="Faculty Login", command=self.open_auth_window,
                          fg_color="#1f538d", hover_color="#14375e", height=38,
                          font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=6, pady=6)

        elif self.current_user["role"] != "admin":
            # === STATE 2: FACULTY WORKSPACE (TEACHER) ===
            self.standby_frame.grid_forget()
            self.tabview.grid(row=2, column=0, sticky="nsew")

            badge = ctk.CTkFrame(self.sidebar_actions, corner_radius=12, fg_color="#122538")
            badge.pack(fill="x", padx=6, pady=(4, 12))
            ctk.CTkLabel(badge, text=f"👨‍🏫 {self.current_user['name']}", font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#00ffcc").pack(pady=(8, 2), padx=8)
            ctk.CTkLabel(badge, text=f"Dept: {self.current_user['department']} | {self.current_user['employee_id']}",
                         font=ctk.CTkFont(size=11), text_color="#a0c4e2").pack(pady=(0, 8), padx=8)

            # Primary Action: Section Batch Scanner
            self.btn_attendance = ctk.CTkButton(
                self.sidebar_actions, text="📸 BATCH CLASS SCAN",
                command=self.start_live_attendance, height=52,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#006400", hover_color="#008000"
            )
            self.btn_attendance.pack(fill="x", padx=6, pady=8)

            # Faculty Allotted Classes & Subjects
            self.btn_teacher = ctk.CTkButton(
                self.sidebar_actions, text="📚 My Allotted Classes",
                command=self.open_teacher_profile_window,
                fg_color="#1f538d", hover_color="#14375e", height=40,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            self.btn_teacher.pack(fill="x", padx=6, pady=6)

            # Student Directory Search (Read-only for teachers)
            ctk.CTkButton(
                self.sidebar_actions, text="🔍 Student Directory",
                command=self.search_student,
                fg_color="#2b2b2b", hover_color="#404040", height=40
            ).pack(fill="x", padx=6, pady=6)

            # Refresh Dashboard
            ctk.CTkButton(
                self.sidebar_actions, text="🔄 Refresh Dashboard",
                command=self.refresh_dashboard_metrics,
                fg_color="#222222", hover_color="#333333", height=32
            ).pack(fill="x", padx=6, pady=(12, 6))

            # Security assurance badge
            sec_card = ctk.CTkFrame(self.sidebar_actions, corner_radius=10, fg_color="#112217")
            sec_card.pack(fill="x", padx=6, pady=(16, 6))
            ctk.CTkLabel(sec_card, text="🛡️ SECTION GUARD ACTIVE", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#00ff88").pack(pady=(8, 3))
            ctk.CTkLabel(sec_card,
                         text="Attendance scanning is strictly limited to students matching your subject's branch & section.",
                         font=ctk.CTkFont(size=10), text_color="#77a585", wraplength=210).pack(padx=8, pady=(0, 8))

        else:
            # === STATE 3: MASTER ADMIN SUITE (ADMIN) ===
            self.standby_frame.grid_forget()
            self.tabview.grid(row=2, column=0, sticky="nsew")

            if hasattr(self, 'btn_reset_attendance'):
                self.btn_reset_attendance.pack(side="right", padx=10)

            admin_badge = ctk.CTkFrame(self.sidebar_actions, corner_radius=12, fg_color="#2b0938")
            admin_badge.pack(fill="x", padx=6, pady=(4, 10))
            ctk.CTkLabel(admin_badge, text="🛡️ MASTER ADMIN", font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#e0aaff").pack(pady=(8, 2), padx=8)
            ctk.CTkLabel(admin_badge, text=f"{self.current_user['name']} ({self.current_user['employee_id']})",
                         font=ctk.CTkFont(size=11), text_color="#c77dff").pack(pady=(0, 8), padx=8)

            # Prominent Admin Command Portal Button
            self.btn_admin = ctk.CTkButton(
                self.sidebar_actions, text="🛡️ Admin Command Portal",
                command=self.open_admin_portal,
                fg_color="#5a189a", hover_color="#7b2cbf", height=44,
                font=ctk.CTkFont(size=13, weight="bold")
            )
            self.btn_admin.pack(fill="x", padx=6, pady=6)

            # Batch Class Scan
            self.btn_attendance = ctk.CTkButton(
                self.sidebar_actions, text="📸 BATCH CLASS SCAN",
                command=self.start_live_attendance, height=44,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#006400", hover_color="#008000"
            )
            self.btn_attendance.pack(fill="x", padx=6, pady=6)

            # Student Registration
            ctk.CTkButton(
                self.sidebar_actions, text="👤 Register Student",
                command=self.open_registration_window,
                fg_color="#1f538d", hover_color="#14375e", height=34
            ).pack(fill="x", padx=6, pady=5)

            # Student Directory
            ctk.CTkButton(
                self.sidebar_actions, text="🔍 Student Directory",
                command=self.search_student,
                fg_color="#2b2b2b", hover_color="#404040", height=34
            ).pack(fill="x", padx=6, pady=5)

            # Curriculum & Faculty Matrix
            self.btn_teacher = ctk.CTkButton(
                self.sidebar_actions, text="📚 Curriculum Matrix",
                command=self.open_teacher_profile_window,
                fg_color="#2d3142", hover_color="#4f5d75", height=34
            )
            self.btn_teacher.pack(fill="x", padx=6, pady=5)

            # Train AI Brain
            self.btn_train = ctk.CTkButton(
                self.sidebar_actions, text="🧠 Train AI Brain",
                command=self.train_model,
                fg_color="#cc7000", hover_color="#e68a00", height=34
            )
            self.btn_train.pack(fill="x", padx=6, pady=5)

            # Delete Student
            ctk.CTkButton(
                self.sidebar_actions, text="🗑️ Delete Student",
                command=self.delete_student,
                fg_color="#8b0000", hover_color="#a52a2a", height=34
            ).pack(fill="x", padx=6, pady=5)

    def update_session_display(self):
        if self.current_user:
            role_label = f"[{self.current_user['role'].upper()}]"
            user_text = f"● Active: {self.current_user['name']} ({self.current_user['employee_id']}) • {self.current_user['department']} • {role_label}"
            self.lbl_session.configure(text=user_text, text_color="#38bdf8")
            self.btn_auth.configure(text="Logout", fg_color="#8b0000", hover_color="#a52a2a", command=self.logout)
            self.btn_lock.pack(side="right", padx=6, pady=8)
            self.btn_change_pass.pack(side="right", padx=6, pady=8)
        else:
            self.lbl_session.configure(text="● Standby — Authentication Required", text_color="#94a3b8")
            self.btn_auth.configure(text="Faculty Login", fg_color="#1f538d", hover_color="#14375e", command=self.open_auth_window)
            self.btn_lock.pack_forget()
            self.btn_change_pass.pack_forget()

        self.render_role_interface()

    def lock_terminal(self):
        if not self.current_user or self.is_terminal_locked:
            return

        self.is_terminal_locked = True
        lock_win = ctk.CTkToplevel(self)
        lock_win.title("Terminal Locked")
        lock_win.geometry("450x380")
        lock_win.transient(self)
        lock_win.lift()
        lock_win.focus_force()
        lock_win.grab_set()

        def on_attempt_close():
            pass
        lock_win.protocol("WM_DELETE_WINDOW", on_attempt_close)

        ctk.CTkLabel(lock_win, text="🔒", font=ctk.CTkFont(size=44)).pack(pady=(22, 4))
        ctk.CTkLabel(lock_win, text="TERMINAL LOCKED", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffcc00").pack(pady=3)
        ctk.CTkLabel(lock_win, text=f"Active Session: {self.current_user['name']} ({self.current_user['employee_id']})",
                     font=ctk.CTkFont(size=13), text_color="#00ffcc").pack(pady=3)

        ctk.CTkLabel(lock_win, text="Enter your account password to resume session:", font=ctk.CTkFont(size=12)).pack(pady=(15, 6))
        pwd_entry = ctk.CTkEntry(lock_win, placeholder_text="Password", show="*", width=260)
        pwd_entry.pack(pady=6)
        pwd_entry.focus_set()

        def do_unlock():
            entered = pwd_entry.get()
            if not entered:
                return
            if verify_teacher_password(self.current_user["id"], entered):
                self.is_terminal_locked = False
                self.last_user_activity = time.time()
                lock_win.destroy()
            else:
                self.show_error("Access Denied", "Incorrect password! Terminal remains locked.", parent=lock_win)
                pwd_entry.delete(0, 'end')

        pwd_entry.bind("<Return>", lambda _: do_unlock())

        ctk.CTkButton(lock_win, text="Unlock Terminal", command=do_unlock,
                      fg_color="#006400", hover_color="#008000", width=220, height=36).pack(pady=12)

        def switch_user():
            self.is_terminal_locked = False
            lock_win.destroy()
            self.logout()
            self.open_auth_window()

        ctk.CTkButton(lock_win, text="Switch User / Logout", command=switch_user,
                      fg_color="#333333", hover_color="#555555", width=220).pack(pady=4)

    def logout(self):
        self.current_user = None
        self.update_session_display()
        self.refresh_dashboard_metrics()
        self.show_info("Logged Out", "You have been securely logged out.")

    def require_login(self):
        if not self.current_user:
            self.show_warning("Authentication Required", "Please log in with your Faculty/Teacher account to proceed.")
            self.open_auth_window()
            return False
        return True

    def require_admin(self):
        if not self.require_login():
            return False
        if self.current_user["role"] != "admin":
            self.show_error("Access Denied", "Administrator privileges required!\nPlease log in with an Administrator account (e.g. ADMIN01).")
            return False
        return True

    def update_roster_subject_dropdown(self):
        if self.current_user and self.current_user["role"] != "admin":
            subjects = get_subjects_by_teacher(self.current_user["id"])
        else:
            subjects = get_all_subjects()

        subject_options = ["All Registered Students"]
        self.subject_map = {}
        for s in subjects:
            key = f"[{s['subject_code']}] {s['subject_name']} | {s['branch']}-Sec {s['section']} (Teacher: {s['teacher_name']})"
            subject_options.append(key)
            self.subject_map[key] = s

        self.roster_subject_menu.configure(values=subject_options)
        if self.roster_subject_var.get() not in subject_options:
            self.roster_subject_var.set("All Registered Students")

    def refresh_dashboard_metrics(self):
        self.update_roster_subject_dropdown()
        self.update_session_display()

        total_students = 0
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]
            conn.close()
            self.lbl_total_students.configure(text=str(total_students))
        except:
            self.lbl_total_students.configure(text="0")

        teachers = get_all_teachers()
        self.lbl_total_teachers.configure(text=str(len(teachers)))

        today = datetime.now().strftime("%Y%m%d")
        present_count = 0

        if ATTENDANCE_DIR.exists():
            sheets = list(ATTENDANCE_DIR.glob(f"Attendance_*_{today}*.csv")) + list(ATTENDANCE_DIR.glob(f"Attendance_{today}*.csv"))
            unique_sheets = list(set(sheets))
            self.lbl_sheets.configure(text=f"{len(unique_sheets)} Generated")

            if unique_sheets:
                latest_sheet = max(unique_sheets, key=os.path.getctime)
                try:
                    df = pd.read_csv(latest_sheet)
                    present_count = len(df)
                except:
                    pass

        self.lbl_progress_text.configure(text=f"{present_count} / {total_students} Present Today")
        if total_students > 0:
            self.progress_bar.set(present_count / total_students)
        else:
            self.progress_bar.set(0)

        self.populate_roster()
        if hasattr(self, 'btn_attendance') and self.btn_attendance and self.btn_attendance.cget("state") == "disabled":
            self.after(5000, self.refresh_dashboard_metrics)

    def populate_roster(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = ["Roll Number", "Name", "Branch & Section", "Attendance Status", "Time Marked"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(self.table_frame, text=text, font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=col, pady=6, padx=5, sticky="ew")

        selected_key = self.roster_subject_var.get()
        target_subject = self.subject_map.get(selected_key) if hasattr(self, 'subject_map') else None

        all_students = {}

        if target_subject:
            deg = target_subject["degree"]
            yr = target_subject["year"]
            br = target_subject["branch"]
            sec = target_subject["section"]
            sub_id = target_subject["id"]
            sub_code = target_subject["subject_code"]

            class_students = get_students_by_class(deg, yr, br, sec)
            for r, n, g, d, y, b, s in class_students:
                all_students[str(r)] = {
                    "name": n,
                    "branch_sec": f"{b} - Sec {s}",
                    "status": "ABSENT",
                    "time": "--"
                }

            today_date = datetime.now().strftime("%Y-%m-%d")
            db_records = get_attendance_for_subject_date(sub_id, today_date)
            for r, n, b, s, tm, status in db_records:
                roll_str = str(r)
                if roll_str in all_students:
                    all_students[roll_str]["status"] = status.upper()
                    all_students[roll_str]["time"] = tm

            today_str = datetime.now().strftime("%Y%m%d")
            if ATTENDANCE_DIR.exists():
                matching_sheets = list(ATTENDANCE_DIR.glob(f"Attendance_{sub_code}_{br}_{sec}_{today_str}*.csv"))
                if matching_sheets:
                    latest = max(matching_sheets, key=os.path.getctime)
                    try:
                        df = pd.read_csv(latest)
                        for _, row in df.iterrows():
                            roll_str = str(row['Roll Number'])
                            if roll_str in all_students:
                                all_students[roll_str]["status"] = "PRESENT"
                                all_students[roll_str]["time"] = row['Time Marked']
                    except:
                        pass
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT roll_number, name, branch, section FROM students ORDER BY roll_number ASC")
                for r, n, b, s in cursor.fetchall():
                    all_students[str(r)] = {
                        "name": n,
                        "branch_sec": f"{b} - Sec {s}",
                        "status": "ABSENT",
                        "time": "--"
                    }
                conn.close()
            except Exception:
                pass

            today = datetime.now().strftime("%Y%m%d")
            if ATTENDANCE_DIR.exists():
                sheets = list(ATTENDANCE_DIR.glob(f"Attendance_*_{today}*.csv")) + list(ATTENDANCE_DIR.glob(f"Attendance_{today}*.csv"))
                if sheets:
                    latest_sheet = max(sheets, key=os.path.getctime)
                    try:
                        df = pd.read_csv(latest_sheet)
                        for index, row in df.iterrows():
                            roll = str(row['Roll Number'])
                            if roll in all_students:
                                all_students[roll]["status"] = "PRESENT"
                                all_students[roll]["time"] = row['Time Marked']
                    except:
                        pass

        row_idx = 1
        if not all_students:
            msg = "No students registered in this section yet." if target_subject else "No students registered in database."
            ctk.CTkLabel(self.table_frame, text=msg, text_color="gray").grid(
                row=1, column=0, columnspan=5, pady=25)
            return

        for roll, data in all_students.items():
            ctk.CTkLabel(self.table_frame, text=roll).grid(row=row_idx, column=0, pady=5)
            ctk.CTkLabel(self.table_frame, text=data["name"]).grid(row=row_idx, column=1, pady=5)
            ctk.CTkLabel(self.table_frame, text=data["branch_sec"]).grid(row=row_idx, column=2, pady=5)

            status_color = "#00ffcc" if data["status"] == "PRESENT" else "#ff4444"
            ctk.CTkLabel(self.table_frame, text=data["status"], text_color=status_color,
                         font=ctk.CTkFont(weight="bold")).grid(row=row_idx, column=3, pady=5)
            ctk.CTkLabel(self.table_frame, text=data["time"]).grid(row=row_idx, column=4, pady=5)
            row_idx += 1

    def reset_attendance(self):
        if not self.require_admin():
            return

        pwd = self.prompt_input("Security Verification", "Enter your password to authorize resetting today's attendance:", is_password=True)
        if not pwd:
            return

        if not verify_teacher_password(self.current_user["id"], pwd):
            self.show_error("Security Error", "Incorrect password! Reset operation denied.")
            return

        today = datetime.now().strftime("%Y%m%d")
        today_db = datetime.now().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance_records WHERE date = ?", (today_db,))
            conn.commit()
            conn.close()
        except Exception:
            pass

        if ATTENDANCE_DIR.exists():
            sheets = list(ATTENDANCE_DIR.glob(f"Attendance_*_{today}*.csv")) + list(ATTENDANCE_DIR.glob(f"Attendance_{today}*.csv"))
            for sheet in sheets:
                try:
                    os.remove(sheet)
                except:
                    pass
        self.refresh_dashboard_metrics()
        self.show_info("Success", "Today's attendance records have been reset securely.")

    def open_registration_window(self):
        if not self.require_admin():
            return

        reg_window = ctk.CTkToplevel(self)
        reg_window.title("Register Student")
        reg_window.geometry("450x660")
        reg_window.transient(self)
        reg_window.lift()
        reg_window.focus_force()
        reg_window.grab_set()
        self.active_modal = reg_window

        def on_close():
            self.active_modal = None
            reg_window.destroy()

        reg_window.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(reg_window, text="Student Registration", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=15)
        roll_entry = ctk.CTkEntry(reg_window, placeholder_text="Roll Number (Numbers Only)", width=260)
        roll_entry.pack(pady=8)
        name_entry = ctk.CTkEntry(reg_window, placeholder_text="Full Name", width=260)
        name_entry.pack(pady=8)

        gender_var = ctk.StringVar(value="Select Gender")
        ctk.CTkOptionMenu(reg_window, variable=gender_var, values=["Male", "Female", "Neutral"], width=260).pack(
            pady=8)

        year_var = ctk.StringVar(value="Select Academic Year")
        year_menu = ctk.CTkOptionMenu(reg_window, variable=year_var, values=["Select Degree First"], width=260,
                                      state="disabled")

        def update_years(choice):
            year_menu.configure(state="normal")
            if choice == "BTECH":
                year_menu.configure(values=["1st Year", "2nd Year", "3rd Year", "4th Year"])
            elif choice in ["MTECH", "BBA"]:
                year_menu.configure(
                    values=["1st Year", "2nd Year", "3rd Year"] if choice == "BBA" else ["1st Year", "2nd Year"])
            elif choice == "PHD":
                year_menu.configure(values=["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"])
            year_var.set("Select Academic Year")

        degree_var = ctk.StringVar(value="Select Degree")
        ctk.CTkOptionMenu(reg_window, variable=degree_var, values=["BTECH", "MTECH", "PHD", "BBA"], width=260,
                          command=update_years).pack(pady=8)
        year_menu.pack(pady=8)

        branch_var = ctk.StringVar(value="Select Branch")
        ctk.CTkOptionMenu(reg_window, variable=branch_var,
                          values=["CSE", "MECHANICAL", "CHEMICAL", "ELECTRICAL", "ECE", "ECE-IOT", "IT", "NONE"],
                          width=260).pack(pady=8)
        section_var = ctk.StringVar(value="Select Section")
        ctk.CTkOptionMenu(reg_window, variable=section_var, values=["A", "B", "C", "D", "NONE"], width=260).pack(
            pady=8)

        def on_registration_done(success, msg, branch, section):
            btn_submit.configure(text="Open Camera & Capture", state="normal")
            if success:
                self.show_info("Registration Complete", msg + f"\nStudent automatically enrolled in {branch} Section {section}!", parent=self)
                self.refresh_dashboard_metrics()
                on_close()
            else:
                reg_window.deiconify()
                reg_window.lift()
                reg_window.focus_force()
                reg_window.grab_set()
                self.show_error("Registration Stopped", msg, parent=reg_window)

        def submit_form():
            roll, name = roll_entry.get().strip(), name_entry.get().strip()
            gender, degree, year = gender_var.get(), degree_var.get(), year_var.get()
            branch = branch_var.get() if branch_var.get() != "NONE" else ""
            section = section_var.get() if section_var.get() != "NONE" else ""

            if not roll.isdigit() or not name or degree == "Select Degree" or year in ["Select Academic Year",
                                                                                       "Select Degree First"] or gender == "Select Gender":
                self.show_error("Validation Error", "Please fill out all required fields properly.", parent=reg_window)
                return

            try:
                from src.registration import register_student
            except Exception as ex:
                self.show_error("Module Error", f"Failed to load registration module:\n{str(ex)}", parent=reg_window)
                return

            btn_submit.configure(text="Launching Camera... Please Look at Camera", state="disabled")
            reg_window.grab_release()
            reg_window.withdraw()

            def run_capture_worker():
                try:
                    success, msg = register_student(roll, name, gender, degree, year, branch, section)
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    success, msg = False, f"Unexpected error during capture: {str(ex)}"
                self.after(0, lambda: on_registration_done(success, msg, branch, section))

            threading.Thread(target=run_capture_worker, daemon=True).start()

        btn_submit = ctk.CTkButton(reg_window, text="Open Camera & Capture", command=submit_form,
                                   fg_color="#006400", hover_color="#008000", height=38,
                                   font=ctk.CTkFont(size=14, weight="bold"))
        btn_submit.pack(pady=20)

    def search_student(self):
        if not self.require_login():
            return

        roll = self.prompt_input("Search Student Database", "Enter Roll Number to search:")
        if roll and roll.isdigit():
            from src.registration import search_student_record
            found, record, img_count = search_student_record(roll)
            if found:
                info = (
                    f"Roll Number: {record[0]}\nName: {record[1]}\nGender: {record[2]}\nDegree: {record[3]}\nYear: {record[4]}\n"
                    f"Branch: {record[5]}\nSection: {record[6]}\nRegistered: {record[7]}\nFace Images: {img_count}/5")
                self.show_info("Record Found", info)
            else:
                self.show_error("Not Found", f"No record found for Roll Number {roll}")

    def delete_student(self):
        if not self.require_admin():
            return

        roll = self.prompt_input("Delete Student Record", "Enter Roll Number to permanently DELETE:")
        if not roll or not roll.isdigit():
            return

        pwd = self.prompt_input("Security Verification", f"Enter your password to authorize deleting student {roll}:", is_password=True)
        if not pwd:
            return

        ok, msg = delete_student_secure(roll, self.current_user, pwd)
        if ok:
            student_dir = Path(BASE_DIR) / "data" / "known_faces" / roll
            if student_dir.exists():
                import shutil
                shutil.rmtree(student_dir)
            self.refresh_dashboard_metrics()
            self.show_info("Deleted", msg)
        else:
            self.show_error("Security Error", msg)

    def train_model(self):
        if not self.require_admin():
            return

        if hasattr(self, 'btn_train') and self.btn_train:
            self.btn_train.configure(text="Training... Please Wait", state="disabled")
        self.update()
        from src.recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        recognizer.train_system()
        if hasattr(self, 'btn_train') and self.btn_train:
            self.btn_train.configure(text="🧠 Train AI Brain", state="normal")
        self.refresh_dashboard_metrics()
        self.show_info("Success", "AI Recognizer Model trained successfully!")

    # AUTHENTICATION WINDOW (LOGIN & SECURE REGISTRATION)
    def open_auth_window(self):
        auth_win = ctk.CTkToplevel(self)
        auth_win.title("SmartClass Vision - Authentication")
        auth_win.geometry("520x620")
        auth_win.resizable(False, False)
        auth_win.transient(self)
        auth_win.lift()
        auth_win.focus_force()
        auth_win.grab_set()
        self.active_modal = auth_win

        def on_close():
            self.active_modal = None
            auth_win.destroy()

        auth_win.protocol("WM_DELETE_WINDOW", on_close)

        tabs = ctk.CTkTabview(auth_win)
        tabs.pack(fill="both", expand=True, padx=15, pady=15)
        tab_login = tabs.add("Teacher Login")
        tab_signup = tabs.add("Create Account")

        # TAB 1: LOGIN
        ctk.CTkLabel(tab_login, text="Faculty / Staff Login", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(tab_login, text="Enter your Employee ID and password to access the system.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 20))

        login_emp = ctk.CTkEntry(tab_login, placeholder_text="Employee ID (e.g. ADMIN01 or EMP101)", width=320)
        login_emp.pack(pady=10)
        login_pwd = ctk.CTkEntry(tab_login, placeholder_text="Password", show="*", width=320)
        login_pwd.pack(pady=10)

        def do_login():
            emp = login_emp.get().strip()
            pwd = login_pwd.get()
            if not emp or not pwd:
                self.show_error("Error", "Please enter Employee ID and Password!", parent=auth_win)
                return

            ok, msg, user = authenticate_teacher(emp, pwd)
            if ok:
                self.current_user = user
                self.last_user_activity = time.time()
                self.update_session_display()
                self.refresh_dashboard_metrics()
                on_close()
                self.show_info("Login Successful", f"Welcome, {user['name']}!\nAuthenticated as [{user['role'].upper()}].", parent=self)
            else:
                self.show_error("Login Failed", msg, parent=auth_win)

        ctk.CTkButton(tab_login, text="Login Securely", command=do_login,
                      fg_color="#006400", hover_color="#008000", height=40, width=320).pack(pady=25)

        # TAB 2: SIGNUP / CREATE ACCOUNT (FACULTY OR ADMIN)
        ctk.CTkLabel(tab_signup, text="Create New User Account", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(6, 2))

        sign_emp = ctk.CTkEntry(tab_signup, placeholder_text="Employee ID (e.g. EMP-202 or ADMIN02)", width=320)
        sign_emp.pack(pady=4)
        sign_name = ctk.CTkEntry(tab_signup, placeholder_text="Full Name (e.g. Dr. K. Sharma)", width=320)
        sign_name.pack(pady=4)

        dept_var = ctk.StringVar(value="CSE")
        ctk.CTkOptionMenu(tab_signup, variable=dept_var,
                          values=["CSE", "IT", "ECE", "ELECTRICAL", "MECHANICAL", "CHEMICAL", "ADMINISTRATION"],
                          width=320).pack(pady=4)

        sign_email = ctk.CTkEntry(tab_signup, placeholder_text="Email Address (Optional)", width=320)
        sign_email.pack(pady=4)

        role_choice_var = ctk.StringVar(value="Faculty (Teacher)")
        role_frame = ctk.CTkFrame(tab_signup, fg_color="transparent")
        role_frame.pack(pady=4)
        ctk.CTkLabel(role_frame, text="Account Type:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8)

        master_box = ctk.CTkFrame(tab_signup, fg_color="#2b0938", corner_radius=8)
        master_key_entry = ctk.CTkEntry(master_box, placeholder_text="🔑 Admin Master Authorization Key", show="*", width=300)
        lbl_master_desc = ctk.CTkLabel(master_box, text="Institutional authorization key required for Admin accounts",
                                       font=ctk.CTkFont(size=11), text_color="#d8bbff")

        def on_type_changed(val):
            if val == "System Administrator":
                dept_var.set("ADMINISTRATION")
                master_box.pack(pady=4, padx=20, fill="x")
                master_key_entry.pack(pady=(6, 2), padx=10)
                lbl_master_desc.pack(pady=(0, 6))
            else:
                master_box.pack_forget()

        ctk.CTkOptionMenu(role_frame, variable=role_choice_var,
                          values=["Faculty (Teacher)", "System Administrator"],
                          command=on_type_changed, width=190).pack(side="left")

        sign_pwd = ctk.CTkEntry(tab_signup, placeholder_text="Set Password (Min 6 characters)", show="*", width=320)
        sign_pwd.pack(pady=4)
        sign_pwd_conf = ctk.CTkEntry(tab_signup, placeholder_text="Confirm Password", show="*", width=320)
        sign_pwd_conf.pack(pady=4)

        def do_register():
            emp = sign_emp.get().strip()
            name = sign_name.get().strip()
            dept = dept_var.get()
            email = sign_email.get().strip()
            pwd = sign_pwd.get()
            pwd_conf = sign_pwd_conf.get()
            is_admin = (role_choice_var.get() == "System Administrator")
            assigned_role = "admin" if is_admin else "teacher"

            if not emp or not name or not pwd:
                self.show_error("Error", "Employee ID, Name, and Password are required!", parent=auth_win)
                return
            if pwd != pwd_conf:
                self.show_error("Error", "Passwords do not match!", parent=auth_win)
                return
            if len(pwd) < 6:
                self.show_error("Error", "Password must be at least 6 characters long!", parent=auth_win)
                return

            if is_admin:
                candidate_key = master_key_entry.get().strip()
                if not candidate_key:
                    self.show_error("Authorization Key Required",
                                    "Admin Master Authorization Key is required to create an Administrator account!", parent=auth_win)
                    return
                if not verify_admin_master_key(candidate_key):
                    self.show_error("Authorization Denied",
                                    "Invalid Admin Master Authorization Key!\nOnly authorized institutional personnel can register as Administrator.", parent=auth_win)
                    return

            ok, msg, tid = register_teacher_secure(emp, name, dept, email, pwd, role=assigned_role)
            if ok:
                role_label = "Administrator" if is_admin else "Teacher"
                self.show_info("Account Created", f"{role_label} account created securely for {name}!\nYou can now log in.", parent=auth_win)
                tabs.set("Teacher Login")
                login_emp.delete(0, 'end')
                login_emp.insert(0, emp)
            else:
                self.show_error("Registration Failed", msg, parent=auth_win)

        ctk.CTkButton(tab_signup, text="Create Secure Account", command=do_register,
                      fg_color="#1f538d", hover_color="#14375e", height=36, width=320).pack(pady=8)

    def open_change_password_window(self):
        if not self.require_login():
            return

        cp_win = ctk.CTkToplevel(self)
        cp_win.title("Change Password")
        cp_win.geometry("380x300")
        cp_win.transient(self)
        cp_win.lift()
        cp_win.focus_force()
        cp_win.grab_set()
        self.active_modal = cp_win

        def on_close():
            self.active_modal = None
            cp_win.destroy()

        cp_win.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(cp_win, text="Change Password", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        old_pwd_entry = ctk.CTkEntry(cp_win, placeholder_text="Current Password", show="*", width=260)
        old_pwd_entry.pack(pady=8)
        new_pwd_entry = ctk.CTkEntry(cp_win, placeholder_text="New Password (Min 6 chars)", show="*", width=260)
        new_pwd_entry.pack(pady=8)
        conf_pwd_entry = ctk.CTkEntry(cp_win, placeholder_text="Confirm New Password", show="*", width=260)
        conf_pwd_entry.pack(pady=8)

        def save_new_pwd():
            old_p = old_pwd_entry.get()
            new_p = new_pwd_entry.get()
            conf_p = conf_pwd_entry.get()

            if new_p != conf_p:
                self.show_error("Error", "New passwords do not match!", parent=cp_win)
                return

            ok, msg = change_teacher_password(self.current_user["id"], old_p, new_p)
            if ok:
                on_close()
                self.show_info("Success", msg, parent=self)
            else:
                self.show_error("Error", msg, parent=cp_win)

        ctk.CTkButton(cp_win, text="Update Password", command=save_new_pwd,
                      fg_color="#006400", hover_color="#008000", width=200).pack(pady=15)

    # TEACHER PROFILE & SUBJECT ALLOTMENT WINDOW
    def open_teacher_profile_window(self):
        if not self.require_login():
            return

        prof_win = ctk.CTkToplevel(self)
        prof_win.title("Faculty Portal - Profile & Subject Allotment")
        prof_win.geometry("860x700")
        prof_win.transient(self)
        prof_win.lift()
        prof_win.focus_force()
        prof_win.grab_set()
        self.active_modal = prof_win

        def on_close():
            self.active_modal = None
            prof_win.destroy()

        prof_win.protocol("WM_DELETE_WINDOW", on_close)

        tabs = ctk.CTkTabview(prof_win)
        tabs.pack(fill="both", expand=True, padx=15, pady=15)
        tab_subjects = tabs.add("My Subjects & Section Students")
        tab_faculty = tabs.add("Faculty Directory")

        # TAB 1: MY SUBJECTS & AUTO-ENROLLED SECTION STUDENTS
        tab_subjects.grid_columnconfigure((0, 1), weight=1)
        tab_subjects.grid_rowconfigure(0, weight=1)

        subs_box = ctk.CTkFrame(tab_subjects)
        subs_box.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(subs_box, text=f"Subjects Allotted to You ({self.current_user['name']})",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=8)

        subs_scroll = ctk.CTkScrollableFrame(subs_box, height=220)
        subs_scroll.pack(fill="both", expand=True, padx=8, pady=5)

        students_box = ctk.CTkFrame(tab_subjects)
        students_box.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        lbl_students_title = ctk.CTkLabel(students_box, text="Section Students (Auto-Enrolled): 0",
                                          font=ctk.CTkFont(size=14, weight="bold"), text_color="#00ffcc")
        lbl_students_title.pack(pady=8)

        students_scroll = ctk.CTkScrollableFrame(students_box, height=220)
        students_scroll.pack(fill="both", expand=True, padx=8, pady=5)

        add_sub_frame = ctk.CTkFrame(tab_subjects)
        add_sub_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(add_sub_frame, text="Allot a New Subject to Your Account", font=ctk.CTkFont(weight="bold")).pack(pady=(6, 2))

        sub_inputs = ctk.CTkFrame(add_sub_frame, fg_color="transparent")
        sub_inputs.pack(pady=5)

        entry_sub_code = ctk.CTkEntry(sub_inputs, placeholder_text="Code (e.g. CS-301)", width=130)
        entry_sub_code.grid(row=0, column=0, padx=5, pady=3)
        entry_sub_name = ctk.CTkEntry(sub_inputs, placeholder_text="Subject Name (e.g. Data Structures)", width=200)
        entry_sub_name.grid(row=0, column=1, padx=5, pady=3)

        sub_deg_var = ctk.StringVar(value="BTECH")
        ctk.CTkOptionMenu(sub_inputs, variable=sub_deg_var, values=["BTECH", "MTECH", "PHD", "BBA"], width=100).grid(row=0, column=2, padx=5, pady=3)

        sub_yr_var = ctk.StringVar(value="2nd Year")
        ctk.CTkOptionMenu(sub_inputs, variable=sub_yr_var, values=["1st Year", "2nd Year", "3rd Year", "4th Year"], width=110).grid(row=0, column=3, padx=5, pady=3)

        sub_br_var = ctk.StringVar(value="CSE")
        ctk.CTkOptionMenu(sub_inputs, variable=sub_br_var, values=["CSE", "MECHANICAL", "CHEMICAL", "ELECTRICAL", "ECE", "ECE-IOT", "IT"], width=110).grid(row=0, column=4, padx=5, pady=3)

        sub_sec_var = ctk.StringVar(value="A")
        ctk.CTkOptionMenu(sub_inputs, variable=sub_sec_var, values=["A", "B", "C", "D"], width=80).grid(row=0, column=5, padx=5, pady=3)

        def load_section_students(deg, yr, br, sec):
            for w in students_scroll.winfo_children():
                w.destroy()
            students = get_students_by_class(deg, yr, br, sec)
            lbl_students_title.configure(text=f"{br} Sec {sec} Students (Auto-Enrolled): {len(students)}")
            if not students:
                ctk.CTkLabel(students_scroll, text=f"No students registered yet for {br} Sec {sec}.\nWhen a student registers with this section, they will automatically appear here!",
                             text_color="gray").pack(pady=20)
                return

            h_frame = ctk.CTkFrame(students_scroll, fg_color="transparent")
            h_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(h_frame, text="Roll No", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(h_frame, text="Student Name", width=140, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(h_frame, text="Class", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left")

            for r, n, g, d, y, b, s in students:
                row = ctk.CTkFrame(students_scroll)
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=str(r), width=80).pack(side="left")
                ctk.CTkLabel(row, text=n, width=140).pack(side="left")
                ctk.CTkLabel(row, text=f"{b}-{s}", width=100, text_color="#00ffcc").pack(side="left")

        def refresh_teacher_subjects():
            for w in subs_scroll.winfo_children():
                w.destroy()
            for w in students_scroll.winfo_children():
                w.destroy()
            lbl_students_title.configure(text="Section Students (Auto-Enrolled): 0")

            t_id = self.current_user["id"]
            if self.current_user["role"] == "admin":
                t_subjects = get_all_subjects()
            else:
                t_subjects = get_subjects_by_teacher(t_id)

            if not t_subjects:
                ctk.CTkLabel(subs_scroll, text="No subjects allotted yet.\nUse the form below to allot your class.", text_color="gray").pack(pady=20)
                return

            for idx, sub in enumerate(t_subjects):
                s_card = ctk.CTkFrame(subs_scroll)
                s_card.pack(fill="x", pady=4, padx=4)

                header_lbl = ctk.CTkLabel(s_card, text=f"[{sub['subject_code']}] {sub['subject_name']}",
                                          font=ctk.CTkFont(weight="bold"), text_color="#00ffcc")
                header_lbl.pack(anchor="w", padx=8, pady=(4, 0))

                sub_desc = f"{sub['degree']} | {sub['year']} | {sub['branch']} - Sec {sub['section']} (Teacher: {sub['teacher_name']})"
                ctk.CTkLabel(s_card, text=sub_desc, font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=8)

                btn_box = ctk.CTkFrame(s_card, fg_color="transparent")
                btn_box.pack(fill="x", padx=8, pady=4)

                deg, yr, br, sec = sub['degree'], sub['year'], sub['branch'], sub['section']
                ctk.CTkButton(btn_box, text="View Students", width=95, height=22, fg_color="#1f538d", hover_color="#14375e",
                              command=lambda d=deg, y=yr, b=br, s=sec: load_section_students(d, y, b, s)).pack(side="left")

                sub_id = sub['id']
                ctk.CTkButton(btn_box, text="Delete", width=55, height=22, fg_color="#8b0000", hover_color="#a52a2a",
                              command=lambda sid=sub_id: delete_sub_action(sid)).pack(side="right")

                if idx == 0:
                    load_section_students(deg, yr, br, sec)

        def delete_sub_action(sid):
            pwd = self.prompt_input("Security Verification", "Enter your password to authorize deleting this subject allotment:", parent=prof_win, is_password=True)
            if not pwd:
                return

            ok, msg = delete_subject_secure(sid, self.current_user, pwd)
            if ok:
                self.show_info("Success", msg, parent=prof_win)
                refresh_teacher_subjects()
                self.refresh_dashboard_metrics()
            else:
                self.show_error("Security Error", msg, parent=prof_win)

        def allot_subject():
            code = entry_sub_code.get().strip()
            name = entry_sub_name.get().strip()
            if not code or not name:
                self.show_error("Error", "Please enter Subject Code and Subject Name!", parent=prof_win)
                return

            ok, msg, sid = add_subject(self.current_user["id"], code, name, sub_deg_var.get(), sub_yr_var.get(), sub_br_var.get(), sub_sec_var.get())
            if ok:
                self.show_info("Success", msg, parent=prof_win)
                entry_sub_code.delete(0, 'end')
                entry_sub_name.delete(0, 'end')
                refresh_teacher_subjects()
                self.refresh_dashboard_metrics()
            else:
                self.show_error("Error", msg, parent=prof_win)

        ctk.CTkButton(add_sub_frame, text="Allot Subject to My Profile", command=allot_subject,
                      fg_color="#006400", hover_color="#008000", height=32).pack(pady=(0, 6))

        refresh_teacher_subjects()

        # TAB 2: FACULTY DIRECTORY
        tab_faculty.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab_faculty, text="Registered Faculty Members", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        fac_scroll = ctk.CTkScrollableFrame(tab_faculty, height=350)
        fac_scroll.pack(fill="both", expand=True, padx=15, pady=5)

        def refresh_fac_list():
            for w in fac_scroll.winfo_children():
                w.destroy()
            teachers = get_all_teachers()
            for t in teachers:
                card = ctk.CTkFrame(fac_scroll, corner_radius=8)
                card.pack(fill="x", pady=5, padx=5)

                title_color = "#00a8cc" if t["role"] == "admin" else "white"
                ctk.CTkLabel(card, text=f"{t['name']} ({t['employee_id']}) [{t['role'].upper()}]",
                             font=ctk.CTkFont(weight="bold"), text_color=title_color).pack(anchor="w", padx=10, pady=(6, 0))
                ctk.CTkLabel(card, text=f"Department: {t['department']} | Email: {t['email'] or 'N/A'}",
                             font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=10)

        refresh_fac_list()

    # =========================================================================
    # ADVANCED ADMINISTRATOR PORTAL (5-TAB COMPREHENSIVE CONTROL CENTER)
    # =========================================================================
    def open_admin_portal(self):
        if not self.require_admin():
            return

        admin_win = ctk.CTkToplevel(self)
        admin_win.title("SmartClass Vision - Administration")
        admin_win.geometry("1020x720")
        admin_win.transient(self)
        admin_win.lift()
        admin_win.focus_force()
        admin_win.grab_set()
        self.active_modal = admin_win

        def on_close():
            self.active_modal = None
            admin_win.destroy()

        admin_win.protocol("WM_DELETE_WINDOW", on_close)

        top_header = ctk.CTkFrame(admin_win, height=45, fg_color="#2b0938")
        top_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(top_header, text="🛡️ System Administration Portal",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color="#d8bbff").pack(side="left", padx=15, pady=8)
        ctk.CTkLabel(top_header, text=f"Admin: {self.current_user['name']} ({self.current_user['employee_id']})",
                     font=ctk.CTkFont(size=12), text_color="#00ffcc").pack(side="right", padx=15)

        adm_tabs = ctk.CTkTabview(admin_win)
        adm_tabs.pack(fill="both", expand=True, padx=15, pady=10)

        tab_fac = adm_tabs.add("Faculty Control")
        tab_std = adm_tabs.add("Student Directory & Transfers")
        tab_cur = adm_tabs.add("Curriculum & Allotments")
        tab_aud = adm_tabs.add("Attendance Audits")
        tab_sec = adm_tabs.add("Security & Spoof Audits")
        tab_int = adm_tabs.add("Integrity & Backups")
        tab_sys = adm_tabs.add("System Diagnostics")

        # -------------------------------------------------------------
        # ADMIN TAB 1: FACULTY CONTROL
        # -------------------------------------------------------------
        tab_fac.grid_columnconfigure(0, weight=3)
        tab_fac.grid_columnconfigure(1, weight=2)
        tab_fac.grid_rowconfigure(0, weight=1)

        fac_list_box = ctk.CTkFrame(tab_fac)
        fac_list_box.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(fac_list_box, text="Faculty Roster & Access Rights", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=8)

        fac_scroll = ctk.CTkScrollableFrame(fac_list_box, height=450)
        fac_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def refresh_admin_faculty():
            for w in fac_scroll.winfo_children():
                w.destroy()
            teachers = get_all_teachers()
            for t in teachers:
                card = ctk.CTkFrame(fac_scroll, corner_radius=8)
                card.pack(fill="x", pady=4, padx=3)

                role_color = "#00ffcc" if t["role"] == "admin" else "white"
                ctk.CTkLabel(card, text=f"{t['name']} ({t['employee_id']}) [{t['role'].upper()}]",
                             font=ctk.CTkFont(weight="bold"), text_color=role_color).pack(anchor="w", padx=8, pady=(4, 0))
                ctk.CTkLabel(card, text=f"Dept: {t['department']} | Email: {t['email'] or 'N/A'}",
                             font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=8)

                is_locked = (t.get("failed_login_attempts", 0) >= 5) or (t.get("locked_until") is not None)
                if is_locked:
                    ctk.CTkLabel(card, text="⚠️ ACCOUNT LOCKED OUT (Too many failed passwords)",
                                 font=ctk.CTkFont(size=11, weight="bold"), text_color="#ff4444").pack(anchor="w", padx=8)

                bar = ctk.CTkFrame(card, fg_color="transparent")
                bar.pack(fill="x", padx=8, pady=4)

                tid = t["id"]
                tname = t["name"]
                trole = t["role"]

                ctk.CTkButton(bar, text="Reset Pwd", width=75, height=22, fg_color="#3d5a80", hover_color="#293241",
                              command=lambda target_id=tid, name=tname: on_reset_pwd(target_id, name)).pack(side="left", padx=2)

                toggle_text = "Demote" if trole == "admin" else "Make Admin"
                new_role = "teacher" if trole == "admin" else "admin"
                ctk.CTkButton(bar, text=toggle_text, width=85, height=22, fg_color="#5a189a", hover_color="#7b2cbf",
                              command=lambda target_id=tid, r=new_role: on_toggle_role(target_id, r)).pack(side="left", padx=2)

                if is_locked:
                    ctk.CTkButton(bar, text="Unlock", width=65, height=22, fg_color="#006400", hover_color="#008000",
                                  command=lambda target_id=tid: on_unlock_fac(target_id)).pack(side="left", padx=2)

                ctk.CTkButton(bar, text="Delete", width=60, height=22, fg_color="#8b0000", hover_color="#a52a2a",
                              command=lambda target_id=tid: on_delete_fac(target_id)).pack(side="right", padx=2)

        def on_unlock_fac(tid):
            ok, msg = unlock_teacher_account(tid, self.current_user)
            if ok:
                self.show_info("Account Unlocked", msg, parent=admin_win)
                refresh_admin_faculty()
            else:
                self.show_error("Error", msg, parent=admin_win)

        def on_reset_pwd(tid, tname):
            new_p = self.prompt_input("Admin Password Reset", f"Enter new password for {tname} (min 6 chars):", parent=admin_win)
            if not new_p:
                return
            ok, msg = admin_reset_teacher_password(tid, new_p)
            if ok:
                self.show_info("Success", msg, parent=admin_win)
            else:
                self.show_error("Error", msg, parent=admin_win)

        def on_toggle_role(tid, new_role):
            if tid == self.current_user["id"]:
                self.show_error("Denied", "You cannot demote your own active admin account!", parent=admin_win)
                return
            ok, msg = update_teacher_role(tid, new_role)
            if ok:
                self.show_info("Role Updated", msg, parent=admin_win)
                refresh_admin_faculty()
            else:
                self.show_error("Error", msg, parent=admin_win)

        def on_delete_fac(tid):
            pwd = self.prompt_input("Admin Verification", "Enter your Administrator password to authorize deletion:", parent=admin_win, is_password=True)
            if not pwd:
                return
            ok, msg = delete_teacher_secure(tid, self.current_user, pwd)
            if ok:
                self.show_info("Success", msg, parent=admin_win)
                refresh_admin_faculty()
                self.refresh_dashboard_metrics()
            else:
                self.show_error("Error", msg, parent=admin_win)

        # Right: Add Faculty Form
        fac_add_box = ctk.CTkFrame(tab_fac)
        fac_add_box.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(fac_add_box, text="Register New Faculty / Admin", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=8)

        e_emp = ctk.CTkEntry(fac_add_box, placeholder_text="Faculty ID (e.g. EMP102)", width=220)
        e_emp.pack(pady=6)
        e_name = ctk.CTkEntry(fac_add_box, placeholder_text="Full Name", width=220)
        e_name.pack(pady=6)

        d_var = ctk.StringVar(value="CSE")
        ctk.CTkOptionMenu(fac_add_box, variable=d_var, values=["CSE", "IT", "ECE", "ELECTRICAL", "MECHANICAL", "CHEMICAL", "ADMIN"], width=220).pack(pady=6)

        e_mail = ctk.CTkEntry(fac_add_box, placeholder_text="Email Address", width=220)
        e_mail.pack(pady=6)

        e_pwd = ctk.CTkEntry(fac_add_box, placeholder_text="Initial Password (Min 6 chars)", show="*", width=220)
        e_pwd.pack(pady=6)

        role_var = ctk.StringVar(value="teacher")
        ctk.CTkOptionMenu(fac_add_box, variable=role_var, values=["teacher", "admin"], width=220).pack(pady=6)

        def on_add_fac():
            emp = e_emp.get().strip()
            nm = e_name.get().strip()
            pw = e_pwd.get()
            if not emp or not nm or not pw:
                self.show_error("Error", "Employee ID, Name, and Password are required!", parent=admin_win)
                return
            ok, msg, _ = register_teacher_secure(emp, nm, d_var.get(), e_mail.get().strip(), pw, role=role_var.get())
            if ok:
                self.show_info("Faculty Created", msg, parent=admin_win)
                e_emp.delete(0, 'end')
                e_name.delete(0, 'end')
                e_mail.delete(0, 'end')
                e_pwd.delete(0, 'end')
                refresh_admin_faculty()
                self.refresh_dashboard_metrics()
            else:
                self.show_error("Error", msg, parent=admin_win)

        ctk.CTkButton(fac_add_box, text="Save Faculty Account", command=on_add_fac,
                      fg_color="#006400", hover_color="#008000", height=34).pack(pady=15)

        refresh_admin_faculty()

        # -------------------------------------------------------------
        # ADMIN TAB 2: STUDENT DIRECTORY & SECTION TRANSFERS
        # -------------------------------------------------------------
        tab_std.grid_columnconfigure(0, weight=1)
        tab_std.grid_rowconfigure(1, weight=1)

        filter_bar = ctk.CTkFrame(tab_std, fg_color="transparent")
        filter_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(filter_bar, text="Filter Class:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        std_br_var = ctk.StringVar(value="ALL")
        std_sec_var = ctk.StringVar(value="ALL")

        std_table_scroll = ctk.CTkScrollableFrame(tab_std)
        std_table_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        std_table_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        def refresh_admin_students():
            for w in std_table_scroll.winfo_children():
                w.destroy()

            headers = ["Roll Number", "Full Name", "Gender", "Degree & Year", "Branch - Sec", "Actions"]
            for col, h in enumerate(headers):
                ctk.CTkLabel(std_table_scroll, text=h, font=ctk.CTkFont(weight="bold")).grid(
                    row=0, column=col, pady=5, padx=4, sticky="ew")

            all_s = get_all_students_master()
            sel_br = std_br_var.get()
            sel_sec = std_sec_var.get()

            row_num = 1
            for roll, nm, gen, deg, yr, br, sec, reg_at in all_s:
                if sel_br != "ALL" and br.upper() != sel_br.upper():
                    continue
                if sel_sec != "ALL" and sec.upper() != sel_sec.upper():
                    continue

                ctk.CTkLabel(std_table_scroll, text=str(roll)).grid(row=row_num, column=0, pady=3)
                ctk.CTkLabel(std_table_scroll, text=nm).grid(row=row_num, column=1, pady=3)
                ctk.CTkLabel(std_table_scroll, text=gen).grid(row=row_num, column=2, pady=3)
                ctk.CTkLabel(std_table_scroll, text=f"{deg} ({yr})").grid(row=row_num, column=3, pady=3)
                ctk.CTkLabel(std_table_scroll, text=f"{br} - Sec {sec}", text_color="#00ffcc").grid(row=row_num, column=4, pady=3)

                act_frame = ctk.CTkFrame(std_table_scroll, fg_color="transparent")
                act_frame.grid(row=row_num, column=5, pady=3)

                r_val = roll
                ctk.CTkButton(act_frame, text="Transfer/Edit", width=90, height=22, fg_color="#1f538d", hover_color="#14375e",
                              command=lambda r=r_val, n=nm, g=gen, d=deg, y=yr, b=br, s=sec: on_edit_student(r, n, g, d, y, b, s)).pack(side="left", padx=2)
                ctk.CTkButton(act_frame, text="Del", width=40, height=22, fg_color="#8b0000", hover_color="#a52a2a",
                              command=lambda r=r_val: on_delete_std(r)).pack(side="left", padx=2)

                row_num += 1

            if row_num == 1:
                ctk.CTkLabel(std_table_scroll, text="No students match the selected filter.", text_color="gray").grid(
                    row=1, column=0, columnspan=6, pady=25)

        ctk.CTkOptionMenu(filter_bar, variable=std_br_var, values=["ALL", "CSE", "IT", "ECE", "ELECTRICAL", "MECHANICAL", "CHEMICAL"],
                          width=120, command=lambda _: refresh_admin_students()).pack(side="left", padx=5)
        ctk.CTkOptionMenu(filter_bar, variable=std_sec_var, values=["ALL", "A", "B", "C", "D"],
                          width=90, command=lambda _: refresh_admin_students()).pack(side="left", padx=5)
        ctk.CTkButton(filter_bar, text="Refresh", width=80, command=refresh_admin_students).pack(side="right", padx=5)

        def on_edit_student(roll, cur_name, cur_gender, cur_deg, cur_yr, cur_br, cur_sec):
            t_win = ctk.CTkToplevel(admin_win)
            t_win.title(f"Transfer/Edit Student - Roll {roll}")
            t_win.geometry("400x440")
            t_win.transient(admin_win)
            t_win.lift()
            t_win.focus_force()
            t_win.grab_set()

            ctk.CTkLabel(t_win, text=f"Transfer/Edit Student #{roll}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=12)

            t_name = ctk.CTkEntry(t_win, width=240)
            t_name.insert(0, cur_name)
            t_name.pack(pady=6)

            t_gen_var = ctk.StringVar(value=cur_gender)
            ctk.CTkOptionMenu(t_win, variable=t_gen_var, values=["Male", "Female", "Neutral"], width=240).pack(pady=6)

            t_deg_var = ctk.StringVar(value=cur_deg)
            ctk.CTkOptionMenu(t_win, variable=t_deg_var, values=["BTECH", "MTECH", "PHD", "BBA"], width=240).pack(pady=6)

            t_yr_var = ctk.StringVar(value=cur_yr)
            ctk.CTkOptionMenu(t_win, variable=t_yr_var, values=["1st Year", "2nd Year", "3rd Year", "4th Year"], width=240).pack(pady=6)

            ctk.CTkLabel(t_win, text="Transfer Section & Branch:", font=ctk.CTkFont(weight="bold")).pack(pady=(8, 2))
            t_br_var = ctk.StringVar(value=cur_br)
            ctk.CTkOptionMenu(t_win, variable=t_br_var, values=["CSE", "IT", "ECE", "ELECTRICAL", "MECHANICAL", "CHEMICAL"], width=240).pack(pady=4)

            t_sec_var = ctk.StringVar(value=cur_sec)
            ctk.CTkOptionMenu(t_win, variable=t_sec_var, values=["A", "B", "C", "D"], width=240).pack(pady=4)

            def do_save_transfer():
                ok = update_student_details(roll, t_name.get().strip(), t_gen_var.get(), t_deg_var.get(), t_yr_var.get(), t_br_var.get(), t_sec_var.get())
                if ok:
                    t_win.destroy()
                    self.show_info("Transfer Complete", f"Student {roll} transferred to {t_br_var.get()} Section {t_sec_var.get()} successfully!", parent=admin_win)
                    refresh_admin_students()
                    self.refresh_dashboard_metrics()
                else:
                    self.show_error("Update Failed", "Could not update student details.", parent=t_win)

            ctk.CTkButton(t_win, text="Save & Transfer Section", fg_color="#006400", hover_color="#008000",
                          height=34, command=do_save_transfer).pack(pady=15)

        def on_delete_std(roll):
            pwd = self.prompt_input("Admin Verification", f"Enter Administrator password to delete student {roll}:", parent=admin_win, is_password=True)
            if not pwd:
                return
            ok, msg = delete_student_secure(roll, self.current_user, pwd)
            if ok:
                student_dir = Path(BASE_DIR) / "data" / "known_faces" / str(roll)
                if student_dir.exists():
                    import shutil
                    shutil.rmtree(student_dir)
                self.show_info("Deleted", msg, parent=admin_win)
                refresh_admin_students()
                self.refresh_dashboard_metrics()
            else:
                self.show_error("Error", msg, parent=admin_win)

        refresh_admin_students()

        # -------------------------------------------------------------
        # ADMIN TAB 3: CURRICULUM & ALLOTMENTS MASTER
        # -------------------------------------------------------------
        tab_cur.grid_columnconfigure(0, weight=1)
        tab_cur.grid_rowconfigure(1, weight=1)

        cur_ctrl = ctk.CTkFrame(tab_cur, fg_color="transparent")
        cur_ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        ctk.CTkLabel(cur_ctrl, text="Global Subject Allotments Master Matrix", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        cur_scroll = ctk.CTkScrollableFrame(tab_cur)
        cur_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        cur_scroll.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        def refresh_admin_curriculum():
            for w in cur_scroll.winfo_children():
                w.destroy()

            headers = ["Subject Code", "Subject Name", "Class Allotment", "Assigned Faculty", "Actions"]
            for col, h in enumerate(headers):
                ctk.CTkLabel(cur_scroll, text=h, font=ctk.CTkFont(weight="bold")).grid(
                    row=0, column=col, pady=5, padx=4, sticky="ew")

            subjects = get_all_subjects()
            teachers = get_all_teachers()

            for idx, s in enumerate(subjects, start=1):
                ctk.CTkLabel(cur_scroll, text=s["subject_code"], font=ctk.CTkFont(weight="bold")).grid(row=idx, column=0, pady=4)
                ctk.CTkLabel(cur_scroll, text=s["subject_name"]).grid(row=idx, column=1, pady=4)
                ctk.CTkLabel(cur_scroll, text=f"{s['branch']} Sec {s['section']} ({s['year']})", text_color="#00ffcc").grid(row=idx, column=2, pady=4)
                ctk.CTkLabel(cur_scroll, text=f"{s['teacher_name']} ({s.get('teacher_emp_id', '')})").grid(row=idx, column=3, pady=4)

                act_box = ctk.CTkFrame(cur_scroll, fg_color="transparent")
                act_box.grid(row=idx, column=4, pady=4)

                sub_id = s["id"]
                ctk.CTkButton(act_box, text="Reassign", width=75, height=22, fg_color="#3d5a80", hover_color="#293241",
                              command=lambda sid=sub_id, scode=s["subject_code"], t_list=teachers: on_reassign(sid, scode, t_list)).pack(side="left", padx=2)
                ctk.CTkButton(act_box, text="Delete", width=55, height=22, fg_color="#8b0000", hover_color="#a52a2a",
                              command=lambda sid=sub_id: on_del_sub(sid)).pack(side="left", padx=2)

        def on_reassign(sid, scode, teachers):
            r_win = ctk.CTkToplevel(admin_win)
            r_win.title(f"Reassign Subject {scode}")
            r_win.geometry("380x200")
            r_win.transient(admin_win)
            r_win.lift()
            r_win.focus_force()
            r_win.grab_set()

            ctk.CTkLabel(r_win, text=f"Reassign {scode} to Faculty:", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
            t_opts = [f"{t['name']} ({t['employee_id']})" for t in teachers]
            t_map = {f"{t['name']} ({t['employee_id']})": t["id"] for t in teachers}

            sel_t_var = ctk.StringVar(value=t_opts[0] if t_opts else "No Teachers")
            ctk.CTkOptionMenu(r_win, variable=sel_t_var, values=t_opts, width=280).pack(pady=10)

            def do_reassign():
                new_tid = t_map.get(sel_t_var.get())
                if new_tid:
                    reassign_subject_teacher(sid, new_tid)
                    r_win.destroy()
                    self.show_info("Success", "Subject successfully reassigned!", parent=admin_win)
                    refresh_admin_curriculum()
                    self.refresh_dashboard_metrics()

            ctk.CTkButton(r_win, text="Confirm Reassignment", fg_color="#006400", hover_color="#008000", command=do_reassign).pack(pady=15)

        def on_del_sub(sid):
            pwd = self.prompt_input("Admin Verification", "Enter Administrator password to delete subject:", parent=admin_win, is_password=True)
            if not pwd:
                return
            ok, msg = delete_subject_secure(sid, self.current_user, pwd)
            if ok:
                self.show_info("Success", msg, parent=admin_win)
                refresh_admin_curriculum()
                self.refresh_dashboard_metrics()
            else:
                self.show_error("Error", msg, parent=admin_win)

        refresh_admin_curriculum()

        # -------------------------------------------------------------
        # ADMIN TAB 4: ATTENDANCE AUDITS & ANALYTICS
        # -------------------------------------------------------------
        tab_aud.grid_columnconfigure(0, weight=1)
        tab_aud.grid_rowconfigure(1, weight=1)

        aud_top = ctk.CTkFrame(tab_aud, fg_color="transparent")
        aud_top.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        ctk.CTkLabel(aud_top, text="Official Attendance Audit Logs (Last 250 Records)", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(aud_top, text="Refresh Logs", width=100, command=lambda: refresh_admin_audits()).pack(side="right")

        aud_scroll = ctk.CTkScrollableFrame(tab_aud)
        aud_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        aud_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        def refresh_admin_audits():
            for w in aud_scroll.winfo_children():
                w.destroy()

            headers = ["Date & Time", "Subject", "Teacher", "Roll Number", "Student Name", "Class", "Action"]
            for col, h in enumerate(headers):
                ctk.CTkLabel(aud_scroll, text=h, font=ctk.CTkFont(weight="bold")).grid(
                    row=0, column=col, pady=5, padx=3, sticky="ew")

            logs = get_attendance_audit_logs(limit=250)
            if not logs:
                ctk.CTkLabel(aud_scroll, text="No historical attendance records logged yet.", text_color="gray").grid(
                    row=1, column=0, columnspan=7, pady=25)
                return

            for idx, item in enumerate(logs, start=1):
                ctk.CTkLabel(aud_scroll, text=f"{item['date']} {item['time_marked']}").grid(row=idx, column=0, pady=3)
                ctk.CTkLabel(aud_scroll, text=item["subject_code"], font=ctk.CTkFont(weight="bold")).grid(row=idx, column=1, pady=3)
                ctk.CTkLabel(aud_scroll, text=item["teacher_name"]).grid(row=idx, column=2, pady=3)
                ctk.CTkLabel(aud_scroll, text=item["roll_number"]).grid(row=idx, column=3, pady=3)
                ctk.CTkLabel(aud_scroll, text=item["name"]).grid(row=idx, column=4, pady=3)
                ctk.CTkLabel(aud_scroll, text=f"{item['branch']}-{item['section']}", text_color="#00ffcc").grid(row=idx, column=5, pady=3)

                lid = item["id"]
                ctk.CTkButton(aud_scroll, text="Delete", width=55, height=20, fg_color="#8b0000", hover_color="#a52a2a",
                              command=lambda log_id=lid: delete_single_audit(log_id)).grid(row=idx, column=6, pady=3)

        def delete_single_audit(log_id):
            delete_attendance_log(log_id)
            refresh_admin_audits()
            self.refresh_dashboard_metrics()

        refresh_admin_audits()

        # -------------------------------------------------------------
        # ADMIN TAB 5: ENTERPRISE SECURITY & SPOOF AUDITS
        # -------------------------------------------------------------
        tab_sec.grid_columnconfigure(0, weight=1)
        tab_sec.grid_rowconfigure(1, weight=1)

        sec_ctrl = ctk.CTkFrame(tab_sec, fg_color="transparent")
        sec_ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        ctk.CTkLabel(sec_ctrl, text="Security Audit Incident Log", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        ctk.CTkLabel(sec_ctrl, text="Severity:").pack(side="left", padx=(15, 4))
        sec_sev_var = ctk.StringVar(value="ALL")
        ctk.CTkOptionMenu(sec_ctrl, variable=sec_sev_var, values=["ALL", "CRITICAL", "WARNING", "INFO"],
                          width=100, command=lambda _: refresh_sec_logs()).pack(side="left")

        ctk.CTkLabel(sec_ctrl, text="Event:").pack(side="left", padx=(10, 4))
        sec_ev_var = ctk.StringVar(value="ALL")
        ctk.CTkOptionMenu(sec_ctrl, variable=sec_ev_var,
                          values=["ALL", "LOGIN_SUCCESS", "LOGIN_FAILED", "ACCOUNT_LOCKED", "ACCOUNT_UNLOCKED", "SPOOF_ATTEMPT", "TAMPER_DETECTED", "ATTENDANCE_SIGNED", "MASTER_KEY_ROTATED", "BACKUP_CREATED"],
                          width=170, command=lambda _: refresh_sec_logs()).pack(side="left")

        ctk.CTkButton(sec_ctrl, text="Refresh Logs", width=90, command=lambda: refresh_sec_logs()).pack(side="right", padx=5)

        sec_scroll = ctk.CTkScrollableFrame(tab_sec)
        sec_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        sec_scroll.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        def refresh_sec_logs():
            for w in sec_scroll.winfo_children():
                w.destroy()

            headers = ["Timestamp", "Severity", "Event Type", "User / Client", "Incident Details"]
            for col, h in enumerate(headers):
                ctk.CTkLabel(sec_scroll, text=h, font=ctk.CTkFont(weight="bold")).grid(
                    row=0, column=col, pady=5, padx=3, sticky="ew")

            logs = get_security_audit_logs(limit=250, severity_filter=sec_sev_var.get(), event_filter=sec_ev_var.get())
            if not logs:
                ctk.CTkLabel(sec_scroll, text="No security events recorded matching criteria.", text_color="gray").grid(
                    row=1, column=0, columnspan=5, pady=25)
                return

            for idx, item in enumerate(logs, start=1):
                sev = item["severity"]
                sev_color = "#ff4444" if sev == "CRITICAL" else ("#ffcc00" if sev == "WARNING" else "#00ffcc")

                ctk.CTkLabel(sec_scroll, text=item["timestamp"]).grid(row=idx, column=0, pady=3)
                ctk.CTkLabel(sec_scroll, text=f"[{sev}]", text_color=sev_color, font=ctk.CTkFont(weight="bold")).grid(row=idx, column=1, pady=3)
                ctk.CTkLabel(sec_scroll, text=item["event_type"], font=ctk.CTkFont(weight="bold")).grid(row=idx, column=2, pady=3)
                ctk.CTkLabel(sec_scroll, text=f"{item['user_identifier']} ({item['ip_or_host']})").grid(row=idx, column=3, pady=3)
                ctk.CTkLabel(sec_scroll, text=item["details"], justify="left", wraplength=380).grid(row=idx, column=4, pady=3, sticky="w")

        refresh_sec_logs()

        # -------------------------------------------------------------
        # ADMIN TAB 6: DATA INTEGRITY & DISASTER RECOVERY
        # -------------------------------------------------------------
        tab_int.grid_columnconfigure((0, 1), weight=1)
        tab_int.grid_rowconfigure(0, weight=1)

        # Left Card: HMAC-SHA256 File Tamper Verifier
        int_card = ctk.CTkFrame(tab_int)
        int_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(int_card, text="Attendance Sheet Integrity Verifier", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)
        ctk.CTkLabel(int_card, text="Verify attendance CSV cryptographic HMAC-SHA256 signatures against external file tampering or manual edits.",
                     font=ctk.CTkFont(size=12), text_color="gray", wraplength=380).pack(padx=15, pady=(0, 10))

        csv_options = []
        if ATTENDANCE_DIR.exists():
            csv_options = [p.name for p in sorted(ATTENDANCE_DIR.glob("*.csv"), reverse=True)]
        if not csv_options:
            csv_options = ["No Attendance Sheets Found"]

        sel_csv_var = ctk.StringVar(value=csv_options[0])
        csv_menu = ctk.CTkOptionMenu(int_card, variable=sel_csv_var, values=csv_options, width=380)
        csv_menu.pack(pady=8)

        lbl_result_box = ctk.CTkLabel(int_card, text="Select a sheet and click Verify.",
                                      font=ctk.CTkFont(size=12), justify="left", wraplength=400)
        lbl_result_box.pack(padx=20, pady=12)

        def do_verify_sheet():
            chosen = sel_csv_var.get()
            if not chosen or chosen == "No Attendance Sheets Found":
                return
            target_path = ATTENDANCE_DIR / chosen
            is_valid, msg = verify_file_integrity(target_path)
            res_color = "#00ffcc" if is_valid else "#ff4444"
            lbl_result_box.configure(text=msg, text_color=res_color)

        ctk.CTkButton(int_card, text="Verify Cryptographic Signature", command=do_verify_sheet,
                      fg_color="#006400", hover_color="#008000", height=34).pack(pady=10)

        # Right Card: Database Backups & Master Key Rotation
        bkp_card = ctk.CTkFrame(tab_int)
        bkp_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(bkp_card, text="Disaster Recovery & Master Key", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

        def do_backup():
            ok, msg = create_database_backup()
            if ok:
                self.show_info("Backup Complete", msg, parent=admin_win)
                refresh_backups()
            else:
                self.show_error("Backup Failed", msg, parent=admin_win)

        ctk.CTkButton(bkp_card, text="Create Instant Full Backup", command=do_backup,
                      fg_color="#1f538d", hover_color="#14375e", height=34, width=280).pack(pady=6)

        bkp_scroll = ctk.CTkScrollableFrame(bkp_card, height=130)
        bkp_scroll.pack(fill="x", padx=15, pady=6)

        def refresh_backups():
            for w in bkp_scroll.winfo_children():
                w.destroy()
            backups = get_backup_list()
            if not backups:
                ctk.CTkLabel(bkp_scroll, text="No existing backups.", text_color="gray").pack(pady=10)
                return
            for b in backups:
                row = ctk.CTkFrame(bkp_scroll, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=b["folder_name"], font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
                ctk.CTkLabel(row, text=f"{b['size_kb']} KB", font=ctk.CTkFont(size=11), text_color="#00ffcc").pack(side="right")

        refresh_backups()

        key_box = ctk.CTkFrame(bkp_card, fg_color="#2b0938", corner_radius=8)
        key_box.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(key_box, text="Master Admin Authorization Key", font=ctk.CTkFont(weight="bold"), text_color="#d8bbff").pack(pady=(6, 2))
        ctk.CTkLabel(key_box, text="Used during registration to grant Administrator privileges.", font=ctk.CTkFont(size=11), text_color="gray").pack(pady=2)

        def rotate_key_action():
            new_k = self.prompt_input("Rotate Master Key", "Enter new Master Admin Authorization Key (min 8 chars):", parent=admin_win, is_password=True)
            if not new_k:
                return
            ok, msg = update_admin_master_key(new_k, self.current_user)
            if ok:
                self.show_info("Success", msg, parent=admin_win)
            else:
                self.show_error("Error", msg, parent=admin_win)

        ctk.CTkButton(key_box, text="Rotate Master Key", command=rotate_key_action,
                      fg_color="#5a189a", hover_color="#7b2cbf", height=28).pack(pady=6)

        # -------------------------------------------------------------
        # ADMIN TAB 7: SYSTEM DIAGNOSTICS & MAINTENANCE
        # -------------------------------------------------------------
        tab_sys.grid_columnconfigure((0, 1), weight=1)

        diag_card = ctk.CTkFrame(tab_sys)
        diag_card.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(diag_card, text="Database & Storage Health", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        lbl_diag_text = ctk.CTkLabel(diag_card, text="", justify="left", font=ctk.CTkFont(size=13))
        lbl_diag_text.pack(padx=20, pady=10)

        def refresh_diag():
            stats = get_system_diagnostics()
            msg = (
                f"• Database File: {DB_PATH.name} ({stats['db_size_kb']} KB)\n\n"
                f"• Total Registered Students: {stats['students']}\n"
                f"• Total Registered Teachers: {stats['teachers']}\n"
                f"• Total Active Subjects: {stats['subjects']}\n"
                f"• Total Attendance Records: {stats['attendance_records']}\n\n"
                f"• AI Facial Embeddings: {stats['embeddings_count']} Loaded\n"
                f"• YOLOv8 Face Weights: {'✅ Present' if stats['yolo_weights'] else '❌ Missing'}\n"
                f"• FaceNet-512 Weights: {'✅ Present' if stats['facenet_weights'] else '❌ Missing'}"
            )
            lbl_diag_text.configure(text=msg)

        refresh_diag()

        # Maintenance Controls
        maint_card = ctk.CTkFrame(tab_sys)
        maint_card.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(maint_card, text="Administrative Operations", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        def clear_unknown_faces():
            count = 0
            if UNKNOWN_FACES_DIR.exists():
                for p in UNKNOWN_FACES_DIR.glob("*.*"):
                    try:
                        p.unlink()
                        count += 1
                    except:
                        pass
            self.show_info("Cleaned", f"Purged {count} unknown face snapshots.", parent=admin_win)

        def admin_retrain_all():
            admin_win.withdraw()
            self.train_model()
            admin_win.deiconify()
            refresh_diag()

        ctk.CTkButton(maint_card, text="Retrain AI Facial Recognition Brain", command=admin_retrain_all,
                      fg_color="#cc7000", hover_color="#e68a00", width=260, height=36).pack(pady=12)

        ctk.CTkButton(maint_card, text="Clear Unknown Face Snapshots", command=clear_unknown_faces,
                      fg_color="#3d5a80", hover_color="#293241", width=260, height=36).pack(pady=12)

        ctk.CTkButton(maint_card, text="Refresh Health Status", command=refresh_diag,
                      width=260, height=36).pack(pady=12)

    # BATCH SCAN FLOW: TEACHER PICKS ALLOTTED SUBJECT
    def start_live_attendance(self):
        if not self.require_login():
            return

        if self.current_user["role"] == "admin":
            subjects = get_all_subjects()
        else:
            subjects = get_subjects_by_teacher(self.current_user["id"])

        if not subjects:
            self.show_warning("No Subjects Allotted",
                              f"No subjects assigned to your profile ({self.current_user['name']})!\nPlease allot a subject in 'Teacher Profiles & Subjects' first.")
            self.open_teacher_profile_window()
            return

        scan_modal = ctk.CTkToplevel(self)
        scan_modal.title("Faculty Attendance Portal - Select Subject")
        scan_modal.geometry("580x570")
        scan_modal.transient(self)
        scan_modal.lift()
        scan_modal.focus_force()
        scan_modal.grab_set()
        self.active_modal = scan_modal

        def on_close():
            self.active_modal = None
            scan_modal.destroy()

        scan_modal.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(scan_modal, text="Teacher Attendance Portal", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(18, 3))
        ctk.CTkLabel(scan_modal, text=f"Authenticated: {self.current_user['name']} ({self.current_user['employee_id']})",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#00ffcc").pack(pady=(0, 10))

        subject_keys = []
        key_to_sub = {}
        for s in subjects:
            key = f"[{s['subject_code']}] {s['subject_name']} | {s['branch']}-Sec {s['section']}"
            subject_keys.append(key)
            key_to_sub[key] = s

        selected_sub_var = ctk.StringVar(value=subject_keys[0])

        info_card = ctk.CTkFrame(scan_modal, corner_radius=12)
        info_card.pack(fill="x", padx=30, pady=8)

        lbl_sub_title = ctk.CTkLabel(info_card, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00ffcc")
        lbl_sub_title.pack(pady=(10, 2))
        lbl_teacher = ctk.CTkLabel(info_card, text="", font=ctk.CTkFont(size=14))
        lbl_teacher.pack(pady=2)
        lbl_class = ctk.CTkLabel(info_card, text="", font=ctk.CTkFont(size=13), text_color="#00a8cc")
        lbl_class.pack(pady=2)
        lbl_enrolled = ctk.CTkLabel(info_card, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffcc00")
        lbl_enrolled.pack(pady=(2, 10))

        roster_preview_box = ctk.CTkScrollableFrame(scan_modal, height=130)
        roster_preview_box.pack(fill="x", padx=30, pady=5)

        def update_info_card(choice):
            sub = key_to_sub[choice]
            lbl_sub_title.configure(text=f"{sub['subject_code']} - {sub['subject_name']}")
            lbl_teacher.configure(text=f"Faculty: {sub['teacher_name']} (Emp ID: {sub.get('teacher_emp_id', 'N/A')})")
            lbl_class.configure(text=f"Allotted Class: {sub['degree']} {sub['year']} | {sub['branch']} - Section {sub['section']}")

            students = get_students_by_class(sub['degree'], sub['year'], sub['branch'], sub['section'])
            lbl_enrolled.configure(text=f"Auto-Enrolled Students in this Section: {len(students)}")

            for w in roster_preview_box.winfo_children():
                w.destroy()

            if not students:
                ctk.CTkLabel(roster_preview_box, text="No students registered yet in this section.", text_color="gray").pack(pady=15)
            else:
                for r, n, g, d, y, b, s in students:
                    row = ctk.CTkFrame(roster_preview_box, fg_color="transparent")
                    row.pack(fill="x", pady=1)
                    ctk.CTkLabel(row, text=f"• Roll {r}: {n}", font=ctk.CTkFont(size=12)).pack(side="left")
                    ctk.CTkLabel(row, text=f"{b}-{s}", font=ctk.CTkFont(size=11), text_color="#00ffcc").pack(side="right")

        ctk.CTkOptionMenu(scan_modal, variable=selected_sub_var, values=subject_keys, width=500,
                          command=update_info_card).pack(pady=8)

        update_info_card(subject_keys[0])

        def proceed_scan():
            chosen_sub = key_to_sub[selected_sub_var.get()]
            on_close()

            if hasattr(self, 'btn_attendance') and self.btn_attendance:
                self.btn_attendance.configure(
                    text=f"SCANNING: {chosen_sub['subject_code']}...",
                    state="disabled"
                )
            self.update()

            threading.Thread(
                target=self._run_camera_thread,
                args=(chosen_sub,),
                daemon=True
            ).start()
            self.after(5000, self.refresh_dashboard_metrics)

        ctk.CTkButton(scan_modal, text="START SECTION ATTENDANCE SCAN", command=proceed_scan,
                      height=48, font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color="#006400", hover_color="#008000").pack(pady=18)

    def _run_camera_thread(self, subject_info):
        from src.attendance_logic import start_attendance
        result = start_attendance(subject_info)
        self.after(0, lambda: self._camera_finished(result, subject_info))

    def _camera_finished(self, result, subject_info):
        if hasattr(self, 'btn_attendance') and self.btn_attendance:
            self.btn_attendance.configure(text="BATCH CLASS SCAN", state="normal")
        self.refresh_dashboard_metrics()

        if isinstance(result, dict) and "error" in result:
            self.show_error("Scan Error", result["error"])
        else:
            verified = result.get("verified", 0) if isinstance(result, dict) else 0
            rejected = result.get("rejected_section", 0) if isinstance(result, dict) else 0
            spoofs = result.get("spoofs_rejected", 0) if isinstance(result, dict) else 0
            enrolled = result.get("enrolled_total", 0) if isinstance(result, dict) else 0
            sub_code = subject_info.get("subject_code", "")
            sec = subject_info.get("section", "")
            br = subject_info.get("branch", "")
            teacher = subject_info.get("teacher_name", "")
            hmac_sig = result.get("hmac_signature")

            msg = (
                f"Batch Attendance Completed!\n\n"
                f"Subject: {sub_code} ({br} - Section {sec})\n"
                f"Faculty: {teacher}\n"
                f"Section Enrolled: {enrolled}\n\n"
                f"✅ Verified Present: {verified} students\n"
                f"❌ Wrong Section Discarded: {rejected} students\n"
            )
            if spoofs > 0:
                msg += f"🚨 Spoof Attacks Blocked: {spoofs} (Audit snapshots saved)\n"
            if hmac_sig:
                msg += f"🔏 HMAC Signature: {hmac_sig[:12]}... (Tamper-Proof)\n"
            msg += "\nAttendance sheet saved and Section Roster updated."
            self.show_info("Attendance Finished", msg)


if __name__ == "__main__":
    app = SmartClassApp()
    app.mainloop()