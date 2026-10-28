"""
db.py  –  Database layer for College Management System
All table creation, migration helpers, and raw connection live here.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "college.db")

# --------------------------------------------------------------------------- #
#  Connection helper                                                           #
# --------------------------------------------------------------------------- #

def get_connection() -> sqlite3.Connection:
    """Return a thread-local connection with FK enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row          # access columns by name
    return conn


# --------------------------------------------------------------------------- #
#  Schema initialisation                                                       #
# --------------------------------------------------------------------------- #

SCHEMA_SQL = """
-- ================================================================
-- CORE TABLES
-- ================================================================

-- ----------------------------------------------------------------
-- USERS  (authentication — shared by all roles)
-- is_active = 1 (enabled) | 0 (disabled by admin → login blocked)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    salt          TEXT    NOT NULL,
    role          TEXT    NOT NULL
        CHECK(role IN ('admin','student','professor','lab_attendant')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------
-- STUDENTS  (IDs start at 101)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    age             INTEGER CHECK(age BETWEEN 14 AND 100),
    gender          TEXT    CHECK(gender IN ('M','F')),
    department      TEXT    NOT NULL,
    gpa             REAL    CHECK(gpa BETWEEN 0.0 AND 4.0),
    city            TEXT,
    phone           TEXT,
    enrollment_year INTEGER,
    profile_pic     BLOB
);

-- ----------------------------------------------------------------
-- PROFESSORS  (IDs start at 201)
-- profile_pic added so admins/professors can upload photos
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS professors (
    prof_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    first_name   TEXT    NOT NULL,
    last_name    TEXT    NOT NULL,
    age          INTEGER CHECK(age BETWEEN 22 AND 100),
    gender       TEXT    CHECK(gender IN ('M','F')),
    department   TEXT    NOT NULL,
    salary       REAL    CHECK(salary >= 0),
    city         TEXT,
    phone        TEXT,
    joining_year INTEGER,
    profile_pic  BLOB
);

-- ----------------------------------------------------------------
-- LAB ATTENDANTS  (IDs start at 301)
-- profile_pic added
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lab_attendants (
    lab_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    first_name   TEXT    NOT NULL,
    last_name    TEXT    NOT NULL,
    age          INTEGER CHECK(age BETWEEN 18 AND 100),
    gender       TEXT    CHECK(gender IN ('M','F')),
    lab_name     TEXT    NOT NULL,
    shift        TEXT    CHECK(shift IN ('Morning','Evening','Night')),
    city         TEXT,
    phone        TEXT,
    joining_year INTEGER,
    profile_pic  BLOB
);

-- ----------------------------------------------------------------
-- COURSES  (IDs start at 401)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    course_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name  TEXT    NOT NULL,
    credit_hours INTEGER CHECK(credit_hours BETWEEN 1 AND 6),
    semester     TEXT,
    department   TEXT,
    fee          REAL    CHECK(fee >= 0),
    room_no      TEXT,
    timing       TEXT,
    status       TEXT    DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
    year         INTEGER
);

-- ----------------------------------------------------------------
-- COURSE ASSIGNMENTS  (professor → course)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS course_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id     INTEGER NOT NULL REFERENCES courses(course_id)     ON DELETE CASCADE,
    prof_id       INTEGER NOT NULL REFERENCES professors(prof_id)    ON DELETE CASCADE,
    assigned_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(course_id, prof_id)
);

-- ----------------------------------------------------------------
-- ENROLLMENTS  (student → course)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    INTEGER NOT NULL REFERENCES students(student_id)   ON DELETE CASCADE,
    course_id     INTEGER NOT NULL REFERENCES courses(course_id)     ON DELETE CASCADE,
    enrolled_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    grade         TEXT,
    UNIQUE(student_id, course_id)
);

-- ----------------------------------------------------------------
-- LAB ASSIGNMENTS  (lab_attendant → lab duty)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lab_assignments (
    la_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    lab_id           INTEGER NOT NULL REFERENCES lab_attendants(lab_id) ON DELETE CASCADE,
    lab_name         TEXT    NOT NULL,
    responsibilities TEXT,
    assigned_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ================================================================
-- INDEXES  — speed up the most common WHERE / JOIN columns
-- ================================================================

-- login lookup by email (most-hit query)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

-- role-based filtering on the users table
CREATE INDEX IF NOT EXISTS idx_users_role
    ON users(role);

-- is_active filter (admin disables/enables users)
CREATE INDEX IF NOT EXISTS idx_users_active
    ON users(is_active);

-- FK join: students → users
CREATE INDEX IF NOT EXISTS idx_students_user_id
    ON students(user_id);

-- departmental queries on students
CREATE INDEX IF NOT EXISTS idx_students_department
    ON students(department);

-- GPA range queries / sorting
CREATE INDEX IF NOT EXISTS idx_students_gpa
    ON students(gpa);

-- FK join: professors → users
CREATE INDEX IF NOT EXISTS idx_professors_user_id
    ON professors(user_id);

-- departmental queries on professors
CREATE INDEX IF NOT EXISTS idx_professors_department
    ON professors(department);

-- FK join: lab_attendants → users
CREATE INDEX IF NOT EXISTS idx_lab_attendants_user_id
    ON lab_attendants(user_id);

-- enrollment lookups by student and by course
CREATE INDEX IF NOT EXISTS idx_enrollments_student
    ON enrollments(student_id);

CREATE INDEX IF NOT EXISTS idx_enrollments_course
    ON enrollments(course_id);

-- course assignment lookups by professor
CREATE INDEX IF NOT EXISTS idx_assignments_prof
    ON course_assignments(prof_id);

CREATE INDEX IF NOT EXISTS idx_assignments_course
    ON course_assignments(course_id);

-- lab duty lookups by attendant
CREATE INDEX IF NOT EXISTS idx_lab_assignments_lab
    ON lab_assignments(lab_id);

-- ================================================================
-- VIEWS  — pre-built read-only queries used throughout the app
-- ================================================================

-- Full student roster (excludes disabled accounts and BLOB column)
DROP VIEW IF EXISTS vw_students_active;
CREATE VIEW vw_students_active AS
    SELECT  s.student_id,
            s.first_name,
            s.last_name,
            s.age,
            s.gender,
            s.department,
            s.gpa,
            s.city,
            s.phone,
            s.enrollment_year,
            u.email,
            u.is_active
    FROM    students s
    JOIN    users    u ON u.user_id = s.user_id
    WHERE   u.is_active = 1;

-- Full professor roster (excludes disabled accounts and BLOB column)
DROP VIEW IF EXISTS vw_professors_active;
CREATE VIEW vw_professors_active AS
    SELECT  p.prof_id,
            p.first_name,
            p.last_name,
            p.age,
            p.gender,
            p.department,
            p.salary,
            p.city,
            p.phone,
            p.joining_year,
            u.email,
            u.is_active
    FROM    professors p
    JOIN    users      u ON u.user_id = p.user_id
    WHERE   u.is_active = 1;

-- Full lab-attendant roster (excludes disabled accounts and BLOB column)
DROP VIEW IF EXISTS vw_lab_attendants_active;
CREATE VIEW vw_lab_attendants_active AS
    SELECT  l.lab_id,
            l.first_name,
            l.last_name,
            l.age,
            l.gender,
            l.lab_name,
            l.shift,
            l.city,
            l.phone,
            l.joining_year,
            u.email,
            u.is_active
    FROM    lab_attendants l
    JOIN    users          u ON u.user_id = l.user_id
    WHERE   u.is_active = 1;

-- Enrollment detail view (student name + course name + teacher)
DROP VIEW IF EXISTS vw_enrollments_detail;
CREATE VIEW vw_enrollments_detail AS
    SELECT  e.enrollment_id,
            s.student_id,
            s.first_name || ' ' || s.last_name  AS student_name,
            s.department                         AS student_dept,
            c.course_id,
            c.course_name,
            c.credit_hours,
            c.semester,
            COALESCE(p.first_name || ' ' || p.last_name, '—') AS teacher,
            e.grade,
            e.enrolled_at
    FROM    enrollments     e
    JOIN    students        s  ON s.student_id = e.student_id
    JOIN    courses         c  ON c.course_id  = e.course_id
    LEFT JOIN course_assignments ca ON ca.course_id = c.course_id
    LEFT JOIN professors    p  ON p.prof_id    = ca.prof_id;

-- Course detail view (with assigned teacher name)
DROP VIEW IF EXISTS vw_courses_with_teacher;
CREATE VIEW vw_courses_with_teacher AS
    SELECT  c.course_id,
            c.course_name,
            c.credit_hours,
            c.semester,
            c.department,
            c.fee,
            c.room_no,
            c.timing,
            c.status,
            c.year,
            COALESCE(p.first_name || ' ' || p.last_name, 'Unassigned') AS teacher
    FROM    courses c
    LEFT JOIN course_assignments ca ON ca.course_id = c.course_id
    LEFT JOIN professors         p  ON p.prof_id    = ca.prof_id;

-- Summary statistics view
DROP VIEW IF EXISTS vw_summary_stats;
CREATE VIEW vw_summary_stats AS
    SELECT
        (SELECT COUNT(*) FROM students  s JOIN users u ON u.user_id=s.user_id WHERE u.is_active=1) AS active_students,
        (SELECT COUNT(*) FROM professors p JOIN users u ON u.user_id=p.user_id WHERE u.is_active=1) AS active_professors,
        (SELECT COUNT(*) FROM lab_attendants l JOIN users u ON u.user_id=l.user_id WHERE u.is_active=1) AS active_lab_attendants,
        (SELECT COUNT(*) FROM users WHERE is_active=0 AND role != 'admin')  AS disabled_users,
        (SELECT COUNT(*) FROM courses)                                       AS total_courses,
        (SELECT COUNT(*) FROM enrollments)                                   AS total_enrollments,
        (SELECT ROUND(AVG(gpa),2) FROM students)                            AS avg_gpa,
        (SELECT ROUND(AVG(salary),2) FROM professors)                       AS avg_salary;

-- ================================================================
-- TRIGGERS  — enforce business rules automatically
-- ================================================================

-- Prevent deleting the admin user account
DROP TRIGGER IF EXISTS trg_protect_admin_delete;
CREATE TRIGGER trg_protect_admin_delete
    BEFORE DELETE ON users
    WHEN OLD.role = 'admin'
BEGIN
    SELECT RAISE(ABORT, 'The admin account cannot be deleted.');
END;

-- When a student is deleted, automatically drop all their enrollments
-- (redundant with FK CASCADE but makes intent explicit in audit logs)
DROP TRIGGER IF EXISTS trg_student_delete_cleanup;
CREATE TRIGGER trg_student_delete_cleanup
    BEFORE DELETE ON students
BEGIN
    DELETE FROM enrollments WHERE student_id = OLD.student_id;
END;

-- When a professor is deleted, remove their course assignments
DROP TRIGGER IF EXISTS trg_professor_delete_cleanup;
CREATE TRIGGER trg_professor_delete_cleanup
    BEFORE DELETE ON professors
BEGIN
    DELETE FROM course_assignments WHERE prof_id = OLD.prof_id;
END;

-- Prevent enrolling a student into a full course (> 60 students)
DROP TRIGGER IF EXISTS trg_enrollment_capacity;
CREATE TRIGGER trg_enrollment_capacity
    BEFORE INSERT ON enrollments
BEGIN
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM enrollments WHERE course_id = NEW.course_id) >= 60
        THEN RAISE(ABORT, 'Course is full (maximum 60 students).')
    END;
END;

-- Auto-set enrolled_at timestamp on new enrollment
DROP TRIGGER IF EXISTS trg_enrollment_timestamp;
CREATE TRIGGER trg_enrollment_timestamp
    AFTER INSERT ON enrollments
BEGIN
    UPDATE enrollments
    SET    enrolled_at = datetime('now')
    WHERE  enrollment_id = NEW.enrollment_id
      AND  NEW.enrolled_at IS NULL;
END;

-- Prevent GPA being set outside 0.0–4.0 via UPDATE (CHECK only fires on INSERT in some SQLite builds)
DROP TRIGGER IF EXISTS trg_student_gpa_check;
CREATE TRIGGER trg_student_gpa_check
    BEFORE UPDATE OF gpa ON students
BEGIN
    SELECT CASE
        WHEN NEW.gpa < 0.0 OR NEW.gpa > 4.0
        THEN RAISE(ABORT, 'GPA must be between 0.0 and 4.0.')
    END;
END;

-- Prevent salary going negative via UPDATE
DROP TRIGGER IF EXISTS trg_professor_salary_check;
CREATE TRIGGER trg_professor_salary_check
    BEFORE UPDATE OF salary ON professors
BEGIN
    SELECT CASE
        WHEN NEW.salary < 0
        THEN RAISE(ABORT, 'Salary cannot be negative.')
    END;
END;
"""

