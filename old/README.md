# Ratlam Relay Centre - Webinar Access Portal

A Flask web application designed to provide authorized access to webinar streams for registered ITS members. This application features user authentication via ITS ID, session management, and an admin panel for managing authorized users.

## Features

- **User Authentication**: Users can log in using their unique 8-digit ITS ID.
- **Session Management**: Tracks active user sessions and ensures secure access.
- **Admin Panel**: Allows administrators to manage authorized users and webinar settings.
- **Webinar Access**: Provides access to a webinar stream embedded from YouTube with detailed information such as title, description, date, time, and speaker.
- **Data Storage**: Stores ITS IDs, active sessions, admin credentials, and webinar settings in JSON files.

## Installation

1. **Prerequisites**:
   - Python 3.6 or higher
   - Flask
   - Other dependencies (if any)

2. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

3. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize Data Files**:
   - Ensure all required data files are initialized by running the `init_files()` function in the application.

6. **Set Admin Credentials**:
   - Set the admin credentials in the `admin_credentials.json` file.

## Usage

1. **Running the Application**:
   - Start the Flask development server by running:
     ```bash
     python app.py
     ```
   - Access the application through a web browser at `http://localhost:5000`.

2. **User Access**:
   - Navigate to the home page and enter your ITS ID to log in.
   - Access the webinar stream and related information.

3. **Admin Access**:
   - Navigate to the admin login page and enter the admin credentials.
   - Use the admin dashboard to manage ITS IDs and webinar settings.

## Routes

- `/`: Home page and login route.
- `/webinar`: Webinar page that requires a valid session.
- `/logout`: Logout route to clear the session.
- `/admin/login`: Admin login route.
- `/admin/logout`: Admin logout route.
- `/admin/dashboard`: Admin dashboard to manage ITS IDs and webinar settings.
- `/admin/add_its`: Add a single ITS ID.
- `/admin/add_bulk_its`: Add multiple ITS IDs from a textarea.
- `/admin/delete_its`: Delete a specific ITS ID.
- `/admin/delete_all_its`: Delete all ITS IDs.
- `/admin/clear_sessions`: Clear all active sessions.
- `/admin/update_webinar_settings`: Update webinar settings.
- `/health`: Health check endpoint for monitoring.
- `/api/status`: API endpoint to check login status.

## Data Files

- `its_ids.json`: Stores authorized ITS IDs.
- `active_sessions.json`: Stores active user sessions.
- `admin_credentials.json`: Stores admin credentials.
- `webinar_settings.json`: Stores webinar settings such as the embed URL, title, description, etc.
