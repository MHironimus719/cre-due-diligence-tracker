import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

DATABASE_NAME = "dd_tracker.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the database with schema and pre-populated data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create the main DD items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dd_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not Started',
                responsible_party TEXT,
                due_date TEXT,
                notes TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create property info table for storing property name
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS property_info (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                property_name TEXT NOT NULL DEFAULT 'Property Name',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Check if we need to populate initial data
        cursor.execute('SELECT COUNT(*) as count FROM dd_items')
        if cursor.fetchone()['count'] == 0:
            # Pre-populate with standard DD checklist items
            default_items = get_default_dd_items()
            cursor.executemany('''
                INSERT INTO dd_items (category, item_name, status, responsible_party, due_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', default_items)

        # Initialize property info if not exists
        cursor.execute('SELECT COUNT(*) as count FROM property_info')
        if cursor.fetchone()['count'] == 0:
            cursor.execute('INSERT INTO property_info (id, property_name) VALUES (1, "Property Name")')

        conn.commit()

def get_default_dd_items():
    """Return a list of default DD items with realistic names"""
    base_date = datetime.now()

    items = [
        # Title & Survey (4 items)
        ("Title & Survey", "Title Commitment Review", "Not Started", "",
         (base_date + timedelta(days=7)).strftime("%Y-%m-%d"), "Review title commitment for exceptions and encumbrances"),
        ("Title & Survey", "ALTA Survey", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Obtain current ALTA/NSPS Land Title Survey"),
        ("Title & Survey", "Zoning Report", "Not Started", "",
         (base_date + timedelta(days=10)).strftime("%Y-%m-%d"), "Third-party zoning compliance report"),
        ("Title & Survey", "Title Policy Review", "Not Started", "",
         (base_date + timedelta(days=30)).strftime("%Y-%m-%d"), "Review proposed title policy and endorsements"),

        # Environmental (5 items)
        ("Environmental", "Phase I ESA", "Not Started", "",
         (base_date + timedelta(days=21)).strftime("%Y-%m-%d"), "Environmental Site Assessment per ASTM E1527-21"),
        ("Environmental", "Phase II ESA (if needed)", "Not Started", "",
         (base_date + timedelta(days=35)).strftime("%Y-%m-%d"), "Soil and groundwater testing if Phase I identifies concerns"),
        ("Environmental", "Asbestos Survey", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Building materials testing for ACM"),
        ("Environmental", "Environmental Compliance Review", "Not Started", "",
         (base_date + timedelta(days=15)).strftime("%Y-%m-%d"), "Review permits, violations, and remediation status"),
        ("Environmental", "Wetlands Delineation", "Not Started", "",
         (base_date + timedelta(days=20)).strftime("%Y-%m-%d"), "If applicable based on property location"),

        # Zoning (3 items)
        ("Zoning", "Zoning Compliance Verification", "Not Started", "",
         (base_date + timedelta(days=10)).strftime("%Y-%m-%d"), "Verify current use is legally conforming"),
        ("Zoning", "Certificate of Occupancy", "Not Started", "",
         (base_date + timedelta(days=7)).strftime("%Y-%m-%d"), "Obtain and review current CO"),
        ("Zoning", "Parking Requirement Analysis", "Not Started", "",
         (base_date + timedelta(days=10)).strftime("%Y-%m-%d"), "Verify compliance with parking code requirements"),

        # Financial (4 items)
        ("Financial", "Rent Roll Verification", "Not Started", "",
         (base_date + timedelta(days=5)).strftime("%Y-%m-%d"), "Verify current rent roll against leases"),
        ("Financial", "Operating Statements (3 years)", "Not Started", "",
         (base_date + timedelta(days=7)).strftime("%Y-%m-%d"), "Review historical income and expense statements"),
        ("Financial", "Tax Bill Review", "Not Started", "",
         (base_date + timedelta(days=10)).strftime("%Y-%m-%d"), "Review current and historical property tax bills"),
        ("Financial", "Utility Bills Analysis", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Review 12 months of utility bills"),

        # Lease Review (3 items)
        ("Lease Review", "Estoppel Certificates", "Not Started", "",
         (base_date + timedelta(days=21)).strftime("%Y-%m-%d"), "Obtain from all tenants representing >80% of NRA"),
        ("Lease Review", "Lease Abstraction", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Abstract all leases with key terms"),
        ("Lease Review", "SNDA Agreements", "Not Started", "",
         (base_date + timedelta(days=25)).strftime("%Y-%m-%d"), "Review subordination, non-disturbance agreements"),

        # Physical/Engineering (4 items)
        ("Physical/Engineering", "Property Condition Assessment", "Not Started", "",
         (base_date + timedelta(days=21)).strftime("%Y-%m-%d"), "ASTM E2018 PCA by qualified engineer"),
        ("Physical/Engineering", "Roof Inspection", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Detailed roof condition assessment"),
        ("Physical/Engineering", "HVAC Systems Review", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Review age, condition, and maintenance records"),
        ("Physical/Engineering", "ADA Compliance Survey", "Not Started", "",
         (base_date + timedelta(days=18)).strftime("%Y-%m-%d"), "Accessibility compliance assessment"),

        # Legal (3 items)
        ("Legal", "Purchase Agreement Review", "Not Started", "",
         (base_date + timedelta(days=3)).strftime("%Y-%m-%d"), "Legal review of PSA terms and conditions"),
        ("Legal", "Entity Formation", "Not Started", "",
         (base_date + timedelta(days=20)).strftime("%Y-%m-%d"), "Form acquisition entity (LLC/LP)"),
        ("Legal", "Service Contracts Review", "Not Started", "",
         (base_date + timedelta(days=14)).strftime("%Y-%m-%d"), "Review all property management and service contracts"),

        # Insurance (2 items)
        ("Insurance", "Insurance Quote", "Not Started", "",
         (base_date + timedelta(days=21)).strftime("%Y-%m-%d"), "Obtain property and liability insurance quotes"),
        ("Insurance", "Loss Runs Review", "Not Started", "",
         (base_date + timedelta(days=10)).strftime("%Y-%m-%d"), "Review 5-year property loss history"),
    ]

    return items

def get_all_items():
    """Retrieve all DD items from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dd_items
            ORDER BY category, item_name
        ''')
        return cursor.fetchall()

def get_items_by_filters(category=None, status=None):
    """Get items filtered by category and/or status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM dd_items WHERE 1=1'
        params = []

        if category and category != "All":
            query += ' AND category = ?'
            params.append(category)

        if status and status != "All":
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY category, item_name'
        cursor.execute(query, params)
        return cursor.fetchall()

def get_summary_by_category():
    """Get status counts grouped by category"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                category,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as complete,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Under Review' THEN 1 ELSE 0 END) as under_review,
                SUM(CASE WHEN status = 'Issue Flagged' THEN 1 ELSE 0 END) as flagged,
                SUM(CASE WHEN status = 'Not Started' THEN 1 ELSE 0 END) as not_started
            FROM dd_items
            GROUP BY category
            ORDER BY category
        ''')
        return cursor.fetchall()

def get_overall_stats():
    """Get overall project statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as complete,
                SUM(CASE WHEN status = 'Issue Flagged' THEN 1 ELSE 0 END) as flagged
            FROM dd_items
        ''')
        return cursor.fetchone()