# --------------------------------------------------------------------------- #
#  Auto-increment starting seeds                                               #
#  SQLite uses the sqlite_sequence table to track AUTOINCREMENT counters.      #
#  Inserting a row with seq = (start - 1) makes the NEXT insert use `start`.  #
# --------------------------------------------------------------------------- #
ID_SEEDS = {
    # table_name : first id that will be assigned
    "students":      101,
    "professors":    201,
    "lab_attendants": 301,
    "courses":       401,
}


def _apply_id_seeds(cur):
    """
    Set the AUTOINCREMENT counters so IDs begin at the configured seeds.
    Only runs when a table has zero rows (fresh DB).
    Safe to call on every startup — skips tables that already have data.
    """
    for table, start in ID_SEEDS.items():
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0:
            # sqlite_sequence is created by the first AUTOINCREMENT table
            cur.execute(
                "INSERT OR IGNORE INTO sqlite_sequence(name, seq) VALUES(?, ?)",
                (table, start - 1)
            )
            cur.execute(
                "UPDATE sqlite_sequence SET seq=? WHERE name=? AND seq < ?",
                (start - 1, table, start - 1)
            )


def _migrate_existing_db(cur):
    """
    Safely add new columns to an existing database without dropping data.
    ALTER TABLE ADD COLUMN is idempotent — it does nothing if the column exists.
    """
    migrations = [
        # (table, column, definition)
        ("users",          "is_active",   "INTEGER NOT NULL DEFAULT 1"),
        ("professors",     "profile_pic", "BLOB"),
        ("lab_attendants", "profile_pic", "BLOB"),
    ]
    for table, col, defn in migrations:
        existing = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        if not existing:
            # Fresh databases have no tables to migrate until schema creation.
            continue
        if col not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")


