# Due Diligence Tracker for Commercial Real Estate

A comprehensive web application built with Streamlit to track and manage due diligence workstreams for commercial real estate property acquisitions.

## Features

### 📊 Dashboard View
- **Visual Progress Tracking**: Interactive pie chart showing completion status
- **Key Metrics**: Total items, completion percentage, items in progress, and flagged issues
- **Flagged Issues Alert**: Immediate visibility of items requiring attention
- **Upcoming Deadlines**: Items due in the next 7 days
- **Category Breakdown**: Progress bars and detailed statistics for each DD category

### 📝 Detail View
- **Comprehensive Item List**: View all due diligence items with full details
- **Advanced Filtering**: Filter by category and status
- **Quick Edit**: One-click access to edit any item
- **Add New Items**: Easily add custom DD checklist items
- **Status Tracking**: Track items through their lifecycle (Not Started → In Progress → Under Review → Complete)
- **Issue Flagging**: Mark items that require special attention

### 📄 Reports & Export
- **Markdown Reports**: Generate comprehensive status reports
- **Executive Summary**: High-level overview of DD progress
- **Category Analysis**: Detailed breakdown by each DD category
- **Issue Tracking**: All flagged items with notes and responsible parties
- **Deadline Monitoring**: Items due within the next 7 days
- **Download Reports**: Export reports in Markdown format

### 🗄️ Data Management
- **SQLite Database**: Persistent data storage
- **Pre-populated Checklist**: 29 standard DD items across 8 categories
- **Automatic Timestamps**: Track when items were last updated
- **Property Name Management**: Customize for each acquisition

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Navigate to the application directory:**
   ```bash
   cd dd_tracker
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

2. **Access the application:**
   - The app will automatically open in your default web browser
   - Default URL: `http://localhost:8501`

3. **First-time setup:**
   - The database will be automatically created with pre-populated DD items
   - Update the "Property Name" field on the Dashboard to match your acquisition

## Usage Guide

### Dashboard
1. **Update Property Name**: Enter the property address or name in the text field at the top
2. **Monitor Progress**: View overall completion percentage and visual progress chart
3. **Review Flagged Issues**: Check the flagged issues section for items requiring attention
4. **Track Deadlines**: View items due in the next 7 days
5. **Category Progress**: Expand categories to see detailed status breakdowns

### Detail View
1. **Filter Items**: Use the dropdown filters to view specific categories or statuses
2. **Edit Items**: Click the ✏️ button next to any item to update its details
3. **Add New Items**: Click "➕ Add New Item" to create custom checklist items
4. **Update Status**: Change item status as work progresses
5. **Assign Responsibility**: Enter the name or team responsible for each item
6. **Set Deadlines**: Assign due dates to track timeline
7. **Add Notes**: Include relevant details, findings, or action items

### Reports
1. **Generate Report**: Click "📊 Generate Report" to create a current status report
2. **Review Content**: Preview the Markdown-formatted report
3. **Download**: Use "⬇️ Download Report" to save the report to your computer
4. **Share**: Share the downloaded Markdown file with stakeholders

## Due Diligence Categories

The application comes pre-populated with items across these categories:

1. **Title & Survey** (4 items)
   - Title Commitment Review, ALTA Survey, Zoning Report, Title Policy Review

2. **Environmental** (5 items)
   - Phase I ESA, Phase II ESA, Asbestos Survey, Environmental Compliance, Wetlands Delineation

3. **Zoning** (3 items)
   - Zoning Compliance Verification, Certificate of Occupancy, Parking Requirements

4. **Financial** (4 items)
   - Rent Roll Verification, Operating Statements, Tax Bills, Utility Bills Analysis

5. **Lease Review** (3 items)
   - Estoppel Certificates, Lease Abstraction, SNDA Agreements

6. **Physical/Engineering** (4 items)
   - Property Condition Assessment, Roof Inspection, HVAC Review, ADA Compliance

7. **Legal** (3 items)
   - Purchase Agreement Review, Entity Formation, Service Contracts Review

8. **Insurance** (2 items)
   - Insurance Quotes, Loss Runs Review

## Status Definitions

- **Not Started**: Item has not been initiated
- **In Progress**: Work is actively underway
- **Under Review**: Item completed and under review/approval
- **Complete**: Item fully completed and approved
- **Issue Flagged**: Item requires immediate attention or has identified problems

## Data Persistence

- All data is stored in a SQLite database (`dd_tracker.db`)
- The database file is created automatically in the application directory
- Database includes automatic timestamp tracking for all updates
- To reset the application, delete the `dd_tracker.db` file and restart

## Customization

### Adding Custom Categories
When adding a new item, you can:
1. Select an existing category from the dropdown
2. Enter a custom category name in the "Or enter new category" field

### Modifying Pre-populated Items
Edit any pre-populated item through the Detail View to match your specific requirements.

### Due Date Management
Due dates are automatically set to reasonable timelines but can be adjusted based on your acquisition timeline.

## Tips for Best Practices

1. **Update Regularly**: Keep item statuses current to maintain accurate progress tracking
2. **Use Notes Field**: Document key findings, issues, or next steps in the notes field
3. **Flag Issues Early**: Mark items as "Issue Flagged" as soon as problems are identified
4. **Assign Responsibility**: Always assign a responsible party to ensure accountability
5. **Set Realistic Deadlines**: Adjust due dates based on your actual closing timeline
6. **Generate Reports Frequently**: Create weekly reports to track progress and communicate with stakeholders
7. **Review Dashboard Daily**: Check the dashboard each day during active DD period

## Technical Details

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Database**: SQLite3
- **Visualization**: Plotly
- **Data Processing**: Pandas

### File Structure
```
dd_tracker/
├── app.py              # Main Streamlit application
├── database.py         # Database operations and queries
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── dd_tracker.db      # SQLite database (created on first run)
```

### Database Schema

**dd_items table:**
- id (INTEGER PRIMARY KEY)
- category (TEXT)
- item_name (TEXT)
- status (TEXT)
- responsible_party (TEXT)
- due_date (TEXT)
- notes (TEXT)
- last_updated (TIMESTAMP)

**property_info table:**
- id (INTEGER PRIMARY KEY)
- property_name (TEXT)
- last_updated (TIMESTAMP)

## Troubleshooting

### Application won't start
- Verify Python 3.8+ is installed: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're in the correct directory: `pwd` (should show the dd_tracker folder)

### Database errors
- Delete the `dd_tracker.db` file and restart the application to recreate it
- Ensure you have write permissions in the application directory

### Port already in use
- Streamlit default port (8501) is already in use
- Run with a different port: `streamlit run app.py --server.port 8502`

### Items not saving
- Check browser console for errors
- Ensure the database file is not locked by another process
- Restart the application

## Support and Feedback

This application is designed to be intuitive and user-friendly. For additional assistance:
- Review this README thoroughly
- Check the Streamlit documentation: https://docs.streamlit.io
- Ensure all required fields are filled when adding/editing items

## Version History

**v1.0** - Initial Release
- Complete dashboard with progress visualization
- Detailed item management with filtering
- Report generation and export
- Pre-populated standard DD checklist
- SQLite database integration

## License

This application is provided as-is for commercial real estate due diligence tracking purposes.

---

**Built with Streamlit** | **Designed for CRE Professionals**
