# Belong — Project Details and User Flow

Belong is a Django-based campus lost-and-found platform. Users can publish lost or found item reports, discover possible matches, submit ownership claims, and complete a supervised handoff.

## Technology

- **Backend:** Python and Django
- **Frontend:** Django templates, HTML, CSS, and JavaScript
- **Database:** SQLite for local development; PostgreSQL-compatible configuration is supported
- **Authentication:** Django's built-in `User` model
- **Uploads:** Item photographs, claim evidence, and profile avatars
- **Applications:** `accounts`, `items`, and `claims`

## Project Structure

```text
Belong/
├── manage.py
├── config/                  # Django settings, URLs, ASGI, and WSGI
├── accounts/                # Authentication, profiles, dashboards, notifications
├── items/                   # Lost/found reports, search, ownership, custody
├── claims/                  # Claims, reviews, OTP, signatures, audit logs
├── templates/               # Shared and application templates
├── static/                  # CSS and JavaScript
├── media/                   # Uploaded files
├── db.sqlite3               # Local development database
├── requirements.txt
└── manage.py
```

## Main Data Models

### User and UserProfile

Every authenticated user has a Django `User` account and a related profile.

Profile roles:

- `student`
- `faculty`
- `desk_admin`

The Django `is_staff` flag also grants administrative access.

### Item

An item report contains:

- Title
- Type: `lost` or `found`
- Category and campus location
- Incident date and specific spot
- Public description
- Confidential identifying details
- Optional image
- Reporter/owner
- Physical holding location
- Current status

Item statuses:

1. `active`
2. `claim_pending`
3. `handoff_ready`
4. `returned`
5. `archived`

### Claim

A claim belongs to one found item and one claimant. It contains:

- Ownership explanation
- Optional proof image
- Review status
- Review notes
- Reviewer
- Review timestamp

Claim statuses:

1. `pending`
2. `approved`
3. `rejected`
4. `completed`

### HandoffOTP and HandoffAuditLog

Approved claims can use:

- A time-limited six-digit OTP, or
- A recorded signature confirmation

Each completed handoff creates an audit record containing the item, claim, recipient, confirming user, date, and notes.

## User Roles and Permissions

### User A — Lost-item owner

User A can:

- Create a lost-item report
- View the public report
- Edit their own report
- Delete their own report
- View confidential details for their own report
- Receive notifications about possible matching found reports
- Submit a claim against a matching found report
- View their own claim and its status

User A cannot approve their own claim. The claim must be reviewed by the finder or an authorized desk officer.

### User B — Finder

User B can:

- Create a found-item report
- View public listings
- View and manage their own found report
- See claims submitted against their own found report
- Review, approve, or reject claims on their report
- Verify an approved handoff using OTP or signature

User B cannot:

- Edit User A's report
- Delete User A's report
- View User A's private contact information
- Approve a claim submitted by User B

### User C — General browser

User C can:

- Browse public listings
- Search and filter reports
- View public item details
- See public matching suggestions

User C cannot modify another user's item, review claims, or view private verification details.

### Admin / Campus Desk Officer

An admin is either:

- A Django user with `is_staff=True`, or
- A user whose profile role is `desk_admin`

Admins can:

- Access the admin dashboard and campus desk
- Review claims when the finder cannot do so
- Approve or reject pending claims
- Verify OTP or signature handoffs
- View confidential identifying details
- Manage aged or archived items
- Edit or delete listings when intervention is required
- Record disposal or archival actions

Admins are trusted supervisors. They are not required for every normal exchange, because the finder can review claims directly.

## Complete Lost-to-Found Flow

### 1. User A reports a lost item

1. User A signs in.
2. User A opens **Report Item**.
3. User A selects `Lost`.
4. User A enters the title, category, location, date, description, and optional confidential details.
5. The report is saved with User A as the reporter and `active` as its status.
6. The report appears on the public listings page.

### 2. User B reports a found item

1. User B signs in.
2. User B opens **Report Item**.
3. User B selects `Found`.
4. User B enters the found item's details and holding location.
5. The report is saved with User B as the reporter.
6. The system compares the found report with active lost reports using category and/or location.
7. Matching lost-report owners receive an in-app notification containing a link to the found listing.

