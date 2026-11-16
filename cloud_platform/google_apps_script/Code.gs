/**
 * RubberGuard AI — Independent Google Form Feedback Verification Script
 *
 * Instructions:
 * 1. Create a Google Form with questions matching the evaluation rubric.
 * 2. Ensure Question 1 or a dedicated field is: "Verification Code (RG-XXXXXX)".
 * 3. Open responses sheet -> Extensions -> Apps Script.
 * 4. Paste this code into Code.gs.
 * 5. Update RUBBERGUARD_API_URL with your hosted backend URL.
 * 6. Set up an installable trigger: Edit -> Current project's triggers -> Add Trigger -> onFormSubmit -> From spreadsheet -> On form submit.
 */

// Replace with your active cloud backend URL (e.g. https://rubberguard-ai.onrender.com or http://your-ip:5000)
var RUBBERGUARD_API_URL = "http://localhost:5000";

function onFormSubmit(e) {
  if (!e || !e.values) {
    Logger.log("No form event values received.");
    return;
  }

  var sheet = e.range.getSheet();
  var row = e.range.getRow();
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  // Find column indexes
  var codeColIndex = -1;
  var ratingColIndex = -1;
  var easeColIndex = -1;
  var accuracyColIndex = -1;
  var commentsColIndex = -1;
  var statusColIndex = -1;
  var reasonColIndex = -1;

  for (var i = 0; i < headers.length; i++) {
    var header = headers[i].toString().toLowerCase();
    if (header.indexOf("code") !== -1 || header.indexOf("verification") !== -1) {
      codeColIndex = i + 1;
    } else if (header.indexOf("rating") !== -1 || header.indexOf("overall") !== -1) {
      ratingColIndex = i + 1;
    } else if (header.indexOf("ease") !== -1) {
      easeColIndex = i + 1;
    } else if (header.indexOf("accuracy") !== -1) {
      accuracyColIndex = i + 1;
    } else if (header.indexOf("comment") !== -1 || header.indexOf("observation") !== -1 || header.indexOf("suggestion") !== -1) {
      commentsColIndex = i + 1;
    } else if (header.indexOf("verification status") !== -1) {
      statusColIndex = i + 1;
    } else if (header.indexOf("status reason") !== -1) {
      reasonColIndex = i + 1;
    }
  }

  // If status columns don't exist yet, create them dynamically
  if (statusColIndex === -1) {
    statusColIndex = headers.length + 1;
    sheet.getRange(1, statusColIndex).setValue("Verification Status").setFontWeight("bold");
  }
  if (reasonColIndex === -1) {
    reasonColIndex = statusColIndex + 1;
    sheet.getRange(1, reasonColIndex).setValue("Status Reason").setFontWeight("bold");
  }

  // Extract verification code from row
  var submittedCode = codeColIndex !== -1 ? sheet.getRange(row, codeColIndex).getValue().toString().trim().toUpperCase() : "";
  var ratingValue = ratingColIndex !== -1 ? parseInt(sheet.getRange(row, ratingColIndex).getValue(), 10) || 5 : 5;
  var easeValue = easeColIndex !== -1 ? sheet.getRange(row, easeColIndex).getValue().toString() : "Easy";
  var accuracyValue = accuracyColIndex !== -1 ? sheet.getRange(row, accuracyColIndex).getValue().toString() : "Accurate";
  var commentsValue = commentsColIndex !== -1 ? sheet.getRange(row, commentsColIndex).getValue().toString() : "";

  if (!submittedCode) {
    sheet.getRange(row, statusColIndex).setValue("INVALID").setBackground("#ffcdd2");
    sheet.getRange(row, reasonColIndex).setValue("Missing verification code in submission");
    return;
  }

  // Call RubberGuard Cloud Verification API
  try {
    var payload = {
      verificationCode: submittedCode,
      rating: ratingValue,
      easeOfUse: easeValue,
      diseaseAccuracy: accuracyValue,
      comments: commentsValue,
      rawAnswers: e.namedValues || {}
    };

    var options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch(RUBBERGUARD_API_URL + "/api/feedback/verify", options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    var result = JSON.parse(responseText);

    if (result.verificationStatus === "VERIFIED") {
      sheet.getRange(row, statusColIndex).setValue("VERIFIED").setBackground("#c8e6c9").setFontColor("#1b5e20");
      sheet.getRange(row, reasonColIndex).setValue(result.message || "Valid code linked to accepted leaf scan");
    } else {
      sheet.getRange(row, statusColIndex).setValue("INVALID").setBackground("#ffcdd2").setFontColor("#b71c1c");
      sheet.getRange(row, reasonColIndex).setValue(result.reason || "Verification code rejected by backend");
    }
  } catch (error) {
    Logger.log("API Connection Error: " + error.toString());
    sheet.getRange(row, statusColIndex).setValue("ERROR").setBackground("#fff9c4");
    sheet.getRange(row, reasonColIndex).setValue("Server error: " + error.toString());
  }
}