def get_flagged_items():
    """Get all items with Issue Flagged status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dd_items
            WHERE status = 'Issue Flagged'
            ORDER BY category, item_name
        ''')
        return cursor.fetchall()

def get_items_due_soon(days=7):
    """Get items due within specified number of days"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        future_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT * FROM dd_items
            WHERE due_date <= ? AND status != 'Complete'
            ORDER BY due_date
        ''', (future_date,))
        return cursor.fetchall()

def get_item_by_id(item_id):
    """Get a specific DD item by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM dd_items WHERE id = ?', (item_id,))
        return cursor.fetchone()

def update_item(item_id, status, responsible_party, due_date, notes):
    """Update an existing DD item"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE dd_items
            SET status = ?,
                responsible_party = ?,
                due_date = ?,
                notes = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, responsible_party, due_date, notes, item_id))
        conn.commit()

def add_new_item(category, item_name, status, responsible_party, due_date, notes):
    """Add a new DD item"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dd_items (category, item_name, status, responsible_party, due_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (category, item_name, status, responsible_party, due_date, notes))
        conn.commit()
        return cursor.lastrowid

def delete_item(item_id):
    """Delete a DD item"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM dd_items WHERE id = ?', (item_id,))
        conn.commit()

def get_property_name():
    """Get the current property name"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT property_name FROM property_info WHERE id = 1')
        result = cursor.fetchone()
        return result['property_name'] if result else "Property Name"

def update_property_name(new_name):
    """Update the property name"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE property_info
            SET property_name = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (new_name,))
        conn.commit()

def get_all_categories():
    """Get list of all unique categories"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM dd_items ORDER BY category')
        return [row['category'] for row in cursor.fetchall()]

def get_all_statuses():
    """Get list of all possible statuses"""
    return ["Not Started", "In Progress", "Under Review", "Complete", "Issue Flagged"]
