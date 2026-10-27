package com.rubber.disease.data

import androidx.room.*

@Dao
interface ScanRecordDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRecord(record: ScanRecordEntity): Long

    @Delete
    suspend fun deleteRecord(record: ScanRecordEntity)

    @Query("SELECT * FROM scan_records ORDER BY id DESC")
    suspend fun getAllRecords(): List<ScanRecordEntity>

    @Query("SELECT * FROM scan_records WHERE id = :id LIMIT 1")
    suspend fun getRecordById(id: Int): ScanRecordEntity?

    @Query("SELECT * FROM scan_records WHERE diseaseName LIKE :query OR farmerName LIKE :query ORDER BY id DESC")
    suspend fun searchRecords(query: String): List<ScanRecordEntity>

    @Query("SELECT COUNT(*) FROM scan_records")
    suspend fun getRecordCount(): Int

    @Query("SELECT COUNT(*) FROM scan_records WHERE diseaseName = :diseaseName")
    suspend fun getCountForDisease(diseaseName: String): Int
}
