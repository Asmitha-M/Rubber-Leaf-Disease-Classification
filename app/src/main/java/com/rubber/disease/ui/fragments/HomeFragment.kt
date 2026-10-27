package com.rubber.disease.ui.fragments

import android.content.Context
import android.os.Bundle
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
import com.rubber.disease.databinding.FragmentHomeBinding
import com.rubber.disease.utils.LanguageHelper
import com.rubber.disease.viewmodels.MainViewModel

class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: MainViewModel
    private lateinit var adapter: ScanRecordAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel = ViewModelProvider(requireActivity())[MainViewModel::class.java]

        // 1. Fetch Session Info
        val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
        val farmerName = prefs.getString("farmer_name", "Farmer") ?: "Farmer"
        binding.tvFarmerName.text = farmerName

        // 2. Setup Recycler View
        adapter = ScanRecordAdapter(emptyList()) { record ->
            val bundle = Bundle().apply {
                putString("imagePath", record.imagePath)
            }
            findNavController().navigate(R.id.action_homeFragment_to_predictionFragment, bundle)
        }
        binding.rvRecentScans.layoutManager = LinearLayoutManager(context)
        binding.rvRecentScans.adapter = adapter

        // Setup Swipe-to-Delete for recent scans list
        val swipeHandler = object : ItemTouchHelper.SimpleCallback(0, ItemTouchHelper.LEFT or ItemTouchHelper.RIGHT) {
            override fun onMove(
                recyclerView: RecyclerView,
                viewHolder: RecyclerView.ViewHolder,
                target: RecyclerView.ViewHolder
            ): Boolean = false

            override fun onSwiped(viewHolder: RecyclerView.ViewHolder, direction: Int) {
                val position = viewHolder.adapterPosition
                val record = viewModel.scanHistory.value?.take(5)?.getOrNull(position)
                if (record != null) {
                    viewModel.deleteScanRecord(record)
                    Toast.makeText(context, "Scan report deleted.", Toast.LENGTH_SHORT).show()
                }
            }
        }
        ItemTouchHelper(swipeHandler).attachToRecyclerView(binding.rvRecentScans)

        // 3. Observe Scan History & Stats
        viewModel.scanHistory.observe(viewLifecycleOwner) { list ->
            if (list.isNullOrEmpty()) {
                binding.rvRecentScans.visibility = View.GONE
                binding.tvEmptyRecent.visibility = View.VISIBLE
            } else {
                binding.rvRecentScans.visibility = View.VISIBLE
                binding.tvEmptyRecent.visibility = View.GONE
                // Take top 5 recent scans for home dashboard
                adapter.updateData(list.take(5))
            }
        }

        viewModel.statistics.observe(viewLifecycleOwner) { stats ->
            var total = 0
            var healthy = 0
            stats.forEach { (disease, count) ->
                total += count
                if (disease.equals("Healthy", ignoreCase = true)) {
                    healthy += count
                }
            }
            binding.tvStatTotal.text = total.toString()
            binding.tvStatHealthy.text = healthy.toString()
            binding.tvStatDiseased.text = (total - healthy).toString()
        }

        // 4. Click Listeners for Scanning
        binding.btnCaptureImage.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_cameraFragment)
        }

        binding.btnUploadImage.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_galleryFragment)
        }

        // 5. Toolbars and Quick Menus
        binding.btnLangToggle.setOnClickListener {
            LanguageHelper.toggleLanguage(requireContext())
            requireActivity().recreate()
        }

        binding.btnOpenChatbot.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_chatbotFragment)
        }

        binding.llMenuHistory.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_historyFragment)
        }

        binding.llMenuChatbot.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_chatbotFragment)
        }

        binding.llMenuProfile.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_profileFragment)
        }

        binding.llMenuSettings.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_settingsFragment)
        }
    }

    override fun onResume() {
        super.onResume()
        // Reload history data on resume to keep stats and list updated
        viewModel.loadAllRecords()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
