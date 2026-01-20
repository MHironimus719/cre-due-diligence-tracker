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

        # Create property info table for storing property name (legacy - will be migrated)
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

        # Run migration to multi-property schema
        migrate_to_multi_property()


def migrate_to_multi_property():
    """
    Migrate database from single-property to multi-property schema.
    This function is idempotent - safe to run multiple times.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if migration has already been done
        cursor.execute("PRAGMA table_info(dd_items)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'property_id' in columns:
            # Migration already complete
            return

        print("Migrating database to multi-property schema...")

        # Step 1: Create properties table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                asset_type TEXT,
                status TEXT DEFAULT 'Active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Step 2: Create templates tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                asset_type TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_default INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                notes TEXT,
                default_due_days INTEGER,
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
            )
        ''')

        # Step 3: Migrate existing property_info data to properties table
        cursor.execute('SELECT property_name FROM property_info WHERE id = 1')
        old_property = cursor.fetchone()

        if old_property:
            property_name = old_property['property_name']
            cursor.execute('''
                INSERT INTO properties (id, name, address, asset_type, status)
                VALUES (1, ?, '', 'Other', 'Active')
            ''', (property_name,))
            print(f"  - Migrated existing property: {property_name}")
        else:
            # No existing property, create a default one
            cursor.execute('''
                INSERT INTO properties (id, name, address, asset_type, status)
                VALUES (1, 'Property Name', '', 'Other', 'Active')
            ''')
            print("  - Created default property")

        # Step 4: Add property_id column to dd_items
        cursor.execute('ALTER TABLE dd_items ADD COLUMN property_id INTEGER DEFAULT 1')
        print("  - Added property_id column to dd_items")

        # Step 5: Update all existing dd_items to property_id = 1
        cursor.execute('UPDATE dd_items SET property_id = 1 WHERE property_id IS NULL')
        print("  - Assigned all existing DD items to first property")

        # Step 6: Create index on property_id for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dd_items_property_id ON dd_items(property_id)')
        print("  - Created index on property_id")

        # Step 7: Create standard template from default DD items
        cursor.execute('''
            INSERT INTO templates (name, description, asset_type, is_default)
            VALUES ('Standard DD Checklist', '28-item standard due diligence checklist for CRE acquisitions', 'All', 1)
        ''')
        template_id = cursor.lastrowid

        # Get template items from the default function
        default_items = get_default_dd_items()
        template_items = []
        for item in default_items:
            category, item_name, status, responsible, due_date_str, notes = item
            # Calculate default_due_days from the due_date in the item
            # (Items have dates like base_date + timedelta(days=X))
            # We'll extract the day offset
            base_date = datetime.now()
            if due_date_str:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                days_offset = (due_date - base_date).days
            else:
                days_offset = 30  # default

            template_items.append((template_id, category, item_name, notes, days_offset))

        cursor.executemany('''
            INSERT INTO template_items (template_id, category, item_name, notes, default_due_days)
            VALUES (?, ?, ?, ?, ?)
        ''', template_items)
        print(f"  - Created standard template with {len(template_items)} items")

        # Step 8: Drop old property_info table (data already migrated)
        cursor.execute('DROP TABLE IF EXISTS property_info')
        print("  - Removed legacy property_info table")

        conn.commit()
        print("Migration complete! Multi-property support enabled.")

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

def get_all_items(property_id):
    """Retrieve all DD items for a specific property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dd_items
            WHERE property_id = ?
            ORDER BY category, item_name
        ''', (property_id,))
        return cursor.fetchall()

def get_items_by_filters(property_id, category=None, status=None):
    """Get items filtered by property, category and/or status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM dd_items WHERE property_id = ?'
        params = [property_id]

        if category and category != "All":
            query += ' AND category = ?'
            params.append(category)

        if status and status != "All":
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY category, item_name'
        cursor.execute(query, params)
        return cursor.fetchall()

def get_summary_by_category(property_id):
    """Get status counts grouped by category for a specific property"""
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
            WHERE property_id = ?
            GROUP BY category
            ORDER BY category
        ''', (property_id,))
        return cursor.fetchall()

def get_overall_stats(property_id):
    """Get overall statistics for a specific property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as complete,
                SUM(CASE WHEN status = 'Issue Flagged' THEN 1 ELSE 0 END) as flagged
            FROM dd_items
            WHERE property_id = ?
        ''', (property_id,))
        return cursor.fetchone()

def get_flagged_items(property_id):
    """Get all items with Issue Flagged status for a specific property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dd_items
            WHERE property_id = ? AND status = 'Issue Flagged'
            ORDER BY category, item_name
        ''', (property_id,))
        return cursor.fetchall()

def get_items_due_soon(property_id, days=7):
    """Get items due within specified number of days for a specific property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        future_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT * FROM dd_items
            WHERE property_id = ? AND due_date <= ? AND status != 'Complete'
            ORDER BY due_date
        ''', (property_id, future_date))
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

