package com.rubber.disease.ui.fragments

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.ItemTouchHelper
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.rubber.disease.R
import com.rubber.disease.adapters.ScanRecordAdapter
import com.rubber.disease.databinding.FragmentHistoryBinding
import com.rubber.disease.viewmodels.MainViewModel

class HistoryFragment : Fragment() {

    private var _binding: FragmentHistoryBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: MainViewModel
    private lateinit var adapter: ScanRecordAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHistoryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel = ViewModelProvider(requireActivity())[MainViewModel::class.java]

        binding.toolbarHistory.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // 1. Setup Adapter and Recycler View
        adapter = ScanRecordAdapter(emptyList()) { record ->
            val bundle = Bundle().apply {
                putString("imagePath", record.imagePath)
                putLong("recordId", record.id.toLong())
            }
            findNavController().navigate(R.id.action_historyFragment_to_predictionFragment, bundle)
        }
        binding.rvHistoryRecords.layoutManager = LinearLayoutManager(context)
        binding.rvHistoryRecords.adapter = adapter

        // 2. Observe scan database list
        viewModel.scanHistory.observe(viewLifecycleOwner) { list ->
            if (list.isNullOrEmpty()) {
                binding.rvHistoryRecords.visibility = View.GONE
                binding.tvHistoryEmpty.visibility = View.VISIBLE
            } else {
                binding.rvHistoryRecords.visibility = View.VISIBLE
                binding.tvHistoryEmpty.visibility = View.GONE
                adapter.updateData(list)
            }
        }

        // 3. Search Filter Listener
        binding.etSearchHistory.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                val query = s.toString().trim()
                viewModel.searchRecords(query)
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        // 4. Swipe-to-Delete functionality
        val swipeHandler = object : ItemTouchHelper.SimpleCallback(0, ItemTouchHelper.LEFT or ItemTouchHelper.RIGHT) {
            override fun onMove(
                recyclerView: RecyclerView,
                viewHolder: RecyclerView.ViewHolder,
                target: RecyclerView.ViewHolder
            ): Boolean = false

            override fun onSwiped(viewHolder: RecyclerView.ViewHolder, direction: Int) {
                val position = viewHolder.adapterPosition
                val record = viewModel.scanHistory.value?.getOrNull(position)
                if (record != null) {
                    viewModel.deleteScanRecord(record)
                    Toast.makeText(context, "Scan report deleted.", Toast.LENGTH_SHORT).show()
                }
            }
        }
        ItemTouchHelper(swipeHandler).attachToRecyclerView(binding.rvHistoryRecords)
    }

    override fun onResume() {
        super.onResume()
        viewModel.loadAllRecords()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
