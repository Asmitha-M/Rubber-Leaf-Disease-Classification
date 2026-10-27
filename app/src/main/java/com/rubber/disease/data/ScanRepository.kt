package com.rubber.disease.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ScanRepository(private val db: AppDatabase) {

    private val userDao = db.userDao()
    private val scanRecordDao = db.scanRecordDao()

    // User Operations
    suspend fun registerUser(user: UserEntity): Long = withContext(Dispatchers.IO) {
        userDao.registerUser(user)
    }

    suspend fun getUserByUsername(username: String): UserEntity? = withContext(Dispatchers.IO) {
        userDao.getUserByUsername(username)
    }

    suspend fun getUserByEmail(email: String): UserEntity? = withContext(Dispatchers.IO) {
        userDao.getUserByEmail(email)
    }

    suspend fun updateUser(user: UserEntity) = withContext(Dispatchers.IO) {
        userDao.updateUser(user)
    }

    suspend fun getUserById(userId: Int): UserEntity? = withContext(Dispatchers.IO) {
        userDao.getUserById(userId)
    }

    // Scan Record Operations
    suspend fun insertRecord(record: ScanRecordEntity): Long = withContext(Dispatchers.IO) {
        scanRecordDao.insertRecord(record)
    }

    suspend fun deleteRecord(record: ScanRecordEntity) = withContext(Dispatchers.IO) {
        scanRecordDao.deleteRecord(record)
    }

    suspend fun getAllRecords(): List<ScanRecordEntity> = withContext(Dispatchers.IO) {
        scanRecordDao.getAllRecords()
    }

    suspend fun getRecordById(id: Int): ScanRecordEntity? = withContext(Dispatchers.IO) {
        scanRecordDao.getRecordById(id)
    }

    suspend fun searchRecords(query: String): List<ScanRecordEntity> = withContext(Dispatchers.IO) {
        val searchPattern = "%$query%"
        scanRecordDao.searchRecords(searchPattern)
    }

    suspend fun getRecordCount(): Int = withContext(Dispatchers.IO) {
        scanRecordDao.getRecordCount()
    }

    suspend fun getCountForDisease(diseaseName: String): Int = withContext(Dispatchers.IO) {
        scanRecordDao.getCountForDisease(diseaseName)
    }
}
