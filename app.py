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
if 'show_new_property_form' not in st.session_state:
    st.session_state.show_new_property_form = False
if 'show_edit_property_form' not in st.session_state:
    st.session_state.show_edit_property_form = False
if 'show_delete_confirmation' not in st.session_state:
    st.session_state.show_delete_confirmation = False
if 'current_property_id' not in st.session_state:
    # Get the first active property as default
    active_properties = db.get_active_properties()
    if active_properties:
        st.session_state.current_property_id = active_properties[0]['id']
    else:
        st.session_state.current_property_id = None

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

    flagged_count = stats['flagged'] if 'flagged' in stats.keys() else 0

    status_config = [
        ("Complete", stats['complete'], "#28a745"),
        ("In Progress", stats['total'] - stats['complete'] - flagged_count, "#ffc107"),
        ("Issue Flagged", flagged_count, "#dc3545")
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
    property_id = st.session_state.get('current_property_id')

    if not property_id:
        st.warning("⚠️ Please select or create a property to view the dashboard.")
        return

    property_info = db.get_property_by_id(property_id)
    if not property_info:
        st.error("Property not found. Please select a different property.")
        return

    st.title(f"📊 Due Diligence Dashboard - {property_info['name']}")

    # Display property details
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if property_info['address']:
            st.caption(f"📍 {property_info['address']}")
    with col2:
        if property_info['asset_type']:
            st.caption(f"🏢 {property_info['asset_type']}")
    with col3:
        if st.button("💾 Save as Template", key="save_template_btn", use_container_width=True):
            st.session_state.show_save_template_form = True

    # Save as Template Form
    if st.session_state.get('show_save_template_form', False):
        with st.form("save_template_form"):
            st.subheader("💾 Save Checklist as Template")

            template_name = st.text_input("Template Name*",
                placeholder=f"e.g., {property_info['asset_type']} DD Checklist" if property_info['asset_type'] else "Custom DD Checklist")

            template_description = st.text_area("Description (optional)",
                placeholder="Describe when to use this template...")

            col1, col2 = st.columns(2)

            with col1:
                submitted = st.form_submit_button("✅ Save Template", use_container_width=True)

            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                if not template_name:
                    st.error("Template name is required!")
                else:
                    try:
                        template_id = db.save_property_as_template(
                            property_id,
                            template_name,
                            template_description
                        )
                        if template_id:
                            st.success(f"✅ Template '{template_name}' saved successfully!")
                            st.session_state.show_save_template_form = False
                            st.rerun()
                        else:
                            st.error("Failed to save template. Please try again.")
                    except Exception as e:
                        st.error(f"Error saving template: {str(e)}")

            if cancelled:
                st.session_state.show_save_template_form = False
                st.rerun()

    st.markdown("---")

    # Overall statistics
    stats = db.get_overall_stats(property_id)
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
        flagged_items = db.get_flagged_items(property_id)
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
    due_soon = db.get_items_due_soon(property_id, 7)
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
    summary = db.get_summary_by_category(property_id)

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
    property_id = st.session_state.get('current_property_id')

    if not property_id:
        st.warning("⚠️ Please select or create a property to view items.")
        return

    property_info = db.get_property_by_id(property_id)
    if not property_info:
        st.error("Property not found. Please select a different property.")
        return

    st.title(f"📝 Detailed Item List - {property_info['name']}")

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
        property_id,
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
                        st.session_state.current_property_id,
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

def generate_report(property_id):
    """Generate a markdown report for a specific property"""
    property_info = db.get_property_by_id(property_id)
    if not property_info:
        return "Error: Property not found"

    property_name = property_info['name']
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Due Diligence Status Report
## {property_name}
**Generated:** {report_date}

"""
    if property_info['address']:
        report += f"**Address:** {property_info['address']}\n"
    if property_info['asset_type']:
        report += f"**Asset Type:** {property_info['asset_type']}\n"

    report += """
---

## Executive Summary

"""

    # Overall stats
    stats = db.get_overall_stats(property_id)
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
    summary = db.get_summary_by_category(property_id)
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
    flagged_items = db.get_flagged_items(property_id)
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
    due_soon = db.get_items_due_soon(property_id, 7)
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
    property_id = st.session_state.get('current_property_id')

    if not property_id:
        st.warning("⚠️ Please select or create a property to generate reports.")
        return

    property_info = db.get_property_by_id(property_id)
    if not property_info:
        st.error("Property not found. Please select a different property.")
        return

    st.title(f"📄 Reports & Export - {property_info['name']}")

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
        report = generate_report(property_id)

        st.subheader("Report Preview")

        # Display report
        st.markdown(report)

        st.markdown("---")

        # Download button
        property_name = property_info['name']
        filename = f"DD_Report_{property_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"

        st.download_button(
            label="⬇️ Download Report (Markdown)",
            data=report,
            file_name=filename,
            mime="text/markdown",
            use_container_width=False
        )

def portfolio_view():
    """Display portfolio-wide analytics and summary across all properties"""
    st.title("📊 Portfolio Dashboard")

    st.markdown("""
    View aggregate analytics and status across all properties in your portfolio.
    """)

    st.markdown("---")

    # Section 1: Portfolio Overview
    st.subheader("Portfolio Overview")

    portfolio_summary = db.get_portfolio_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Properties",
            f"{portfolio_summary['active_properties']} Active",
            delta=f"{portfolio_summary['closed_properties']} Closed" if portfolio_summary['closed_properties'] > 0 else None
        )

    with col2:
        st.metric(
            "Overall Completion",
            f"{portfolio_summary['completion_pct']:.0f}%",
            delta=f"{portfolio_summary['complete_items']}/{portfolio_summary['total_items']} items"
        )

    with col3:
        st.metric(
            "Total Issues Flagged",
            portfolio_summary['flagged_items'],
            delta="Requires attention" if portfolio_summary['flagged_items'] > 0 else "All clear",
            delta_color="inverse"
        )

    with col4:
        at_risk_properties = db.get_properties_at_risk(days=3)
        st.metric(
            "Properties at Risk",
            len(at_risk_properties),
            delta=f"≥5 items due in 3 days" if len(at_risk_properties) > 0 else "None"
        )

    st.markdown("---")

    # Section 2: Properties Summary Table
    st.subheader("Properties Summary")

    properties_stats = db.get_properties_with_stats()

    if properties_stats:
        # Create a more visual table with progress bars
        for prop in properties_stats:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

                with col1:
                    # Property name with clickable link
                    if st.button(f"📍 {prop['name']}", key=f"prop_{prop['id']}", use_container_width=True):
                        st.session_state.current_property_id = prop['id']
                        st.session_state.current_view = 'dashboard'
                        st.rerun()

                    # Address and type
                    st.caption(f"{prop['asset_type'] or 'No type'} • {prop['address'] or 'No address'}")

                with col2:
                    # Progress bar
                    total = prop['total_items']
                    complete = prop['complete_items']
                    completion_pct = (complete / total * 100) if total > 0 else 0

                    st.progress(completion_pct / 100)
                    st.caption(f"{completion_pct:.0f}% ({complete}/{total} items)")

                with col3:
                    # Flagged issues
                    if prop['flagged_items'] > 0:
                        st.markdown(f"🚩 **{prop['flagged_items']}** issues")
                    else:
                        st.caption("✅ No issues")

                with col4:
                    # Due soon
                    if prop['due_soon_items'] > 0:
                        st.markdown(f"⏰ **{prop['due_soon_items']}** due soon")
                    else:
                        st.caption("✅ On track")

                with col5:
                    # Last updated
                    st.caption(f"Updated: {prop['last_updated'][:10]}")

                st.markdown("---")
    else:
        st.info("No active properties found. Create a property to get started.")

    # Section 3: Flagged Issues Rollup
    st.subheader("🚩 All Flagged Issues Across Portfolio")

    all_flagged = db.get_all_flagged_items_by_property()

    if all_flagged:
        current_property_name = None

        for item in all_flagged:
            # Group by property
            if item['property_name'] != current_property_name:
                current_property_name = item['property_name']
                st.markdown(f"### {current_property_name}")

            # Display flagged item
            with st.expander(f"**{item['category']}**: {item['item_name']}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Responsible:** {item['responsible_party'] or 'Unassigned'}")
                    st.markdown(f"**Due Date:** {item['due_date'] or 'Not set'}")

                with col2:
                    st.markdown(f"**Status:** {item['status']}")
                    st.markdown(f"**Updated:** {item['last_updated'][:10]}")

                if item['notes']:
                    st.markdown(f"**Notes:** {item['notes']}")
    else:
        st.success("✅ No issues flagged across the portfolio!")

    st.markdown("---")

    # Section 4: Category Performance Heatmap
    st.subheader("📈 Category Performance Across Properties")

    category_data = db.get_category_completion_by_property()

    if category_data:
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame([
            {
                'Property': row['property_name'],
                'Category': row['category'],
                'Completion %': row['completion_pct']
            }
            for row in category_data
        ])

        # Pivot for heatmap
        pivot_df = df.pivot(index='Category', columns='Property', values='Completion %')

        # Display as styled dataframe
        st.dataframe(
            pivot_df.style.background_gradient(cmap='RdYlGn', vmin=0, vmax=100).format("{:.0f}%"),
            use_container_width=True
        )

        st.caption("Green = Complete | Yellow = In Progress | Red = Not Started")
    else:
        st.info("No data available for category performance heatmap.")

    st.markdown("---")

    # Section 5: Upcoming Deadlines Timeline
    st.subheader("⏰ Upcoming Deadlines (Next 30 Days)")

    upcoming_deadlines = db.get_upcoming_deadlines_all_properties(days=30)

    if upcoming_deadlines:
        # Group by property
        current_property_name = None

        for item in upcoming_deadlines:
            if item['property_name'] != current_property_name:
                current_property_name = item['property_name']
                st.markdown(f"### {current_property_name}")

            # Display deadline item
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

            with col1:
                st.markdown(f"**{item['item_name']}**")

            with col2:
                st.caption(f"{item['category']}")

            with col3:
                # Color code by urgency
                due_date = item['due_date']
                from datetime import datetime, timedelta

                if due_date:
                    days_until = (datetime.strptime(due_date, '%Y-%m-%d') - datetime.now()).days

                    if days_until < 0:
                        st.markdown(f"🔴 **OVERDUE** ({abs(days_until)}d)")
                    elif days_until <= 3:
                        st.markdown(f"🟠 **{days_until}d** remaining")
                    elif days_until <= 7:
                        st.markdown(f"🟡 **{days_until}d** remaining")
                    else:
                        st.markdown(f"🟢 **{days_until}d** remaining")

            with col4:
                st.caption(f"Due: {item['due_date']}")

            st.markdown("---")
    else:
        st.success("✅ No upcoming deadlines in the next 30 days!")

def template_library_view():
    """Display template library for browsing and managing DD checklist templates"""
    st.title("📚 Template Library")

    st.markdown("""
    Browse and manage Due Diligence checklist templates. Apply templates to new properties
    or save existing property checklists as reusable templates.
    """)

    st.markdown("---")

    # Get all templates
    templates = db.get_all_templates()

    if not templates:
        st.info("No templates available. Create your first template by saving a property's checklist.")
    else:
        # Display template count
        st.subheader(f"Available Templates ({len(templates)})")

        # Template cards in grid layout
        for i in range(0, len(templates), 2):
            cols = st.columns(2)

            for idx, col in enumerate(cols):
                template_idx = i + idx
                if template_idx < len(templates):
                    template = templates[template_idx]

                    with col:
                        with st.container():
                            # Template card
                            st.markdown(f"""
                                <div style="background-color: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 16px;">
                                    <div style="font-weight: 600; font-size: 16px; color: #1f2937;">{template['name']}</div>
                                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                                        {template['asset_type'] if template['asset_type'] else 'General'}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            # Get template items count
                            template_items = db.get_template_items(template['id'])
                            item_count = len(template_items)

                            st.caption(f"📝 {item_count} checklist items")

                            if template['description']:
                                st.caption(f"ℹ️ {template['description']}")

                            # Action buttons
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if st.button("👁️ Preview", key=f"preview_{template['id']}", use_container_width=True):
                                    st.session_state[f"show_preview_{template['id']}"] = not st.session_state.get(f"show_preview_{template['id']}", False)

                            with col2:
                                if st.button("📋 Apply", key=f"apply_{template['id']}", use_container_width=True):
                                    st.session_state[f"show_apply_{template['id']}"] = not st.session_state.get(f"show_apply_{template['id']}", False)

                            with col3:
                                if template['id'] != 1:  # Don't allow deleting the default template
                                    if st.button("🗑️ Delete", key=f"delete_{template['id']}", use_container_width=True):
                                        st.session_state[f"confirm_delete_{template['id']}"] = True

                            # Preview expandable section
                            if st.session_state.get(f"show_preview_{template['id']}", False):
                                with st.expander("📋 Template Items", expanded=True):
                                    # Group by category
                                    categories = {}
                                    for item in template_items:
                                        cat = item['category']
                                        if cat not in categories:
                                            categories[cat] = []
                                        categories[cat].append(item)

                                    for category, items in categories.items():
                                        st.markdown(f"**{category}** ({len(items)} items)")
                                        for item in items:
                                            days_text = f" (Due in {item['default_due_days']} days)" if item['default_due_days'] else ""
                                            st.markdown(f"- {item['item_name']}{days_text}")
                                        st.markdown("")

                            # Apply to property section
                            if st.session_state.get(f"show_apply_{template['id']}", False):
                                with st.expander("📋 Apply to Property", expanded=True):
                                    st.markdown("Select a property to apply this template:")

                                    properties = db.get_active_properties()
                                    if properties:
                                        property_options = {p['id']: f"{p['name']} ({p['asset_type']})" for p in properties}

                                        selected_property = st.selectbox(
                                            "Property:",
                                            options=list(property_options.keys()),
                                            format_func=lambda x: property_options[x],
                                            key=f"apply_property_{template['id']}"
                                        )

                                        col1, col2 = st.columns(2)

                                        with col1:
                                            if st.button("✅ Apply Template", key=f"confirm_apply_{template['id']}", use_container_width=True):
                                                try:
                                                    db.apply_template_to_property(selected_property, template['id'])
                                                    st.success(f"Template applied to {property_options[selected_property]}!")
                                                    st.session_state[f"show_apply_{template['id']}"] = False
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Error applying template: {str(e)}")

                                        with col2:
                                            if st.button("Cancel", key=f"cancel_apply_{template['id']}", use_container_width=True):
                                                st.session_state[f"show_apply_{template['id']}"] = False
                                                st.rerun()
                                    else:
                                        st.warning("No active properties available. Create a property first.")

                            # Delete confirmation
                            if st.session_state.get(f"confirm_delete_{template['id']}", False):
                                st.warning(f"⚠️ Delete template '{template['name']}'?")
                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("✅ Confirm Delete", key=f"confirm_delete_yes_{template['id']}", use_container_width=True):
                                        try:
                                            db.delete_template(template['id'])
                                            st.success(f"Template '{template['name']}' deleted!")
                                            st.session_state[f"confirm_delete_{template['id']}"] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error deleting template: {str(e)}")

                                with col2:
                                    if st.button("Cancel", key=f"cancel_delete_{template['id']}", use_container_width=True):
                                        st.session_state[f"confirm_delete_{template['id']}"] = False
                                        st.rerun()

                            st.markdown("---")

# Sidebar navigation
with st.sidebar:
    st.title("🏢 DD Tracker")

    # Property Selection
    st.markdown("### Property Selection")

    properties = db.get_active_properties()

    if properties:
        # Get current property info
        current_property = None
        if st.session_state.current_property_id:
            current_property = db.get_property_by_id(st.session_state.current_property_id)

        # Display current property as a styled card
        if current_property:
            st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 12px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 10px;">
                    <div style="font-weight: 600; font-size: 14px; color: #1f2937;">{current_property['name']}</div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                        {current_property['asset_type'] if current_property['asset_type'] else 'No type'}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Property selector using radio buttons for better UX with 4-10 properties
        if len(properties) <= 6:
            # For 6 or fewer properties, use radio buttons (more visual)
            property_options = {p['id']: f"{p['name']} ({p['asset_type']})" for p in properties}

            selected_property_id = st.radio(
                "Switch to:",
                options=list(property_options.keys()),
                format_func=lambda x: property_options[x],
                key="property_selector",
                index=list(property_options.keys()).index(st.session_state.current_property_id)
                    if st.session_state.current_property_id in property_options else 0,
                label_visibility="collapsed"
            )
        else:
            # For 7+ properties, use searchable selectbox
            property_names = {p['id']: f"{p['name']} - {p['asset_type']}" for p in properties}

            selected_property_id = st.selectbox(
                "Switch to:",
                options=list(property_names.keys()),
                format_func=lambda x: property_names[x],
                key="property_selector",
                index=list(property_names.keys()).index(st.session_state.current_property_id)
                    if st.session_state.current_property_id in property_names else 0,
                label_visibility="collapsed"
            )

        # Update session state if property changed
        if selected_property_id != st.session_state.current_property_id:
            st.session_state.current_property_id = selected_property_id
            st.rerun()
    else:
        st.warning("No properties found")

    st.markdown("---")

    # New Property button
    if st.button("➕ New Property", use_container_width=True):
        st.session_state.show_new_property_form = True

    # New Property Form (Modal-like)
    if st.session_state.get('show_new_property_form', False):
        st.markdown("---")
        with st.form("new_property_form"):
            st.subheader("Create New Property")

            name = st.text_input("Property Name*")
            address = st.text_input("Address")
            asset_type = st.selectbox("Asset Type",
                ["Office", "Retail", "Multifamily", "Industrial", "Mixed-Use", "Land", "Hospitality", "Other"])

            apply_template = st.checkbox("Apply standard DD checklist", value=True)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Create", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                if not name:
                    st.error("Property name required!")
                else:
                    # Create the property
                    property_id = db.create_property(name, address, asset_type)

                    # Apply template if requested
                    if apply_template:
                        templates = db.get_all_templates()
                        if templates:
                            # Use first template (standard template)
                            db.apply_template_to_property(property_id, templates[0]['id'])

                    # Set as current property
                    st.session_state.current_property_id = property_id
                    st.session_state.show_new_property_form = False
                    st.success(f"Created: {name}")
                    st.rerun()

            if cancelled:
                st.session_state.show_new_property_form = False
                st.rerun()

    # Edit/Delete Property buttons (only show if a property is selected)
    if st.session_state.current_property_id and properties:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit", use_container_width=True, key="edit_property_btn"):
                st.session_state.show_edit_property_form = True
                st.session_state.show_delete_confirmation = False
        with col2:
            if st.button("🗑️ Delete", use_container_width=True, key="delete_property_btn"):
                st.session_state.show_delete_confirmation = True
                st.session_state.show_edit_property_form = False

    # Edit Property Form
    if st.session_state.get('show_edit_property_form', False) and st.session_state.current_property_id:
        current_prop = db.get_property_by_id(st.session_state.current_property_id)
        if current_prop:
            st.markdown("---")
            with st.form("edit_property_form"):
                st.subheader("Edit Property")

                edit_name = st.text_input("Property Name*", value=current_prop['name'])
                edit_address = st.text_input("Address", value=current_prop['address'] or '')
                asset_types = ["Office", "Retail", "Multifamily", "Industrial", "Mixed-Use", "Land", "Hospitality", "Other"]
                current_type_index = asset_types.index(current_prop['asset_type']) if current_prop['asset_type'] in asset_types else 7
                edit_asset_type = st.selectbox("Asset Type", asset_types, index=current_type_index)
                status_options = ["Active", "On Hold", "Closed", "Cancelled"]
                current_status_index = status_options.index(current_prop['status']) if current_prop['status'] in status_options else 0
                edit_status = st.selectbox("Status", status_options, index=current_status_index)

                col1, col2 = st.columns(2)
                with col1:
                    save_clicked = st.form_submit_button("Save", use_container_width=True)
                with col2:
                    cancel_edit = st.form_submit_button("Cancel", use_container_width=True)

                if save_clicked:
                    if not edit_name:
                        st.error("Property name is required!")
                    else:
                        db.update_property(st.session_state.current_property_id, edit_name, edit_address, edit_asset_type, edit_status)
                        st.session_state.show_edit_property_form = False
                        st.success(f"Updated: {edit_name}")
                        st.rerun()

                if cancel_edit:
                    st.session_state.show_edit_property_form = False
                    st.rerun()

    # Delete Property Confirmation
    if st.session_state.get('show_delete_confirmation', False) and st.session_state.current_property_id:
        current_prop = db.get_property_by_id(st.session_state.current_property_id)
        if current_prop:
            st.markdown("---")
            st.error(f"⚠️ Delete '{current_prop['name']}'?")
            st.caption("This will permanently delete the property and all its due diligence items.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", use_container_width=True, type="primary", key="confirm_delete"):
                    property_name = current_prop['name']
                    db.delete_property(st.session_state.current_property_id)
                    # Switch to another property if available
                    remaining = db.get_active_properties()
                    if remaining:
                        st.session_state.current_property_id = remaining[0]['id']
                    else:
                        st.session_state.current_property_id = None
                    st.session_state.show_delete_confirmation = False
                    st.success(f"Deleted: {property_name}")
                    st.rerun()
            with col2:
                if st.button("Cancel", use_container_width=True, key="cancel_delete"):
                    st.session_state.show_delete_confirmation = False
                    st.rerun()

    st.markdown("---")
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

    if st.button("📊 Portfolio", use_container_width=True):
        st.session_state.current_view = 'portfolio'
        st.session_state.edit_item_id = None
        st.session_state.show_add_form = False
        st.rerun()

    if st.button("📚 Templates", use_container_width=True):
        st.session_state.current_view = 'templates'
        st.session_state.edit_item_id = None
        st.session_state.show_add_form = False
        st.rerun()

    st.markdown("---")

    # Quick stats in sidebar (only show if property selected)
    if st.session_state.current_property_id:
        stats = db.get_overall_stats(st.session_state.current_property_id)
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
elif st.session_state.current_view == 'portfolio':
    portfolio_view()
elif st.session_state.current_view == 'templates':
    template_library_view()
