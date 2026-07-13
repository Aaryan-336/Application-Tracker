# Design.md

## Product Vision

A mobile-first AI Career Agent for a small group of users that discovers
jobs, matches them against resumes, tracks applications, analyzes
skills, and improves job search outcomes over time.

## Design Principles

-   Mobile-first responsive design.
-   PWA support for installable app experience.
-   Minimal clicks to apply for jobs.
-   Dashboard-driven workflow.
-   User-specific data isolation.
-   Dark mode by default with light mode support.

## Main Screens

### Authentication

-   Login
-   Register
-   Google OAuth
-   Forgot Password

### Onboarding

-   Upload Resume
-   Select Preferred Roles
-   Preferred Locations
-   Salary Expectations
-   Auto Apply Settings

### Dashboard

-   Jobs Found Today
-   Applications Sent
-   Interviews Scheduled
-   Match Rate
-   Response Rate

### Jobs Page

-   Match Score
-   Skills Match Breakdown
-   Apply Button
-   Save Job
-   Ignore Job

### Applications Page

Kanban style stages: - Discovered - Applied - Assessment - Interview -
Offer - Rejected

### Skills Intelligence

-   Current Skills
-   Missing Skills
-   Market Demand
-   Learning Recommendations

### Settings

-   Resume Management
-   Gmail Integration
-   Notification Preferences
-   Auto Apply Controls

## UI Stack

-   shadcn/ui
-   Tailwind CSS
-   Framer Motion
-   Responsive Cards
-   Bottom Navigation for Mobile
