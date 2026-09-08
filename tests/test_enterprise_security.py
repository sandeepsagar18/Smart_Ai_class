import os
import sys
import shutil
import sqlite3
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure utf-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from src.database import (
    init_db, init_default_admin, authenticate_teacher, register_teacher_secure,
    verify_admin_master_key, update_admin_master_key, get_admin_master_key,
    unlock_teacher_account, generate_file_checksum, verify_file_integrity,
    get_security_audit_logs, create_database_backup, get_backup_list,
    delete_teacher_secure, DB_PATH
)
from src.anti_spoof import evaluate_liveness

def run_security_tests():
    print("=" * 60)
    print("   ENTERPRISE SECURITY & ANTI-SPOOFING TEST SUITE")
    print("=" * 60)

    init_db()
    init_default_admin()

    # -------------------------------------------------------------
    # 1. ADMIN MASTER AUTHORIZATION KEY
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Admin Master Authorization Key...")
    assert verify_admin_master_key("SmartClass@Admin#2026"), "Default Master Key verification failed"
    assert not verify_admin_master_key("InvalidKey123"), "Invalid Master Key should fail"
    print("  -> Master Key validation verified successfully.")

    # -------------------------------------------------------------
    # 2. BRUTE-FORCE PASSWORD ATTACK & AUTO-LOCKOUT
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Brute-Force Password Lockout Protection...")
    # Clean test user if exists
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM teachers WHERE employee_id = 'SEC_TEST_EMP'")
    conn.commit()
    conn.close()

    ok, msg, tid = register_teacher_secure("SEC_TEST_EMP", "Prof. Brute Test", "CSE", "brute@test.edu", "correct_pass123")
    assert ok, f"Registration failed: {msg}"

    # Attempt 4 wrong passwords (should warn remaining attempts)
    for i in range(1, 5):
        ok, msg, user = authenticate_teacher("SEC_TEST_EMP", "wrong_pass")
        assert not ok and "remaining" in msg, f"Expected warning on attempt {i}, got: {msg}"
        print(f"  -> Attempt {i}/5 failed as expected: {msg}")

    # 5th wrong password should trigger Account Lockout!
    ok, msg, user = authenticate_teacher("SEC_TEST_EMP", "wrong_pass")
    assert not ok and ("locked" in msg.lower() or "lockout" in msg.lower()), f"5th attempt should lock account, got: {msg}"
    print(f"  -> 5th Attempt triggered lockout: {msg}")

    # 6th attempt with CORRECT password must still be rejected while locked!
    ok, msg, user = authenticate_teacher("SEC_TEST_EMP", "correct_pass123")
    assert not ok and "locked" in msg.lower(), f"Locked account should block correct password until unlocked, got: {msg}"
    print("  -> Verified: Locked account blocks authentication even with correct password.")

    # Admin unlocks the account
    print("  -> Administrator unlocking account...")
    admin_login_ok, _, admin_user = authenticate_teacher("ADMIN01", "admin123")
    ok, unlock_msg = unlock_teacher_account(tid, admin_user)
    assert ok, f"Admin unlock failed: {unlock_msg}"
    print(f"  -> {unlock_msg}")

    # Now login with correct password succeeds!
    ok, msg, user = authenticate_teacher("SEC_TEST_EMP", "correct_pass123")
    assert ok, f"Login failed after unlock: {msg}"
    print("  -> User successfully logged in after Administrator unlock!")

    # -------------------------------------------------------------
    # 3. BIOMETRIC ANTI-SPOOFING & LIVENESS ASSESSMENT
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Biometric Anti-Spoofing & Liveness Engine...")
    # 3a. Flat image (simulating printed paper or blank screen)
    flat_crop = np.ones((100, 100, 3), dtype="uint8") * 200
    is_live, score, reason = evaluate_liveness(flat_crop)
    assert not is_live, f"Flat image should be flagged as spoof! Got live={is_live}, reason={reason}"
    print(f"  -> Flat image spoof test: Blocked=True (Score: {score}%, Reason: {reason})")

    # 3b. High-frequency digital screen moire pattern
    screen_moire = np.zeros((100, 100, 3), dtype="uint8")
    screen_moire[::2, ::2] = 255
    is_live, score, reason = evaluate_liveness(screen_moire)
    assert not is_live, f"Screen moire should be flagged as spoof! Got live={is_live}, reason={reason}"
    print(f"  -> Screen moiré spoof test: Blocked=True (Score: {score}%, Reason: {reason})")

    # -------------------------------------------------------------
    # 4. CRYPTOGRAPHIC HMAC ATTENDANCE FILE TAMPER DETECTION
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Cryptographic HMAC-SHA256 File Tamper Detection...")
    test_csv_path = Path(DB_PATH).parent / "attendance_records" / "Test_Attendance_Security.csv"
    test_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Create official attendance sheet
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write("Roll Number,Name,Status\n101,Alice,Present\n102,Bob,Present\n")

    # Sign the file
    f_hash, hmac_sig = generate_file_checksum(test_csv_path, created_by="ADMIN01")
    assert f_hash and hmac_sig, "HMAC signing failed"
    print(f"  -> Generated HMAC-SHA256 signature: {hmac_sig[:16]}...")

    # Verify authentic file
    is_valid, msg = verify_file_integrity(test_csv_path)
    assert is_valid, f"Authentic file verification failed: {msg}"
    print("  -> Authentic file verified: Signature matches 100%.")

    # TAMPER with the file (e.g. Rogue student edits CSV to add Charlie)
    print("  -> Simulating external file tampering (adding unauthorized student)...")
    with open(test_csv_path, "a", encoding="utf-8") as f:
        f.write("103,Charlie_Hacker,Present\n")

    # Verify tampered file
    is_valid, msg = verify_file_integrity(test_csv_path)
    assert not is_valid, "Tampered file should be caught!"
    print(f"  -> Tamper Alert successfully triggered:\n     {msg.splitlines()[0]}")

    # -------------------------------------------------------------
    # 5. DISASTER RECOVERY & 1-CLICK BACKUP
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing 1-Click Database Disaster Recovery Backup...")
    ok, backup_msg = create_database_backup()
    assert ok, f"Backup creation failed: {backup_msg}"
    print(f"  -> {backup_msg}")

    backups = get_backup_list()
    assert len(backups) > 0, "Backup list should not be empty"
    print(f"  -> Total backups in storage: {len(backups)} (Latest: {backups[0]['folder_name']})")

    # -------------------------------------------------------------
    # 6. SECURITY AUDIT TRAIL LOGGING
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Security Audit Trail...")
    logs = get_security_audit_logs(limit=50)
    assert len(logs) > 0, "Audit logs should contain recorded security events"
    event_types = {l["event_type"] for l in logs}
    print(f"  -> Verified logged events: {event_types}")

    # Cleanup test data
    if test_csv_path.exists():
        test_csv_path.unlink()
    delete_teacher_secure(tid, admin_user, "admin123")

    print("\n" + "=" * 60)
    print("   ALL ENTERPRISE SECURITY TESTS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_security_tests()
