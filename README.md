# Event Scheduler-agent
# 🤖 AI-Driven Learning Orchestrator (Capstone Project)

## Project Overview
This project implements a fully autonomous AI Agent that automatically generates a personalized daily learning plan. It integrates a user's calendar, searches for hands-on code examples on GitHub, and sends the final, actionable plan via SMS.

## ✨ Core Features
* **Daily Schedule Fetching:** Retrieves all learning events from a configured Google Calendar.
* **Intelligent Resource Curation:** A custom **FastAPI MCP Server** searches GitHub and scores repositories based on a custom "hands-on" metric (tutorials, examples, high star/fork count).
* **Gemini Agent Orchestration:** Uses **Gemini's Function Calling** to manage the multi-step reasoning flow (Fetch -> Search -> Synthesize -> Notify).
* **Mobile Delivery:** Utilizes **Twilio** to deliver the final concise plan directly to the user's phone.

## ⚙️ Architecture

The system is a three-way integration orchestrated by the Gemini Agent:


## 🚀 Setup and Installation

### 1. Prerequisites
* Python 3.9+
* Twilio Account (for SMS)
* Google Cloud Project (for Gemini API and Calendar API access)
* A GitHub Personal Access Token (PAT)

### 2. Environment Variables

Create a `.env` file in the root directory and populate it:

```env
# Gemini API Key
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Twilio Credentials (for Tool 3: Notification)
TWILIO_ACCOUNT_SID="ACxxx"
TWILIO_AUTH_TOKEN="YOUR_AUTH_TOKEN"
TWILIO_PHONE_NUMBER="+1800..." # Your Twilio phone number
LEARNER_PHONE_NUMBER="+1555..." # Recipient phone number

# GitHub MCP Credentials (for Tool 2: Search)
GITHUB_TOKEN="YOUR_READ_ONLY_GITHUB_PAT" 
GITHUB_MCP_URL="http://localhost:8000/recommendation"

# Google Calendar (for Tool 1: Calendar Fetcher)
# Ensure your Service Account JSON file path is correct
GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE="./credentials.json"
LEARNING_CALENDAR_ID="your_calendar_id@group.calendar.google.com"