def init_db():
    """
    Create all tables/indexes/views/triggers, migrate existing columns,
    seed the default admin, and insert sample data on first run.
    """
    conn = get_connection()
    cur  = conn.cursor()

    # Upgrade older databases before creating views/indexes that depend on
    # newer columns such as users.is_active.
    _migrate_existing_db(cur)

    # Create tables (IF NOT EXISTS — safe on existing DB)
    cur.executescript(SCHEMA_SQL)

    # Re-run migrations after schema creation so fresh databases also pick up
    # any additive changes in a single startup pass.
    _migrate_existing_db(cur)

    # Apply auto-increment starting values (no-op if rows already exist)
    _apply_id_seeds(cur)

    # Seed default admin: admin@college.edu / Admin@1234
    from auth import hash_password
    if not cur.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        pw_hash, salt = hash_password("Admin@1234")
        cur.execute(
            "INSERT INTO users(email, password_hash, salt, role, is_active) VALUES(?,?,?,?,1)",
            ("admin@college.edu", pw_hash, salt, "admin"),
        )

    conn.commit()

    # Populate sample rows only when tables are empty
    _seed_sample_data(conn)

    conn.close()


# --------------------------------------------------------------------------- #
#  Sample data (12–15 rows per table)                                          #
# --------------------------------------------------------------------------- #

