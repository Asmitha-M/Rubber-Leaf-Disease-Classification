package com.rubber.disease.viewmodels

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.rubber.disease.data.AppDatabase
import com.rubber.disease.data.ScanRecordEntity
import com.rubber.disease.data.ScanRepository
import com.rubber.disease.data.UserEntity
import com.rubber.disease.utils.CloudSyncHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.security.MessageDigest

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val repository: ScanRepository
    
    private val _currentUser = MutableLiveData<UserEntity?>()
    val currentUser: LiveData<UserEntity?> = _currentUser

    private val _scanHistory = MutableLiveData<List<ScanRecordEntity>>()
    val scanHistory: LiveData<List<ScanRecordEntity>> = _scanHistory

    private val _statistics = MutableLiveData<Map<String, Int>>()
    val statistics: LiveData<Map<String, Int>> = _statistics

    init {
        val database = AppDatabase.getDatabase(application)
        repository = ScanRepository(database)
        loadAllRecords()
    }

    private fun hashPassword(password: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(password.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }

    fun login(username: String, passwordPlain: String, onResult: (UserEntity?) -> Unit) {
        viewModelScope.launch {
            // 1. Check local Room DB first
            val localUser = repository.getUserByUsername(username)
            if (localUser != null && localUser.passwordHash == hashPassword(passwordPlain)) {
                _currentUser.postValue(localUser)
                onResult(localUser)
                return@launch
            }

            // 2. If not found locally or credentials mismatch, check Cloud server (if online)
            val cloudRes = withContext(Dispatchers.IO) {
                CloudSyncHelper.loginCloud(getApplication(), username, passwordPlain)
            }
            if (cloudRes.success && cloudRes.user != null) {
                // Cache user in local Room database for offline access
                val cachedUser = UserEntity(
                    username = cloudRes.user.username,
                    email = cloudRes.user.email,
                    passwordHash = hashPassword(passwordPlain),
                    fullName = cloudRes.user.fullName,
                    phone = cloudRes.user.phone,
                    location = cloudRes.user.location
                )
                repository.registerUser(cachedUser)
                val finalUser = repository.getUserByUsername(cloudRes.user.username) ?: cachedUser
                _currentUser.postValue(finalUser)
                onResult(finalUser)
            } else {
                onResult(null)
            }
        }
    }

    fun register(
        username: String,
        email: String,
        passwordPlain: String,
        fullName: String,
        phone: String,
        location: String,
        onResult: (Boolean) -> Unit
    ) {
        viewModelScope.launch {
            val existingUser = repository.getUserByUsername(username)
            val existingEmail = repository.getUserByEmail(email)
            if (existingUser != null || existingEmail != null) {
                onResult(false) // Username or email already exists
            } else {
                val newUser = UserEntity(
                    username = username,
                    email = email,
                    passwordHash = hashPassword(passwordPlain),
                    fullName = fullName,
                    phone = phone,
                    location = location
                )
                repository.registerUser(newUser)
                onResult(true)
            }
        }
    }

    fun loadAllRecords() {
        viewModelScope.launch {
            val records = repository.getAllRecords()
            _scanHistory.postValue(records)
            
            // Calculate statistics
            val stats = mutableMapOf<String, Int>()
            records.forEach { record ->
                val name = record.diseaseName
                stats[name] = stats.getOrDefault(name, 0) + 1
            }
            _statistics.postValue(stats)
        }
    }

    fun saveScanRecord(record: ScanRecordEntity, onComplete: (Long) -> Unit = {}) {
        viewModelScope.launch {
            val id = repository.insertRecord(record)
            loadAllRecords()

            // Background sync to Cloud (if online) to register scan and get verification code
            withContext(Dispatchers.IO) {
                val scanId = "scan_app_${id}_${System.currentTimeMillis()}"
                CloudSyncHelper.syncScan(getApplication(), record, scanId)
            }

            onComplete(id)
        }
    }

    fun deleteScanRecord(record: ScanRecordEntity) {
        viewModelScope.launch {
            repository.deleteRecord(record)
            loadAllRecords()
        }
    }

    fun searchRecords(query: String) {
        viewModelScope.launch {
            val filtered = repository.searchRecords(query)
            _scanHistory.postValue(filtered)
        }
    }

    fun getUserProfile(userId: Int) {
        viewModelScope.launch {
            val user = repository.getUserById(userId)
            _currentUser.postValue(user)
        }
    }

    fun updateUserProfile(user: UserEntity) {
        viewModelScope.launch {
            repository.updateUser(user)
            _currentUser.postValue(user)
        }
    }
}
