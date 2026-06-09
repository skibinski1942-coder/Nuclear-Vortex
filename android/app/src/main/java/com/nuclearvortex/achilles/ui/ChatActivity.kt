package com.nuclearvortex.achilles.ui

import android.os.Bundle
import android.view.MenuItem
import android.view.View
import android.view.inputmethod.EditorInfo
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.preference.PreferenceManager
import androidx.recyclerview.widget.LinearLayoutManager
import com.nuclearvortex.achilles.R
import com.nuclearvortex.achilles.databinding.ActivityChatBinding
import com.nuclearvortex.achilles.model.ChatRequest
import com.nuclearvortex.achilles.model.Message
import com.nuclearvortex.achilles.network.AchillesApiClient
import kotlinx.coroutines.launch
import java.util.UUID

class ChatActivity : AppCompatActivity() {

    private lateinit var binding: ActivityChatBinding
    private lateinit var messageAdapter: MessageAdapter
    private var sessionId: String = UUID.randomUUID().toString()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChatBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = getString(R.string.chat_title)

        messageAdapter = MessageAdapter()
        binding.recyclerMessages.apply {
            adapter = messageAdapter
            layoutManager = LinearLayoutManager(this@ChatActivity).apply {
                stackFromEnd = true
            }
        }

        binding.inputMessage.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                sendMessage()
                true
            } else false
        }

        binding.buttonSend.setOnClickListener { sendMessage() }

        // Show welcome message
        messageAdapter.addMessage(
            Message(getString(R.string.achilles_welcome), isUser = false)
        )
    }

    private fun sendMessage() {
        val text = binding.inputMessage.text?.toString()?.trim() ?: return
        if (text.isEmpty()) return

        binding.inputMessage.text?.clear()
        messageAdapter.addMessage(Message(text, isUser = true))
        scrollToBottom()

        setLoading(true)

        val prefs = PreferenceManager.getDefaultSharedPreferences(this)
        val baseUrl = prefs.getString("server_url", getString(R.string.default_server_url)) ?: getString(R.string.default_server_url)
        val api = AchillesApiClient.getInstance(baseUrl)

        lifecycleScope.launch {
            try {
                val response = api.chat(ChatRequest(message = text, sessionId = sessionId))
                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        sessionId = body.sessionId
                        messageAdapter.addMessage(Message(body.response, isUser = false))
                    } else {
                        showError(getString(R.string.error_empty_response))
                    }
                } else {
                    showError(getString(R.string.error_server, response.code()))
                }
            } catch (e: Exception) {
                showError(getString(R.string.error_connection))
            } finally {
                setLoading(false)
                scrollToBottom()
            }
        }
    }

    private fun setLoading(loading: Boolean) {
        binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
        binding.buttonSend.isEnabled = !loading
        binding.inputMessage.isEnabled = !loading
    }

    private fun showError(message: String) {
        messageAdapter.addMessage(Message("⚠ $message", isUser = false))
    }

    private fun scrollToBottom() {
        binding.recyclerMessages.post {
            val count = messageAdapter.itemCount
            if (count > 0) binding.recyclerMessages.smoothScrollToPosition(count - 1)
        }
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == android.R.id.home) {
            onBackPressedDispatcher.onBackPressed()
            return true
        }
        return super.onOptionsItemSelected(item)
    }
}