def _seed_sample_data(conn):
    """
    Populate every table with realistic sample rows the first time the
    app runs.  Each call is a no-op when rows already exist.
    """
    from auth import hash_password
    cur = conn.cursor()

    # ── helpers ──────────────────────────────────────────────────────────── #

    def _user(email, role):
        """Insert a system user and return its user_id (idempotent)."""
        existing = cur.execute(
            "SELECT user_id FROM users WHERE email=?", (email,)
        ).fetchone()
        if existing:
            return existing[0]
        ph, salt = hash_password("Sample@1234")
        cur.execute(
            "INSERT INTO users(email,password_hash,salt,role) VALUES(?,?,?,?)",
            (email, ph, salt, role)
        )
        return cur.lastrowid

    # ── 1. STUDENTS (12 rows → IDs 101–112) ──────────────────────────────── #
    if cur.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        students = [
            # (first, last, age, gender, dept,     gpa,  city,        phone,          year)
            ("Ali",      "Ahmed",    20, "M", "CS",      3.8, "Lahore",    "0300-1234567", 2022),
            ("Sara",     "Khan",     21, "F", "EE",      3.5, "Karachi",   "0311-2345678", 2021),
            ("Usman",    "Malik",    19, "M", "ME",      3.2, "Islamabad", "0333-3456789", 2023),
            ("Ayesha",   "Siddiqui", 22, "F", "CS",      3.9, "Lahore",    "0321-4567890", 2020),
            ("Bilal",    "Hassan",   20, "M", "BBA",     3.1, "Peshawar",  "0345-5678901", 2022),
            ("Fatima",   "Rehman",   21, "F", "Physics", 3.6, "Multan",    "0301-6789012", 2021),
            ("Hamza",    "Javed",    19, "M", "Math",    3.4, "Faisalabad","0312-7890123", 2023),
            ("Maryam",   "Butt",     20, "F", "CE",      3.7, "Rawalpindi","0322-8901234", 2022),
            ("Zain",     "Sheikh",   22, "M", "CS",      2.9, "Hyderabad", "0346-9012345", 2020),
            ("Noor",     "Akhtar",   21, "F", "EE",      3.3, "Quetta",    "0302-0123456", 2021),
            ("Talha",    "Chaudhry", 20, "M", "BBA",     3.0, "Sialkot",   "0313-1234560", 2022),
            ("Zara",     "Qureshi",  19, "F", "ME",      3.8, "Gujranwala","0323-2345671", 2023),
        ]
        for i, (fn, ln, age, gd, dept, gpa, city, ph, yr) in enumerate(students):
            email = f"student{101+i}@college.edu"
            uid   = _user(email, "student")
            cur.execute(
                """INSERT INTO students
                   (user_id,first_name,last_name,age,gender,department,gpa,city,phone,enrollment_year)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (uid, fn, ln, age, gd, dept, gpa, city, ph, yr)
            )

    # ── 2. PROFESSORS (12 rows → IDs 201–212) ────────────────────────────── #
    if cur.execute("SELECT COUNT(*) FROM professors").fetchone()[0] == 0:
        professors = [
            # (first,      last,        age, gd, dept,     salary,   city,        phone,          year)
            ("Dr. Imran",  "Yousaf",    45, "M", "CS",      85000, "Lahore",    "0300-9876543", 2005),
            ("Dr. Hina",   "Baig",      38, "F", "EE",      78000, "Karachi",   "0311-8765432", 2010),
            ("Prof. Asad", "Riaz",      50, "M", "ME",      92000, "Islamabad", "0333-7654321", 2000),
            ("Dr. Amna",   "Farooq",    42, "F", "CS",      80000, "Lahore",    "0321-6543210", 2008),
            ("Prof. Raza", "Gillani",   55, "M", "BBA",     95000, "Peshawar",  "0345-5432109", 1998),
            ("Dr. Sana",   "Naqvi",     36, "F", "Physics", 72000, "Multan",    "0301-4321098", 2014),
            ("Dr. Tariq",  "Mehmood",   48, "M", "Math",    83000, "Faisalabad","0312-3210987", 2003),
            ("Dr. Lubna",  "Ansari",    40, "F", "CE",      77000, "Rawalpindi","0322-2109876", 2011),
            ("Prof. Adil", "Waheed",    52, "M", "CS",      98000, "Lahore",    "0346-1098765", 2001),
            ("Dr. Rabia",  "Hashmi",    37, "F", "EE",      74000, "Sialkot",   "0302-0987654", 2013),
            ("Prof. Nasir","Gondal",    60, "M", "BBA",    105000, "Gujranwala","0313-9876543", 1995),
            ("Dr. Saima",  "Mirza",     41, "F", "ME",      79000, "Quetta",    "0323-8765432", 2009),
        ]
        for i, (fn, ln, age, gd, dept, sal, city, ph, yr) in enumerate(professors):
            email = f"prof{201+i}@college.edu"
            uid   = _user(email, "professor")
            cur.execute(
                """INSERT INTO professors
                   (user_id,first_name,last_name,age,gender,department,salary,city,phone,joining_year)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (uid, fn, ln, age, gd, dept, sal, city, ph, yr)
            )

    # ── 3. LAB ATTENDANTS (12 rows → IDs 301–312) ────────────────────────── #
    if cur.execute("SELECT COUNT(*) FROM lab_attendants").fetchone()[0] == 0:
        labs = [
            # (first,    last,      age, gd, lab_name,           shift,     city,        phone,          year)
            ("Kamran",  "Iqbal",    28, "M", "CS Lab",           "Morning", "Lahore",    "0300-1111111", 2018),
            ("Sobia",   "Nawaz",    25, "F", "Physics Lab",      "Evening", "Karachi",   "0311-2222222", 2020),
            ("Irfan",   "Rashid",   30, "M", "Chemistry Lab",    "Night",   "Islamabad", "0333-3333333", 2016),
            ("Huma",    "Aziz",     27, "F", "Bio Lab",          "Morning", "Multan",    "0321-4444444", 2019),
            ("Waqas",   "Shabbir",  32, "M", "Electronics Lab",  "Evening", "Peshawar",  "0345-5555555", 2015),
            ("Asma",    "Rauf",     24, "F", "CS Lab",           "Night",   "Faisalabad","0301-6666666", 2021),
            ("Naeem",   "Durrani",  29, "M", "Physics Lab",      "Morning", "Rawalpindi","0312-7777777", 2017),
            ("Uzma",    "Pervez",   26, "F", "Chemistry Lab",    "Evening", "Lahore",    "0322-8888888", 2020),
            ("Shahid",  "Latif",    31, "M", "Bio Lab",          "Night",   "Hyderabad", "0346-9999999", 2015),
            ("Nadia",   "Zafar",    23, "F", "Electronics Lab",  "Morning", "Quetta",    "0302-0000001", 2022),
            ("Faisal",  "Sohail",   33, "M", "CS Lab",           "Evening", "Sialkot",   "0313-0000002", 2014),
            ("Raheela", "Chaudhry", 27, "F", "Physics Lab",      "Night",   "Gujranwala","0323-0000003", 2019),
        ]
        for i, (fn, ln, age, gd, lab, shift, city, ph, yr) in enumerate(labs):
            email = f"lab{301+i}@college.edu"
            uid   = _user(email, "lab_attendant")
            cur.execute(
                """INSERT INTO lab_attendants
                   (user_id,first_name,last_name,age,gender,lab_name,shift,city,phone,joining_year)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (uid, fn, ln, age, gd, lab, shift, city, ph, yr)
            )

    # ── 4. COURSES (15 rows → IDs 401–415) ───────────────────────────────── #
    if cur.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        courses = [
            # (name,                        cr, semester, dept,     fee,    room,  timing,           status, year)
            ("Introduction to Programming",  3, "Fall",   "CS",     15000, "A-101","08:00–09:30", "Active", 2024),
            ("Data Structures",              3, "Spring", "CS",     15000, "A-102","09:30–11:00", "Active", 2024),
            ("Circuit Theory",               4, "Fall",   "EE",     18000, "B-201","11:00–12:30", "Active", 2024),
            ("Signals & Systems",            3, "Spring", "EE",     17000, "B-202","08:00–09:30", "Active", 2024),
            ("Thermodynamics",               4, "Fall",   "ME",     19000, "C-301","12:30–14:00", "Active", 2024),
            ("Fluid Mechanics",              3, "Spring", "ME",     18500, "C-302","14:00–15:30", "Active", 2024),
            ("Principles of Management",     3, "Fall",   "BBA",    14000, "D-401","09:30–11:00", "Active", 2024),
            ("Financial Accounting",         3, "Spring", "BBA",    14500, "D-402","11:00–12:30", "Active", 2024),
            ("Classical Mechanics",          4, "Fall",   "Physics",20000, "E-501","08:00–09:30", "Active", 2024),
            ("Quantum Physics",              3, "Spring", "Physics",20000, "E-502","09:30–11:00", "Active", 2024),
            ("Calculus I",                   4, "Fall",   "Math",   12000, "F-601","12:30–14:00", "Active", 2024),
            ("Linear Algebra",               3, "Spring", "Math",   12500, "F-602","14:00–15:30", "Active", 2024),
            ("Structural Analysis",          4, "Fall",   "CE",     19500, "G-701","08:00–09:30", "Active", 2024),
            ("Software Engineering",         3, "Spring", "CS",     16000, "A-103","09:30–11:00", "Active", 2024),
            ("Database Systems",             3, "Fall",   "CS",     16000, "A-104","11:00–12:30", "Active", 2024),
        ]
        for (cn, cr, sem, dept, fee, room, timing, status, yr) in courses:
            cur.execute(
                """INSERT INTO courses(course_name,credit_hours,semester,department,fee,room_no,timing,status,year)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (cn, cr, sem, dept, fee, room, timing, status, yr)
            )

    conn.commit()

    # ── 5. COURSE ASSIGNMENTS (assign profs to courses) ───────────────────── #
    if cur.execute("SELECT COUNT(*) FROM course_assignments").fetchone()[0] == 0:
        # Get actual IDs from the DB (they may differ if data already existed)
        prof_ids   = [r[0] for r in cur.execute("SELECT prof_id   FROM professors    ORDER BY prof_id   LIMIT 12").fetchall()]
        course_ids = [r[0] for r in cur.execute("SELECT course_id FROM courses       ORDER BY course_id LIMIT 15").fetchall()]

        # Assign each professor to 1-2 courses
        assignments = [
            (course_ids[0],  prof_ids[0]),   # Intro to Prog  → Dr. Imran
            (course_ids[1],  prof_ids[3]),   # Data Structures→ Dr. Amna
            (course_ids[2],  prof_ids[1]),   # Circuit Theory → Dr. Hina
            (course_ids[3],  prof_ids[9]),   # Signals        → Dr. Rabia
            (course_ids[4],  prof_ids[2]),   # Thermodynamics → Prof. Asad
            (course_ids[5],  prof_ids[11]),  # Fluid Mech     → Dr. Saima
            (course_ids[6],  prof_ids[4]),   # Mgt            → Prof. Raza
            (course_ids[7],  prof_ids[10]),  # Fin. Acct      → Prof. Nasir
            (course_ids[8],  prof_ids[5]),   # Classical Mech → Dr. Sana
            (course_ids[9],  prof_ids[5]),   # Quantum Physics→ Dr. Sana
            (course_ids[10], prof_ids[6]),   # Calculus I     → Dr. Tariq
            (course_ids[11], prof_ids[6]),   # Linear Algebra → Dr. Tariq
            (course_ids[12], prof_ids[7]),   # Struct Analysis→ Dr. Lubna
            (course_ids[13], prof_ids[0]),   # Software Eng   → Dr. Imran
            (course_ids[14], prof_ids[8]),   # Database Sys   → Prof. Adil
        ]
        for cid, pid in assignments:
            cur.execute(
                "INSERT OR IGNORE INTO course_assignments(course_id,prof_id) VALUES(?,?)",
                (cid, pid)
            )
        conn.commit()

    # ── 6. ENROLLMENTS (each student enrolled in 2–3 courses) ─────────────── #
    if cur.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0] == 0:
        stu_ids    = [r[0] for r in cur.execute("SELECT student_id FROM students ORDER BY student_id LIMIT 12").fetchall()]
        course_ids = [r[0] for r in cur.execute("SELECT course_id  FROM courses  ORDER BY course_id  LIMIT 15").fetchall()]
        grades     = ["A+","A","A-","B+","B","B-","C+","C","—"]

        import itertools
        enroll_pairs = [
            (stu_ids[0],  course_ids[0],  "A"),
            (stu_ids[0],  course_ids[1],  "A+"),
            (stu_ids[0],  course_ids[13], "B+"),
            (stu_ids[1],  course_ids[2],  "B+"),
            (stu_ids[1],  course_ids[3],  "A-"),
            (stu_ids[2],  course_ids[4],  "B"),
            (stu_ids[2],  course_ids[5],  "B+"),
            (stu_ids[3],  course_ids[0],  "A+"),
            (stu_ids[3],  course_ids[14], "A"),
            (stu_ids[3],  course_ids[1],  "A+"),
            (stu_ids[4],  course_ids[6],  "B-"),
            (stu_ids[4],  course_ids[7],  "C+"),
            (stu_ids[5],  course_ids[8],  "A-"),
            (stu_ids[5],  course_ids[9],  "B+"),
            (stu_ids[6],  course_ids[10], "A"),
            (stu_ids[6],  course_ids[11], "A-"),
            (stu_ids[7],  course_ids[12], "B"),
            (stu_ids[7],  course_ids[4],  "B+"),
            (stu_ids[8],  course_ids[0],  "C+"),
            (stu_ids[8],  course_ids[13], "C"),
            (stu_ids[9],  course_ids[2],  "B"),
            (stu_ids[9],  course_ids[3],  "B-"),
            (stu_ids[10], course_ids[6],  "C+"),
            (stu_ids[10], course_ids[7],  "B-"),
            (stu_ids[11], course_ids[5],  "A"),
            (stu_ids[11], course_ids[4],  "A-"),
        ]
        for sid, cid, grade in enroll_pairs:
            cur.execute(
                "INSERT OR IGNORE INTO enrollments(student_id,course_id,grade) VALUES(?,?,?)",
                (sid, cid, grade)
            )
        conn.commit()

    # ── 7. LAB ASSIGNMENTS (2 per attendant) ─────────────────────────────── #
    if cur.execute("SELECT COUNT(*) FROM lab_assignments").fetchone()[0] == 0:
        lab_ids = [r[0] for r in cur.execute(
            "SELECT lab_id FROM lab_attendants ORDER BY lab_id LIMIT 12").fetchall()]

        lab_duties = [
            (lab_ids[0],  "CS Lab",          "Equipment setup and maintenance"),
            (lab_ids[0],  "CS Lab",          "Student supervision during practicals"),
            (lab_ids[1],  "Physics Lab",     "Instrument calibration"),
            (lab_ids[1],  "Physics Lab",     "Lab report filing"),
            (lab_ids[2],  "Chemistry Lab",   "Chemical storage management"),
            (lab_ids[2],  "Chemistry Lab",   "Safety compliance checks"),
            (lab_ids[3],  "Bio Lab",         "Microscope maintenance"),
            (lab_ids[3],  "Bio Lab",         "Specimen preparation"),
            (lab_ids[4],  "Electronics Lab", "Component inventory tracking"),
            (lab_ids[4],  "Electronics Lab", "Oscilloscope calibration"),
            (lab_ids[5],  "CS Lab",          "Network equipment setup"),
            (lab_ids[5],  "CS Lab",          "Software installation support"),
            (lab_ids[6],  "Physics Lab",     "Experiment preparation"),
            (lab_ids[7],  "Chemistry Lab",   "Reagent preparation"),
            (lab_ids[8],  "Bio Lab",         "Culture media preparation"),
            (lab_ids[9],  "Electronics Lab", "PCB testing support"),
            (lab_ids[10], "CS Lab",          "Server room monitoring"),
            (lab_ids[11], "Physics Lab",     "Optics lab setup"),
        ]
        for lid, lname, resp in lab_duties:
            cur.execute(
                "INSERT INTO lab_assignments(lab_id,lab_name,responsibilities) VALUES(?,?,?)",
                (lid, lname, resp)
            )
        conn.commit()