def add_new_item(property_id, category, item_name, status, responsible_party, due_date, notes):
    """Add a new DD item to a specific property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dd_items (property_id, category, item_name, status, responsible_party, due_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (property_id, category, item_name, status, responsible_party, due_date, notes))
        conn.commit()
        return cursor.lastrowid

def delete_item(item_id):
    """Delete a DD item"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM dd_items WHERE id = ?', (item_id,))
        conn.commit()

# ============================================================================
# PROPERTY MANAGEMENT FUNCTIONS
# ============================================================================

def get_all_properties():
    """Get all properties (active and closed)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM properties
            ORDER BY status DESC, created_date DESC
        ''')
        return cursor.fetchall()

def get_active_properties():
    """Get only active properties"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM properties
            WHERE status = 'Active'
            ORDER BY name
        ''')
        return cursor.fetchall()

def get_property_by_id(property_id):
    """Get a specific property by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM properties WHERE id = ?', (property_id,))
        return cursor.fetchone()

def create_property(name, address='', asset_type='Other', status='Active'):
    """Create a new property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO properties (name, address, asset_type, status)
            VALUES (?, ?, ?, ?)
        ''', (name, address, asset_type, status))
        conn.commit()
        return cursor.lastrowid

def update_property(property_id, name, address, asset_type, status):
    """Update an existing property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE properties
            SET name = ?, address = ?, asset_type = ?, status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, address, asset_type, status, property_id))
        conn.commit()

def delete_property(property_id):
    """Delete a property (cascade deletes all DD items)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Delete property (dd_items will be cascaded if we had FK constraint)
        # Since SQLite needs special handling for FK, we'll delete manually
        cursor.execute('DELETE FROM dd_items WHERE property_id = ?', (property_id,))
        cursor.execute('DELETE FROM properties WHERE id = ?', (property_id,))
        conn.commit()

# ============================================================================
# TEMPLATE MANAGEMENT FUNCTIONS
# ============================================================================

def get_all_templates():
    """Get all available templates"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM templates
            ORDER BY is_default DESC, name
        ''')
        return cursor.fetchall()

def get_template_by_id(template_id):
    """Get a specific template by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates WHERE id = ?', (template_id,))
        return cursor.fetchone()

