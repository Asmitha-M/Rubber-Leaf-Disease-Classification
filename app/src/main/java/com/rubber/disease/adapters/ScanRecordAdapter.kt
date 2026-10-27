package com.rubber.disease.adapters

import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.rubber.disease.data.ScanRecordEntity
import com.rubber.disease.databinding.ItemScanRecordBinding
import java.io.File

class ScanRecordAdapter(
    private var records: List<ScanRecordEntity>,
    private val onItemClick: (ScanRecordEntity) -> Unit
) : RecyclerView.Adapter<ScanRecordAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemScanRecordBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemScanRecordBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val record = records[position]
        val context = holder.itemView.context

        holder.binding.tvRecordDisease.text = record.diseaseName
        holder.binding.tvRecordDate.text = record.dateString
        holder.binding.tvRecordConfidence.text = String.format("Confidence: %.1f%%", record.confidence * 100)
        holder.binding.tvRecordSeverity.text = record.severityLabel

        // Set Severity Badge Color Dynamically
        val badgeColor = when (record.severityLabel) {
            "Healthy", "Healthy/Trace" -> 0xFF2E7D32.toInt() // Green
            "Mild" -> 0xFFFBC02D.toInt()         // Yellow
            "Moderate" -> 0xFFF57C00.toInt()     // Orange
            else -> 0xFFD32F2F.toInt()           // Red
        }

        val backgroundDrawable = holder.binding.tvRecordSeverity.background as? GradientDrawable
            ?: GradientDrawable().apply { cornerRadius = 8f * context.resources.displayMetrics.density }
        
        backgroundDrawable.setColor(badgeColor)
        holder.binding.tvRecordSeverity.background = backgroundDrawable

        // Load Thumbnail offline safely
        if (record.imagePath.isNotEmpty()) {
            val file = File(record.imagePath)
            if (file.exists()) {
                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                if (bitmap != null) {
                    holder.binding.ivRecordThumbnail.setImageBitmap(bitmap)
                } else {
                    holder.binding.ivRecordThumbnail.setImageResource(android.R.drawable.ic_menu_gallery)
                }
            } else {
                holder.binding.ivRecordThumbnail.setImageResource(android.R.drawable.ic_menu_gallery)
            }
        } else {
            holder.binding.ivRecordThumbnail.setImageResource(android.R.drawable.ic_menu_gallery)
        }

        holder.itemView.setOnClickListener {
            onItemClick(record)
        }
    }

    override fun getItemCount(): Int = records.size

    fun updateData(newRecords: List<ScanRecordEntity>) {
        records = newRecords
        notifyDataSetChanged()
    }
}
