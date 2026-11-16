package com.rubber.disease.utils

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import com.rubber.disease.data.ScanRecordEntity
import com.rubber.disease.data.UserEntity
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object CloudSyncHelper {

    private const val TAG = "CloudSyncHelper"
    private const val PREFS_NAME = "rubber_guard_prefs"
    private const val KEY_SERVER_URL = "cloud_server_url"
    private const val KEY_AUTH_TOKEN = "cloud_auth_token"
    private const val KEY_LATEST_CODE = "latest_verification_code"

    // Default development and local fallback URL
    private const val DEFAULT_SERVER_URL = "https://rubberguard-ai.onrender.com"

    fun getServerUrl(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
    }

    fun setServerUrl(context: Context, url: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_SERVER_URL, url.trim().removeSuffix("/")).apply()
    }

    fun getAuthToken(context: Context): String? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_AUTH_TOKEN, null)
    }

    fun setAuthToken(context: Context, token: String?) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }

    fun getLatestVerificationCode(context: Context): String? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_LATEST_CODE, null)
    }

    fun setLatestVerificationCode(context: Context, code: String?) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_LATEST_CODE, code).apply()
    }

    fun isOnline(context: Context): Boolean {
        return try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = cm.activeNetwork ?: return false
            val capabilities = cm.getNetworkCapabilities(network) ?: return false
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
        } catch (e: Exception) {
            false
        }
    }

    data class CloudAuthResult(
        val success: Boolean,
        val token: String? = null,
        val user: UserEntity? = null,
        val errorMessage: String? = null
    )

    data class SyncResult(
        val success: Boolean,
        val scanStatus: String = "ACCEPTED",
        val verificationCode: String? = null,
        val errorMessage: String? = null
    )

    // Authenticate with Cloud backend
    fun loginCloud(context: Context, identifier: String, passwordPlain: String): CloudAuthResult {
        if (!isOnline(context)) {
            return CloudAuthResult(success = false, errorMessage = "Offline mode active")
        }

        return try {
            val baseUrl = getServerUrl(context)
            val url = URL("$baseUrl/api/auth/login")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.connectTimeout = 4000
            conn.readTimeout = 4000
            conn.doOutput = true

            val json = JSONObject().apply {
                put("identifier", identifier)
                put("password", passwordPlain)
            }

            OutputStreamWriter(conn.outputStream).use { it.write(json.toString()) }

            val responseCode = conn.responseCode
            val inputStream = if (responseCode in 200..299) conn.inputStream else conn.errorStream
            val responseText = BufferedReader(InputStreamReader(inputStream)).use { it.readText() }

            val resObj = JSONObject(responseText)
            if (responseCode in 200..299 && resObj.optBoolean("success", false)) {
                val token = resObj.optString("token")
                val userObj = resObj.optJSONObject("user")
                setAuthToken(context, token)

                val userEntity = UserEntity(
                    username = userObj?.optString("username", identifier) ?: identifier,
                    email = userObj?.optString("email", "") ?: "",
                    passwordHash = "",
                    fullName = userObj?.optString("fullName", identifier) ?: identifier,
                    phone = userObj?.optString("phone", "") ?: "",
                    location = userObj?.optString("location", "") ?: ""
                )
                CloudAuthResult(success = true, token = token, user = userEntity)
            } else {
                val err = resObj.optString("error", "Invalid credentials")
                CloudAuthResult(success = false, errorMessage = err)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Cloud login failed (fallback to offline): ${e.message}")
            CloudAuthResult(success = false, errorMessage = e.message)
        }
    }

    // Synchronize scan record with Cloud backend
    fun syncScan(context: Context, record: ScanRecordEntity, uniqueScanId: String): SyncResult {
        if (!isOnline(context)) {
            return SyncResult(success = false, errorMessage = "Offline: Scan saved locally")
        }

        return try {
            val baseUrl = getServerUrl(context)
            val token = getAuthToken(context)
            val url = URL("$baseUrl/api/scans/sync")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            if (!token.isNullOrEmpty()) {
                conn.setRequestProperty("Authorization", "Bearer $token")
            }
            conn.connectTimeout = 5000
            conn.readTimeout = 5000
            conn.doOutput = true

            val json = JSONObject().apply {
                put("scanId", uniqueScanId)
                put("timestamp", record.dateString)
                put("predictedDisease", record.diseaseName)
                put("confidence", record.confidence.toDouble())
                put("severityLabel", record.severityLabel)
                put("severityPercentage", record.severityPercentage.toDouble())
                put("modelVersion", "MobileNetV2-1.0")
                put("appVersion", "1.0")
                put("platform", "ANDROID")
                put("farmerName", record.farmerName)
            }

            OutputStreamWriter(conn.outputStream).use { it.write(json.toString()) }

            val responseCode = conn.responseCode
            val inputStream = if (responseCode in 200..299) conn.inputStream else conn.errorStream
            val responseText = BufferedReader(InputStreamReader(inputStream)).use { it.readText() }

            val resObj = JSONObject(responseText)
            if (responseCode in 200..299 && resObj.optBoolean("success", false)) {
                val scanStatus = resObj.optString("scanStatus", "ACCEPTED")
                val codeRaw = resObj.optString("verificationCode", "")
                val code = if (codeRaw.isNotEmpty() && codeRaw != "null") codeRaw else null
                if (!code.isNullOrEmpty()) {
                    setLatestVerificationCode(context, code)
                }
                SyncResult(
                    success = true,
                    scanStatus = scanStatus,
                    verificationCode = code
                )
            } else {
                SyncResult(
                    success = false,
                    errorMessage = resObj.optString("error", "Scan sync rejected")
                )
            }
        } catch (e: Exception) {
            Log.w(TAG, "Scan sync failed: ${e.message}")
            SyncResult(success = false, errorMessage = e.message)
        }
    }
}