# Web UI User Guide

The Nexus Dashboard MCP Server includes a modern web interface for managing clusters, security settings, and viewing audit logs.

## Getting Started

### Running the Web UI

1. Start the entire stack with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Access the web UI at:
   ```
   http://localhost:3000
   ```

### Development Mode

For development with hot reload:

```bash
cd web-ui
npm install
npm run dev
```

## Features Overview

### Dashboard (Home Page)

The main dashboard provides:
- Quick statistics overview
- Total operations count
- Number of configured clusters
- Audit logs count
- Edit mode status indicator
- Quick links to all management pages

### Clusters Management

**Path:** `/clusters`

Manage Nexus Dashboard cluster connections with full CRUD operations:

#### Features
- **View All Clusters**: Table view showing name, URL, username, status, and SSL verification
- **Add New Cluster**: Click "Add New Cluster" button to open the creation form
- **Edit Cluster**: Click "Edit" on any cluster to modify settings
- **Delete Cluster**: Click "Delete" with confirmation dialog
- **Test Connection**: Click "Test" to verify cluster connectivity

#### Adding a Cluster

1. Click "Add New Cluster"
2. Fill in the form:
   - **Cluster Name**: Unique identifier (cannot be changed later)
   - **URL**: Full URL to Nexus Dashboard (e.g., `https://nexus.example.com`)
   - **Username**: Admin username
   - **Password**: Admin password (stored securely in Vault)
   - **Verify SSL**: Check to validate SSL certificates
3. Click "Add Cluster"

#### Editing a Cluster

1. Click "Edit" on the cluster row
2. Update any field except the cluster name
3. Leave password blank to keep the existing password
4. Click "Update Cluster"

#### Status Indicators

- **Active**: Green - Cluster is configured and accessible
- **Inactive**: Gray - Cluster is configured but not in use
- **Error**: Red - Last connection attempt failed

### Security Dashboard

**Path:** `/security`

Configure security policies and edit mode:

#### Edit Mode Toggle

- **Enabled**: Allows write operations (POST, PUT, DELETE)
- **Disabled**: All operations are read-only
- Visual warning when enabling edit mode
- Toggle switch provides immediate feedback

#### Read-Only Operations

Configure operations that should always be read-only, even when edit mode is enabled:

1. Enter operation ID in the input field
2. Click "Add" or press Enter
3. Operations appear as blue tags
4. Click the × on any tag to remove it

**Example use case:** Force operations like `get-sites`, `list-fabrics` to always be read-only.

#### Blocked Operations

Configure operations that are completely blocked:

1. Enter operation ID in the input field
2. Click "Add" or press Enter
3. Operations appear as red tags
4. Click the × on any tag to remove it

**Example use case:** Block dangerous operations like `delete-site`, `remove-tenant`.

#### Configuration Management

- Changes are tracked in real-time
- "Unsaved changes" banner appears when modifications are made
- Click "Save Configuration" to persist changes
- Click "Discard Changes" to revert to saved configuration
- Success/error messages provide feedback

### Audit Log Viewer

**Path:** `/audit`

View and analyze operation history:

#### Statistics Dashboard

Four key metrics displayed at the top:
- **Total Operations**: All logged operations
- **Successful**: Operations with 2xx status codes (with percentage)
- **Failed**: Operations with 4xx/5xx status codes (with percentage)
- **Most Used Method**: HTTP method with highest usage count

#### Filtering

Apply filters to narrow down results:

- **Cluster Name**: Filter by specific cluster
- **HTTP Method**: GET, POST, PUT, DELETE, PATCH
- **Status Code**: Specific HTTP status code (200, 404, etc.)
- **Start Date**: Filter operations after this date
- **End Date**: Filter operations before this date

Click "Apply Filters" to refresh the results.
Click "Clear All" to reset all filters.

#### Audit Log Table

Displays detailed information for each operation:

- **Timestamp**: When the operation occurred
- **Cluster**: Which cluster was accessed
- **Method**: HTTP method (color-coded)
  - Blue: GET
  - Green: POST
  - Yellow: PUT
  - Red: DELETE
  - Purple: PATCH
- **Endpoint**: API endpoint path
- **Operation**: Operation ID
- **Status**: HTTP status code (color-coded)
  - Green: 2xx (success)
  - Yellow: 4xx (client error)
  - Red: 5xx (server error)
- **Error**: Error message if operation failed

#### Pagination

- 50 items per page
- Navigation controls at bottom of table
- Shows current range (e.g., "Showing 1 to 50 of 237 results")
- Click page numbers or Previous/Next buttons

#### Export to CSV

1. Apply any filters you want
2. Click "Export to CSV" button
3. File downloads automatically with timestamp in filename
4. CSV includes all filtered results (not just current page)

## Navigation

The top navigation bar is consistent across all pages:

- **Nexus Dashboard MCP Server** (logo/home link)
- **Dashboard**: Overview and statistics
- **Clusters**: Cluster management
- **Security**: Security settings
- **Audit Logs**: Operation history

Active page is highlighted for easy orientation.

## Responsive Design

The UI is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

Navigation collapses on smaller screens for better usability.

## Error Handling

The UI provides clear error messages for:
- Network connectivity issues
- Invalid form input
- Server-side validation errors
- Failed API operations

Errors are displayed at the top of each page with clear descriptions and can be dismissed.

## Loading States

All pages show loading spinners during:
- Initial data fetch
- Form submissions
- Delete operations
- Connection tests
- Filter applications

## Best Practices

### Cluster Management
1. Always test connections after adding/editing clusters
2. Use descriptive cluster names
3. Enable SSL verification for production environments
4. Document cluster credentials in your organization's secure vault

### Security Settings
1. Keep edit mode disabled unless actively making changes
2. Be conservative with blocked operations
3. Review read-only operations regularly
4. Test security settings in development first

### Audit Logs
1. Export logs regularly for compliance
2. Use filters to investigate specific issues
3. Monitor failed operations for security concerns
4. Check statistics dashboard for health trends

## Technical Details

### Architecture
- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **API Client**: Axios
- **Build**: Static Site Generation (SSG)

### API Integration
All pages communicate with the FastAPI backend at `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`).

### Security
- No authentication required (add your own auth layer if needed)
- HTTPS recommended for production
- Credentials stored in Vault, not in browser
- No sensitive data in client-side code

### Performance
- Static page generation for fast loading
- Client-side rendering for interactivity
- Optimized bundle size
- Efficient re-renders with React hooks

## Troubleshooting

### Web UI won't load
- Check if Docker containers are running: `docker-compose ps`
- Verify port 3000 is not in use: `lsof -i :3000`
- Check browser console for errors

### API requests fail
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` environment variable
- Verify network connectivity
- Review browser network tab for details

### Data not updating
- Hard refresh the page (Cmd+Shift+R / Ctrl+Shift+R)
- Check browser console for errors
- Verify API endpoints are responding

### Build fails
- Run `npm install` to ensure dependencies are installed
- Check for TypeScript errors: `npm run build`
- Verify Node.js version (18+ required)

## Customization

### Changing the API URL

Edit `web-ui/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### Styling

All components use Tailwind CSS. Modify `web-ui/src/app/globals.css` for global styles or component files for specific changes.

### Adding New Pages

1. Create a new file in `web-ui/src/app/[page-name]/page.tsx`
2. Import and use the `Navigation` component
3. Add link to Navigation component if needed
4. Follow existing patterns for consistency

## Support

For issues or questions:
- Check the logs: `docker-compose logs web-ui`
- Review API documentation: `/docs/API_REFERENCE.md`
- Check backend health: `http://localhost:8000/health`
