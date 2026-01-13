import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import database as db

# Page configuration
st.set_page_config(
    page_title="Due Diligence Tracker",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .status-complete {
        background-color: #d4edda;
        color: #155724;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-in-progress {
        background-color: #fff3cd;
        color: #856404;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-flagged {
        background-color: #f8d7da;
        color: #721c24;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-review {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-not-started {
        background-color: #e9ecef;
        color: #495057;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #007bff;
    }
    .flagged-card {
        background-color: #fff5f5;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin-bottom: 10px;
    }
    h1 {
        color: #2c3e50;
        font-weight: 600;
    }
    h2 {
        color: #34495e;
        font-weight: 500;
        margin-top: 30px;
    }
    h3 {
        color: #546e7a;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database
db.init_database()

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'
if 'edit_item_id' not in st.session_state:
    st.session_state.edit_item_id = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False

def format_status_badge(status):
    """Return HTML for status badge"""
    status_classes = {
        "Complete": "status-complete",
        "In Progress": "status-in-progress",
        "Issue Flagged": "status-flagged",
        "Under Review": "status-review",
        "Not Started": "status-not-started"
    }
    css_class = status_classes.get(status, "status-not-started")
    return f'<span class="{css_class}">{status}</span>'

def create_progress_chart(stats):
    """Create a pie chart showing overall progress"""
    labels = []
    values = []
    colors = []

    status_config = [
        ("Complete", stats['complete'], "#28a745"),
        ("In Progress", stats['total'] - stats['complete'] - stats.get('flagged', 0), "#ffc107"),
        ("Issue Flagged", stats.get('flagged', 0), "#dc3545")
    ]

    for label, value, color in status_config:
        if value > 0:
            labels.append(label)
            values.append(value)
            colors.append(color)

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='auto'
    )])

    fig.update_layout(
        showlegend=True,
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def dashboard_view():
    """Display the main dashboard with summary and progress"""
    st.title("📊 Due Diligence Dashboard")

    # Property name with edit capability
    col1, col2 = st.columns([3, 1])
    with col1:
        property_name = db.get_property_name()
        new_property_name = st.text_input("Property Name:", value=property_name, key="property_name_input")
        if new_property_name != property_name:
            db.update_property_name(new_property_name)
            st.rerun()

    st.markdown("---")

    # Overall statistics
    stats = db.get_overall_stats()
    total = stats['total']
    complete = stats['complete']
    flagged = stats['flagged']
    completion_pct = (complete / total * 100) if total > 0 else 0

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Items",
            value=total
        )

    with col2:
        st.metric(
            label="Complete",
            value=f"{complete} ({completion_pct:.1f}%)"
        )

    with col3:
        st.metric(
            label="In Progress",
            value=total - complete
        )

    with col4:
        st.metric(
            label="Issues Flagged",
            value=flagged,
            delta=None if flagged == 0 else "Attention Required",
            delta_color="inverse"
        )

    st.markdown("---")

    # Progress visualization and flagged items
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Overall Progress")
        if total > 0:
            fig = create_progress_chart(stats)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No items in database")

    with col2:
        st.subheader("Flagged Issues")
        flagged_items = db.get_flagged_items()
        if flagged_items:
            for item in flagged_items:
                st.markdown(f"""
                    <div class="flagged-card">
                        <strong>{item['category']}</strong>: {item['item_name']}<br>
                        <small>Responsible: {item['responsible_party'] or 'Unassigned'} |
                        Due: {item['due_date'] or 'No date set'}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No issues flagged!")

    st.markdown("---")

    # Items due soon
    st.subheader("⏰ Items Due in Next 7 Days")
    due_soon = db.get_items_due_soon(7)
    if due_soon:
        due_df = pd.DataFrame([dict(item) for item in due_soon])
        due_df = due_df[['category', 'item_name', 'status', 'responsible_party', 'due_date']]
        due_df.columns = ['Category', 'Item', 'Status', 'Responsible Party', 'Due Date']
        st.dataframe(due_df, use_container_width=True, hide_index=True)
    else:
        st.info("No items due in the next 7 days")

    st.markdown("---")

    # Category breakdown
    st.subheader("📋 Status by Category")
    summary = db.get_summary_by_category()

    if summary:
        summary_data = []
        for row in summary:
            total_cat = row['total']
            complete_cat = row['complete']
            pct_complete = (complete_cat / total_cat * 100) if total_cat > 0 else 0

            summary_data.append({
                'Category': row['category'],
                'Total': total_cat,
                'Complete': complete_cat,
                'In Progress': row['in_progress'],
                'Under Review': row['under_review'],
                'Flagged': row['flagged'],
                'Not Started': row['not_started'],
                'Progress': f"{pct_complete:.0f}%"
            })

        summary_df = pd.DataFrame(summary_data)

        # Display table with progress bars
        for idx, row_data in summary_df.iterrows():
            col1, col2, col3 = st.columns([2, 3, 1])

            with col1:
                st.write(f"**{row_data['Category']}**")

            with col2:
                progress_val = int(row_data['Progress'].rstrip('%'))
                st.progress(progress_val / 100)

            with col3:
                st.write(f"{row_data['Complete']}/{row_data['Total']}")

            # Show details in expander
            with st.expander(f"View {row_data['Category']} details"):
                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                col_a.metric("Complete", row_data['Complete'])
                col_b.metric("In Progress", row_data['In Progress'])
                col_c.metric("Under Review", row_data['Under Review'])
                col_d.metric("Flagged", row_data['Flagged'])
                col_e.metric("Not Started", row_data['Not Started'])

def detail_view():
    """Display detailed list view with filtering and editing"""
    st.title("📝 Detailed Item List")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        categories = ["All"] + db.get_all_categories()
        selected_category = st.selectbox("Filter by Category:", categories)

    with col2:
        statuses = ["All"] + db.get_all_statuses()
        selected_status = st.selectbox("Filter by Status:", statuses)

    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add New Item", use_container_width=True):
            st.session_state.show_add_form = True
            st.session_state.edit_item_id = None

    st.markdown("---")

    # Show add/edit form if needed
    if st.session_state.show_add_form or st.session_state.edit_item_id:
        show_edit_form()
        st.markdown("---")

    # Get filtered items
    items = db.get_items_by_filters(
        category=selected_category if selected_category != "All" else None,
        status=selected_status if selected_status != "All" else None
    )

    if items:
        st.subheader(f"Found {len(items)} item(s)")

        # Convert to dataframe for display
        items_data = []
        for item in items:
            items_data.append({
                'ID': item['id'],
                'Category': item['category'],
                'Item Name': item['item_name'],
                'Status': item['status'],
                'Responsible Party': item['responsible_party'] or 'Unassigned',
                'Due Date': item['due_date'] or 'Not set',
                'Last Updated': item['last_updated']
            })

        df = pd.DataFrame(items_data)

        # Display items as cards for better interaction
        for item in items:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    st.markdown(f"**{item['item_name']}**")
                    st.caption(f"Category: {item['category']}")

                with col2:
                    st.markdown(format_status_badge(item['status']), unsafe_allow_html=True)

                with col3:
                    st.write(f"👤 {item['responsible_party'] or 'Unassigned'}")
                    st.caption(f"Due: {item['due_date'] or 'Not set'}")

                with col4:
                    if st.button("✏️", key=f"edit_{item['id']}", help="Edit this item"):
                        st.session_state.edit_item_id = item['id']
                        st.session_state.show_add_form = False
                        st.rerun()

                # Show notes if any
                if item['notes']:
                    with st.expander("View Notes"):
                        st.write(item['notes'])
                        st.caption(f"Last updated: {item['last_updated']}")

                st.markdown("---")
    else:
        st.info("No items found matching the selected filters.")

def show_edit_form():
    """Display form for editing or adding items"""
    if st.session_state.edit_item_id:
        st.subheader("✏️ Edit Item")
        item = db.get_item_by_id(st.session_state.edit_item_id)
        if not item:
            st.error("Item not found")
            st.session_state.edit_item_id = None
            return

        current_category = item['category']
        current_item_name = item['item_name']
        current_status = item['status']
        current_responsible = item['responsible_party'] or ""
        current_due_date = datetime.strptime(item['due_date'], "%Y-%m-%d").date() if item['due_date'] else None
        current_notes = item['notes'] or ""
        is_edit = True
    else:
        st.subheader("➕ Add New Item")
        current_category = db.get_all_categories()[0]
        current_item_name = ""
        current_status = "Not Started"
        current_responsible = ""
        current_due_date = None
        current_notes = ""
        is_edit = False

    with st.form(key="edit_form"):
        col1, col2 = st.columns(2)

        with col1:
            categories = db.get_all_categories()
            # Allow custom category
            category = st.selectbox("Category:", categories, index=categories.index(current_category) if is_edit else 0)
            custom_category = st.text_input("Or enter new category:", "")
            final_category = custom_category if custom_category else category

            item_name = st.text_input("Item Name:", value=current_item_name)

            status = st.selectbox("Status:", db.get_all_statuses(),
                                 index=db.get_all_statuses().index(current_status))

        with col2:
            responsible_party = st.text_input("Responsible Party:", value=current_responsible)

            due_date = st.date_input("Due Date:", value=current_due_date)

        notes = st.text_area("Notes:", value=current_notes, height=100)

        col_a, col_b, col_c = st.columns([1, 1, 4])

        with col_a:
            submit = st.form_submit_button("💾 Save", use_container_width=True)

        with col_b:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            if not item_name:
                st.error("Item name is required!")
            else:
                due_date_str = due_date.strftime("%Y-%m-%d") if due_date else ""

                if is_edit:
                    db.update_item(
                        st.session_state.edit_item_id,
                        status,
                        responsible_party,
                        due_date_str,
                        notes
                    )
                    st.success(f"✅ Updated: {item_name}")
                else:
                    db.add_new_item(
                        final_category,
                        item_name,
                        status,
                        responsible_party,
                        due_date_str,
                        notes
                    )
                    st.success(f"✅ Added: {item_name}")

                st.session_state.edit_item_id = None
                st.session_state.show_add_form = False
                st.rerun()

        if cancel:
            st.session_state.edit_item_id = None
            st.session_state.show_add_form = False
            st.rerun()

def generate_report():
    """Generate a markdown report"""
    property_name = db.get_property_name()
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Due Diligence Status Report
## {property_name}
**Generated:** {report_date}

---

## Executive Summary

"""

    # Overall stats
    stats = db.get_overall_stats()
    total = stats['total']
    complete = stats['complete']
    flagged = stats['flagged']
    completion_pct = (complete / total * 100) if total > 0 else 0

    report += f"""
- **Total Items:** {total}
- **Completed:** {complete} ({completion_pct:.1f}%)
- **In Progress:** {total - complete}
- **Issues Flagged:** {flagged}

---

## Status by Category

"""

    # Category breakdown
    summary = db.get_summary_by_category()
    for row in summary:
        total_cat = row['total']
        complete_cat = row['complete']
        pct = (complete_cat / total_cat * 100) if total_cat > 0 else 0

        report += f"""
### {row['category']}
- Progress: {complete_cat}/{total_cat} ({pct:.0f}%)
- Not Started: {row['not_started']}
- In Progress: {row['in_progress']}
- Under Review: {row['under_review']}
- Complete: {row['complete']}
- Flagged: {row['flagged']}

"""

    # Flagged issues
    report += "\n---\n\n## 🚩 Flagged Issues\n\n"
    flagged_items = db.get_flagged_items()
    if flagged_items:
        for item in flagged_items:
            report += f"""
### {item['category']}: {item['item_name']}
- **Responsible:** {item['responsible_party'] or 'Unassigned'}
- **Due Date:** {item['due_date'] or 'Not set'}
- **Notes:** {item['notes'] or 'No notes'}

"""
    else:
        report += "\n✅ No issues flagged\n"

    # Items due soon
    report += "\n---\n\n## ⏰ Items Due in Next 7 Days\n\n"
    due_soon = db.get_items_due_soon(7)
    if due_soon:
        for item in due_soon:
            report += f"""
- **{item['category']}**: {item['item_name']}
  - Status: {item['status']}
  - Responsible: {item['responsible_party'] or 'Unassigned'}
  - Due: {item['due_date']}

"""
    else:
        report += "\n✅ No items due in the next 7 days\n"

    report += "\n---\n\n*End of Report*\n"

    return report

def reports_view():
    """Display reports and export options"""
    st.title("📄 Reports & Export")

    st.markdown("""
    Generate and export Due Diligence status reports in Markdown format.
    Reports include:
    - Overall progress summary
    - Status breakdown by category
    - All flagged issues
    - Items due in the next 7 days
    """)

    st.markdown("---")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("📊 Generate Report", use_container_width=True):
            st.session_state.report_generated = True

    if st.session_state.get('report_generated', False):
        report = generate_report()

        st.subheader("Report Preview")

        # Display report
        st.markdown(report)

        st.markdown("---")

        # Download button
        property_name = db.get_property_name()
        filename = f"DD_Report_{property_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"

        st.download_button(
            label="⬇️ Download Report (Markdown)",
            data=report,
            file_name=filename,
            mime="text/markdown",
            use_container_width=False
        )

# Sidebar navigation
with st.sidebar:
    st.title("🏢 DD Tracker")
    st.markdown("### Navigation")

    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.current_view = 'dashboard'
        st.session_state.edit_item_id = None
        st.session_state.show_add_form = False
        st.rerun()

    if st.button("📝 Detail View", use_container_width=True):
        st.session_state.current_view = 'detail'
        st.session_state.edit_item_id = None
        st.session_state.show_add_form = False
        st.rerun()

    if st.button("📄 Reports", use_container_width=True):
        st.session_state.current_view = 'reports'
        st.session_state.edit_item_id = None
        st.session_state.show_add_form = False
        st.rerun()

    st.markdown("---")

    # Quick stats in sidebar
    stats = db.get_overall_stats()
    total = stats['total']
    complete = stats['complete']
    completion_pct = (complete / total * 100) if total > 0 else 0

    st.markdown("### Quick Stats")
    st.metric("Completion", f"{completion_pct:.0f}%")
    st.metric("Items", f"{complete}/{total}")

    if stats['flagged'] > 0:
        st.warning(f"⚠️ {stats['flagged']} issue(s) flagged")

    st.markdown("---")
    st.caption("Due Diligence Tracker v1.0")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Main content area - route to appropriate view
if st.session_state.current_view == 'dashboard':
    dashboard_view()
elif st.session_state.current_view == 'detail':
    detail_view()
elif st.session_state.current_view == 'reports':
    reports_view()
