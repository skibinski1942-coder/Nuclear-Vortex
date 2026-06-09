package com.nuclearvortex.achilles.model

import com.google.gson.annotations.SerializedName

data class ChatRequest(
    @SerializedName("message") val message: String,
    @SerializedName("session_id") val sessionId: String? = null
)

data class ChatResponse(
    @SerializedName("response") val response: String,
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("timestamp") val timestamp: String
)

data class StatusResponse(
    @SerializedName("status") val status: String,
    @SerializedName("version") val version: String,
    @SerializedName("capabilities") val capabilities: List<String>
)

data class Message(
    val text: String,
    val isUser: Boolean,
    val timestamp: Long = System.currentTimeMillis()
)
