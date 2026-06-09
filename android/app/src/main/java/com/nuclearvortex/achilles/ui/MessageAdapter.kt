package com.nuclearvortex.achilles.ui

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.nuclearvortex.achilles.R
import com.nuclearvortex.achilles.model.Message
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MessageAdapter(private val messages: MutableList<Message> = mutableListOf()) :
    RecyclerView.Adapter<MessageAdapter.MessageViewHolder>() {

    companion object {
        private const val VIEW_TYPE_USER = 0
        private const val VIEW_TYPE_ACHILLES = 1
        private val timeFormat = SimpleDateFormat("h:mm a", Locale.getDefault())
    }

    inner class MessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val textMessage: TextView = itemView.findViewById(R.id.text_message)
        val textTimestamp: TextView = itemView.findViewById(R.id.text_timestamp)
    }

    override fun getItemViewType(position: Int): Int =
        if (messages[position].isUser) VIEW_TYPE_USER else VIEW_TYPE_ACHILLES

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MessageViewHolder {
        val layout = if (viewType == VIEW_TYPE_USER) R.layout.item_message_user else R.layout.item_message_achilles
        val view = LayoutInflater.from(parent.context).inflate(layout, parent, false)
        return MessageViewHolder(view)
    }

    override fun onBindViewHolder(holder: MessageViewHolder, position: Int) {
        val msg = messages[position]
        holder.textMessage.text = msg.text
        holder.textTimestamp.text = timeFormat.format(Date(msg.timestamp))
    }

    override fun getItemCount(): Int = messages.size

    fun addMessage(message: Message) {
        messages.add(message)
        notifyItemInserted(messages.size - 1)
    }

    fun clear() {
        messages.clear()
        notifyDataSetChanged()
    }
}