def get_template_items(template_id):
    """Get all items for a specific template"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM template_items
            WHERE template_id = ?
            ORDER BY category, item_name
        ''', (template_id,))
        return cursor.fetchall()

def create_template(name, description='', asset_type='All', is_default=0):
    """Create a new template"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO templates (name, description, asset_type, is_default)
            VALUES (?, ?, ?, ?)
        ''', (name, description, asset_type, is_default))
        conn.commit()
        return cursor.lastrowid

def save_property_as_template(property_id, template_name, description=''):
    """Save a property's DD items as a reusable template"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get the property details
        property = get_property_by_id(property_id)
        if not property:
            return None

        # Create new template
        asset_type = property['asset_type'] if property['asset_type'] else 'All'
        cursor.execute('''
            INSERT INTO templates (name, description, asset_type, is_default)
            VALUES (?, ?, ?, 0)
        ''', (template_name, description, asset_type))
        template_id = cursor.lastrowid

        # Copy DD items from property to template
        cursor.execute('''
            SELECT category, item_name, notes, due_date
            FROM dd_items
            WHERE property_id = ?
            ORDER BY category, item_name
        ''', (property_id,))

        items = cursor.fetchall()
        base_date = datetime.now()

        template_items = []
        for item in items:
            # Calculate days offset from due_date
            if item['due_date']:
                try:
                    due_date = datetime.strptime(item['due_date'], "%Y-%m-%d")
                    days_offset = (due_date - base_date).days
                except:
                    days_offset = 30
            else:
                days_offset = 30

            template_items.append((
                template_id,
                item['category'],
                item['item_name'],
                item['notes'],
                days_offset
            ))

        cursor.executemany('''
            INSERT INTO template_items (template_id, category, item_name, notes, default_due_days)
            VALUES (?, ?, ?, ?, ?)
        ''', template_items)

        conn.commit()
        return template_id

def apply_template_to_property(property_id, template_id):
    """Apply a template's items to a property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get template items
        cursor.execute('''
            SELECT category, item_name, notes, default_due_days
            FROM template_items
            WHERE template_id = ?
        ''', (template_id,))

        template_items = cursor.fetchall()
        base_date = datetime.now()

        # Create DD items for this property
        dd_items = []
        for item in template_items:
            due_date = (base_date + timedelta(days=item['default_due_days'])).strftime("%Y-%m-%d")
            dd_items.append((
                property_id,
                item['category'],
                item['item_name'],
                'Not Started',
                '',  # responsible_party
                due_date,
                item['notes'] if item['notes'] else ''
            ))

        cursor.executemany('''
            INSERT INTO dd_items (property_id, category, item_name, status, responsible_party, due_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', dd_items)

        conn.commit()
        return len(dd_items)

def delete_template(template_id):
    """Delete a template (cascade deletes template_items)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM template_items WHERE template_id = ?', (template_id,))
        cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        conn.commit()

# ============================================================================
# PORTFOLIO ANALYTICS FUNCTIONS
# ============================================================================

def get_portfolio_summary():
    """Get aggregate statistics across all active properties"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get property count
        cursor.execute('SELECT COUNT(*) as count FROM properties WHERE status = "Active"')
        active_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM properties WHERE status != "Active"')
        closed_count = cursor.fetchone()['count']

        # Get overall DD item statistics across all active properties
        cursor.execute('''
            SELECT
                COUNT(*) as total_items,
                SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as complete_items,
                SUM(CASE WHEN status = 'Issue Flagged' THEN 1 ELSE 0 END) as flagged_items
            FROM dd_items
            WHERE property_id IN (SELECT id FROM properties WHERE status = 'Active')
        ''')
        item_stats = cursor.fetchone()

        return {
            'active_properties': active_count,
            'closed_properties': closed_count,
            'total_items': item_stats['total_items'],
            'complete_items': item_stats['complete_items'],
            'flagged_items': item_stats['flagged_items'],
            'completion_pct': (item_stats['complete_items'] / item_stats['total_items'] * 100)
                if item_stats['total_items'] > 0 else 0
        }

def get_properties_with_stats():
    """Get all active properties with their DD statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                p.id,
                p.name,
                p.address,
                p.asset_type,
                p.status,
                p.last_updated,
                COUNT(d.id) as total_items,
                SUM(CASE WHEN d.status = 'Complete' THEN 1 ELSE 0 END) as complete_items,
                SUM(CASE WHEN d.status = 'Issue Flagged' THEN 1 ELSE 0 END) as flagged_items,
                SUM(CASE WHEN d.due_date <= date('now', '+7 days') AND d.status != 'Complete' THEN 1 ELSE 0 END) as due_soon_items
            FROM properties p
            LEFT JOIN dd_items d ON p.id = d.property_id
            WHERE p.status = 'Active'
            GROUP BY p.id
            ORDER BY p.name
        ''')
        return cursor.fetchall()

def get_properties_at_risk(days=3):
    """Get properties with many items due soon"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        future_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT
                p.id,
                p.name,
                COUNT(d.id) as items_due_soon
            FROM properties p
            JOIN dd_items d ON p.id = d.property_id
            WHERE p.status = 'Active'
                AND d.due_date <= ?
                AND d.status != 'Complete'
            GROUP BY p.id
            HAVING COUNT(d.id) >= 5
            ORDER BY items_due_soon DESC
        ''', (future_date,))
        return cursor.fetchall()

def get_all_flagged_items_by_property():
    """Get all flagged items grouped by property"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                p.id as property_id,
                p.name as property_name,
                d.category,
                d.item_name,
                d.responsible_party,
                d.due_date,
                d.notes,
                d.status,
                d.last_updated
            FROM properties p
            JOIN dd_items d ON p.id = d.property_id
            WHERE p.status = 'Active' AND d.status = 'Issue Flagged'
            ORDER BY p.name, d.category, d.item_name
        ''')
        return cursor.fetchall()

def get_category_completion_by_property():
    """Get completion percentage by category for each property (for heatmap)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                p.id as property_id,
                p.name as property_name,
                d.category,
                COUNT(*) as total,
                SUM(CASE WHEN d.status = 'Complete' THEN 1 ELSE 0 END) as complete,
                CAST(SUM(CASE WHEN d.status = 'Complete' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as completion_pct
            FROM properties p
            JOIN dd_items d ON p.id = d.property_id
            WHERE p.status = 'Active'
            GROUP BY p.id, d.category
            ORDER BY p.name, d.category
        ''')
        return cursor.fetchall()

def get_upcoming_deadlines_all_properties(days=30):
    """Get all DD items due across all properties for timeline view"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        future_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT
                p.id as property_id,
                p.name as property_name,
                d.id as item_id,
                d.category,
                d.item_name,
                d.status,
                d.due_date,
                d.responsible_party
            FROM properties p
            JOIN dd_items d ON p.id = d.property_id
            WHERE p.status = 'Active'
                AND d.due_date <= ?
                AND d.status != 'Complete'
            ORDER BY d.due_date, p.name
        ''', (future_date,))
        return cursor.fetchall()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_categories():
    """Get list of all unique categories"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM dd_items ORDER BY category')
        return [row['category'] for row in cursor.fetchall()]

def get_all_statuses():
    """Get list of all possible statuses"""
    return ["Not Started", "In Progress", "Under Review", "Complete", "Issue Flagged"]
