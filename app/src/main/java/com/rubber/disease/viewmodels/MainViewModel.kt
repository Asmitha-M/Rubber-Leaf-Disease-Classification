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
import kotlinx.coroutines.launch
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
            val user = repository.getUserByUsername(username)
            if (user != null && user.passwordHash == hashPassword(passwordPlain)) {
                _currentUser.postValue(user)
                onResult(user)
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