The notification does not expose private phone numbers, email addresses, or confidential identifying details.

### 3. User A reviews the possible match

1. User A opens the notification.
2. User A views the public details of User B's found report.
3. User A does not see User B's private contact details or confidential verification details.
4. User A submits an ownership claim with proof and explanation.
5. The claim is saved as `pending`.
6. The found item changes from `active` to `claim_pending`.
7. User B receives a claim-submitted notification.

### 4. User B reviews the claim

1. User B opens the claim from the notification or dashboard.
2. User B compares the claim evidence with the private identifying details.
3. User B chooses **Approve** or **Reject**.

If approved:

- The claim becomes `approved`.
- The found item becomes `handoff_ready`.
- A six-digit OTP is generated.
- The claimant receives an approval notification.

If rejected:

- The claim becomes `rejected`.
- The claimant receives a rejection notification.
- The item returns to `active` when no other pending or approved claims remain.

### 5. Handoff and return

The finder or admin completes one of the following:

#### OTP handoff

1. User A presents the OTP during pickup.
2. User B or an admin enters the OTP.
3. The system checks that the OTP exists, is unused, and has not expired.
4. The claim becomes `completed`.
5. The item becomes `returned`.
6. The OTP is marked used.
7. An audit log is created.
8. User A receives an item-returned notification.

#### Signature handoff

1. User B or an admin confirms the recipient's identity.
2. The recipient name and handoff notes are recorded.
3. The claim becomes `completed`.
4. The item becomes `returned`.
5. An audit log is created.

## Privacy and Security Rules

- Public pages show only public item descriptions.
- Confidential identifying details are visible only to the reporter and authorized desk users.
- Claims are visible only to the claimant, the item reporter/finder, and authorized desk users.
- Users cannot edit or delete reports owned by another user.
- Claimants cannot approve their own claims.
- Handoff verification is restricted to the finder or an authorized admin.
- OTP verification prevents reuse and rejects expired codes.
- Item deletion requires a POST request from the confirmation page.
- Uploaded image files are subject to configured size limits.

## Notifications

The system supports notifications for:

- A new claim submitted on a user's found report
- A matching found report for a user's lost report
- An approved claim
- A rejected claim
- A completed item return

Notifications are available through the user's notification page and may link to the related item or claim.

## Search and Matching

The public board supports:

- Keyword search
- Lost/found type filtering
- Category filtering
- Campus location filtering
- Incident date ranges
- Aging filters
- Newest and oldest sorting

Item detail pages provide matching suggestions based on:

- Same category
- Same location
- Incident dates within seven days

## Admin and Campus Desk Workflow

The campus desk is used for operational supervision:

1. Review aged active reports.
2. Review items waiting for handoff.
3. Review recently returned items.
4. Archive or dispose of unclaimed items.
5. Record the disposal action and notes.
6. Review claims and handoff audit history.

## Important URLs

### Items

- `/` — Public listings
- `/item/<id>/` — Item details
- `/report/` — Create a report
- `/item/<id>/edit/` — Edit an owned report
- `/item/<id>/delete/` — Delete an owned report
- `/desk/` — Admin/campus desk

### Claims

- `/claims/item/<item_id>/claim/` — Submit a claim
- `/claims/claim/<id>/` — View a claim
- `/claims/claim/<id>/review/` — Review a claim
- `/claims/claim/<id>/verify-otp/` — Verify OTP handoff
- `/claims/claim/<id>/verify-signature/` — Complete signature handoff

## Local Development

From the `Belong` directory:

```powershell
python manage.py migrate
python manage.py runserver
python manage.py test
```

Optional demo data can be loaded with:

```powershell
python manage.py seed_demo_data
```

## Validation Status

The current implementation includes automated coverage for:

- Authentication and registration
- Public item browsing and search
- Item creation
- Ownership privacy
- Cross-user edit/delete protection
- Matching found-report notifications
- Claim submission
- Claim approval and rejection
- OTP handoff
- Signature handoff
- OTP reuse and expiry protection
- Admin and campus desk authorization

The complete Django test suite currently passes.
