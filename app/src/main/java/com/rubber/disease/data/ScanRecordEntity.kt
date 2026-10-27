package com.rubber.disease.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "scan_records")
data class ScanRecordEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val farmerName: String,
    val diseaseName: String,
    val confidence: Float,
    val severityLabel: String,
    val severityPercentage: Float,
    val dateString: String,
    val imagePath: String,
    val heatmapPath: String,
    val notes: String = ""
)
