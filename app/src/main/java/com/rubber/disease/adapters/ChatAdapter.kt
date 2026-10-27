package com.rubber.disease.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.text.HtmlCompat
import androidx.recyclerview.widget.RecyclerView
import com.rubber.disease.databinding.ItemChatMessageBinding

data class ChatMessage(
    val message: String,
    val isUser: Boolean
)

class ChatAdapter(
    private val messages: MutableList<ChatMessage>
) : RecyclerView.Adapter<ChatAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemChatMessageBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemChatMessageBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val chatMessage = messages[position]
        
        if (chatMessage.isUser) {
            holder.binding.llUserBubble.visibility = View.VISIBLE
            holder.binding.llBotBubble.visibility = View.GONE
            holder.binding.tvUserText.text = chatMessage.message
        } else {
            holder.binding.llUserBubble.visibility = View.GONE
            holder.binding.llBotBubble.visibility = View.VISIBLE
            
            // Format Markdown bold (**text**) to HTML <b>text</b> and newlines to <br/>
            val formattedHtml = formatMarkdown(chatMessage.message)
            holder.binding.tvBotText.text = HtmlCompat.fromHtml(
                formattedHtml,
                HtmlCompat.FROM_HTML_MODE_COMPACT
            )
        }
    }

    private fun formatMarkdown(text: String): String {
        // 1. Convert bold **text** to <b>text</b> across line boundaries
        var formatted = text.replace(Regex("\\*\\*(.+?)\\*\\*", RegexOption.DOT_MATCHES_ALL), "<b>$1</b>")
        // 2. Convert leading asterisk bullet points (* bullet) to bullet symbol
        formatted = formatted.replace(Regex("(?m)^\\s*\\*\\s+"), "• ")
        // 3. Convert inline italic *text* to <i>$1</i>
        formatted = formatted.replace(Regex("(?<!\\*)\\*([^*\\n]+)\\*(?!\\*)"), "<i>$1</i>")
        // 4. Strip ALL remaining asterisks unconditionally so no raw '*' can ever leak into UI
        formatted = formatted.replace("*", "")
        // 5. Convert newlines to HTML breaks
        formatted = formatted.replace("\n", "<br/>")
        return formatted
    }

    override fun getItemCount(): Int = messages.size

    fun addMessage(message: ChatMessage) {
        messages.add(message)
        notifyItemInserted(messages.size - 1)
    }
}
