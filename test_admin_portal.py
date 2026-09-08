import sqlite3
from pathlib import Path
from src.database import (
    init_db, init_default_admin, authenticate_teacher, register_teacher_secure,
    verify_teacher_password, change_teacher_password, get_all_teachers,
    delete_teacher_secure, add_subject, get_subjects_by_teacher,
    get_all_subjects, delete_subject_secure, get_students_by_class,
    get_all_students_master, update_student_details, admin_reset_teacher_password,
    update_teacher_role, reassign_subject_teacher, get_system_diagnostics,
    get_attendance_audit_logs, delete_attendance_log, save_attendance_entry
)

def run_tests():
    print("[TEST] 1. Initializing DB and default Admin...")
    init_db()
    init_default_admin()

    from src.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM teachers WHERE employee_id = 'TEST_FAC01'")
    conn.execute("DELETE FROM students WHERE roll_number = 'TEST_ROLL_99'")
    conn.execute("DELETE FROM subjects WHERE subject_code = 'CS501'")
    conn.commit()
    conn.close()

    # 1. Admin login test
    ok, msg, admin_user = authenticate_teacher("ADMIN01", "admin123")
    assert ok and admin_user["role"] == "admin", f"Failed admin login: {msg}"
    print(f"  -> Default Admin logged in: {admin_user['name']} [{admin_user['role']}]")

    # 2. Register test teacher
    print("[TEST] 2. Registering test teacher...")
    ok, msg, tid = register_teacher_secure("TEST_FAC01", "Dr. Test Faculty", "CSE", "test@cse.edu", "pass123")
    print(f"  -> Register teacher result: {ok}, {msg}")

    # 3. Promote teacher to admin
    print("[TEST] 3. Promoting test teacher to Admin...")
    teachers = get_all_teachers()
    test_teacher = next((t for t in teachers if t["employee_id"] == "TEST_FAC01"), None)
    assert test_teacher is not None, "Test teacher not found"
    ok, msg = update_teacher_role(test_teacher["id"], "admin")
    assert ok, f"Failed to promote: {msg}"
    print(f"  -> Role updated: {msg}")

    # 4. Admin reset password
    print("[TEST] 4. Admin resetting password for test teacher...")
    ok, msg = admin_reset_teacher_password(test_teacher["id"], "newpass456")
    assert ok, f"Failed reset: {msg}"
    ok, _, _ = authenticate_teacher("TEST_FAC01", "newpass456")
    assert ok, "New password authentication failed"
    print("  -> Password reset and re-authentication verified.")

    # 5. Add subject for test teacher
    print("[TEST] 5. Adding subject for test teacher...")
    ok, msg, sub_id = add_subject(test_teacher["id"], "CS501", "Distributed Systems", "BTECH", "3rd Year", "CSE", "A")
    print(f"  -> Subject added: id={sub_id}")

    # 6. Reassign subject to admin
    print("[TEST] 6. Reassigning subject to ADMIN01...")
    reassign_subject_teacher(sub_id, admin_user["id"])
    all_subs = get_all_subjects()
    reassigned = next((s for s in all_subs if s["id"] == sub_id), None)
    assert reassigned and reassigned["teacher_id"] == admin_user["id"], "Subject reassignment failed"
    print(f"  -> Reassigned to: {reassigned['teacher_name']}")

    # 7. Student registration and transfer
    print("[TEST] 7. Registering dummy student & transferring sections...")
    from src.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO students (roll_number, name, gender, degree, year, branch, section) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("TEST_ROLL_99", "Student Ninety-Nine", "Male", "BTECH", "3rd Year", "CSE", "A"))
    conn.commit()
    conn.close()

    # Transfer student to Section B
    ok = update_student_details("TEST_ROLL_99", "Student Ninety-Nine", "Male", "BTECH", "3rd Year", "CSE", "B")
    assert ok, "Failed to transfer student"
    students_in_b = get_students_by_class("BTECH", "3rd Year", "CSE", "B")
    assert any(s[0] == "TEST_ROLL_99" for s in students_in_b), "Transferred student not in Section B roster"
    print("  -> Student successfully transferred from Section A to Section B.")

    # 8. Record attendance and test audit logs
    print("[TEST] 8. Recording attendance and verifying audit logs...")
    save_attendance_entry(sub_id, "CS501", "Distributed Systems", admin_user["name"], "TEST_ROLL_99", "Student Ninety-Nine", "CSE", "B", "2026-09-08", "16:00:00")
    logs = get_attendance_audit_logs(10)
    assert any(l["roll_number"] == "TEST_ROLL_99" for l in logs), "Audit log missing entry"
    print(f"  -> Audit log successfully retrieved {len(logs)} records.")

    # 9. System Diagnostics
    print("[TEST] 9. Running System Diagnostics...")
    diag = get_system_diagnostics()
    assert diag["students"] >= 1
    assert diag["teachers"] >= 2
    assert diag["subjects"] >= 1
    assert diag["attendance_records"] >= 1
    print(f"  -> Diagnostics verified: {diag}")

    # 10. Clean up test data
    print("[TEST] 10. Cleaning up test data...")
    # Delete student
    from src.database import delete_student_secure
    ok, msg = delete_student_secure("TEST_ROLL_99", admin_user, "admin123")
    assert ok, f"Failed student deletion: {msg}"
    # Delete subject
    ok, msg = delete_subject_secure(sub_id, admin_user, "admin123")
    assert ok, f"Failed subject deletion: {msg}"
    # Delete test teacher
    ok, msg = delete_teacher_secure(test_teacher["id"], admin_user, "admin123")
    assert ok, f"Failed teacher deletion: {msg}"

    print("\n[SUCCESS] ALL ADMIN PORTAL DATABASE & BUSINESS LOGIC TESTS PASSED 100%!")

if __name__ == "__main__":
    run_tests()
