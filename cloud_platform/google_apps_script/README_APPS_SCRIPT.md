# RubberGuard AI — Google Form Evaluation & Verification Guide

This document explains how to set up the independent Google Form for the final-year project evaluation of **RubberGuard AI**, link it to Google Sheets, and attach the Google Apps Script webhook to automatically verify that every submitted response is from an authenticated tester who completed an actual leaf disease scan.

---

## 1. Create the Google Form

1. Go to [Google Forms](https://forms.google.com/) and create a new form titled:
   **"RubberGuard AI — Rubber Leaf Disease Classification Evaluation"**
2. Add the following questions:
   - **Question 1 (Mandatory Short Answer):**
     `Verification Code (RG-XXXXXX)`
     Description: *Paste your single-use verification code generated in the RubberGuard Android app or web tester portal.*
   - **Question 2 (Linear Scale 1 to 5):**
     `Overall Evaluation Rating` (1 = Poor, 5 = Excellent)
   - **Question 3 (Multiple Choice):**
     `Ease of Use & Diagnostic Workflow`
     Options: Very Easy, Easy, Neutral, Difficult
   - **Question 4 (Multiple Choice):**
     `Disease Classification Accuracy`
     Options: Highly Accurate, Mostly Accurate, Moderate, Inaccurate
   - **Question 5 (Multiple Choice):**
     `Usefulness of OpenCV Severity % and Grad-CAM Heatmaps`
     Options: Extremely Useful, Helpful, Neutral, Not Useful
   - **Question 6 (Paragraph):**
     `Observations, Feedback, or Local Agricultural Suggestions`

---

## 2. Link Form to Google Sheets

1. In Google Forms, click on the **Responses** tab.
2. Click **Link to Sheets** (or the green Sheets icon) and select **Create a new spreadsheet**.
3. Name it: `RubberGuard AI — User Evaluations (Responses)`.

---

## 3. Add Google Apps Script

1. In the Google Sheet, click **Extensions** -> **Apps Script**.
2. Delete any boilerplate code in `Code.gs`.
3. Copy the full content of `cloud_platform/google_apps_script/Code.gs` and paste it.
4. Replace `RUBBERGUARD_API_URL` at line 13 with your public cloud backend URL:
   ```javascript
   var RUBBERGUARD_API_URL = "https://rubberguard-ai.onrender.com"; // Or your public URL
   ```
5. Click **Save** (disk icon).

---

## 4. Install the Automatic Trigger

1. In the Apps Script left sidebar, click the **Triggers** icon (clock / timer icon).
2. Click **+ Add Trigger** (bottom right).
3. Configure the trigger parameters:
   - **Choose which function to run:** `onFormSubmit`
   - **Choose which deployment should run:** `Head`
   - **Select event source:** `From spreadsheet`
   - **Select event type:** `On form submit`
4. Click **Save**.
5. When prompted, grant Google account permissions (click Advanced -> Go to Untitled project (unsafe) -> Allow).

---

## 5. Verification Workflow & Behavior

- Whenever a tester submits the Google Form:
  1. The script immediately extracts the `RG-XXXXXX` code from the submission row.
  2. It performs an HTTPS POST to `https://<YOUR_BACKEND>/api/feedback/verify`.
  3. The backend validates:
     - Is the code registered in the database?
     - Has the code already been redeemed?
     - Did it originate from an accepted leaf scan?
  4. If valid, the code is atomically marked `USED` and the Google Sheet row is updated:
     - `Verification Status` = **VERIFIED** (highlighted in soft green)
     - `Status Reason` = "Valid code linked to accepted leaf scan"
  5. If invalid or reused:
     - `Verification Status` = **INVALID** (highlighted in soft red)
     - `Status Reason` = Detailed reason (e.g. Code already redeemed or not found)
- The submission is instantly reflected in the **RubberGuard Admin Dashboard**, advancing the target counter (e.g. `13 / 20 Verified Reviewers`).