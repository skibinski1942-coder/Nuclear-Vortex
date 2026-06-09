package com.nuclearvortex.achilles.network

import com.nuclearvortex.achilles.model.ChatRequest
import com.nuclearvortex.achilles.model.ChatResponse
import com.nuclearvortex.achilles.model.StatusResponse
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

interface AchillesApiService {
    @POST("chat")
    suspend fun chat(@Body request: ChatRequest): Response<ChatResponse>

    @GET("status")
    suspend fun getStatus(): Response<StatusResponse>
}

object AchillesApiClient {

    private var retrofit: Retrofit? = null
    private var currentBaseUrl: String = ""

    fun getInstance(baseUrl: String): AchillesApiService {
        val normalizedUrl = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        if (retrofit == null || currentBaseUrl != normalizedUrl) {
            currentBaseUrl = normalizedUrl
            retrofit = buildRetrofit(normalizedUrl)
        }
        return retrofit!!.create(AchillesApiService::class.java)
    }

    private fun buildRetrofit(baseUrl: String): Retrofit {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
}
