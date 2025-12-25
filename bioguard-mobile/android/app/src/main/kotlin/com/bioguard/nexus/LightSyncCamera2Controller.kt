package com.bioguard.nexus

import android.content.Context
import android.graphics.ImageFormat
import android.hardware.camera2.CameraCaptureSession
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraDevice
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureRequest
import android.hardware.camera2.TotalCaptureResult
import android.media.Image
import android.media.ImageReader
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.util.Size
import android.view.Surface
import io.flutter.view.TextureRegistry
import io.flutter.plugin.common.MethodChannel
import java.nio.ByteBuffer
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit

class LightSyncCamera2Controller(
    private val context: Context,
    private val textureRegistry: TextureRegistry
) {
    private val cameraManager =
        context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
    private val openCloseLock = Semaphore(1)
    private val mainHandler = Handler(Looper.getMainLooper())

    private var backgroundThread: HandlerThread? = null
    private var backgroundHandler: Handler? = null

    private var cameraDevice: CameraDevice? = null
    private var session: CameraCaptureSession? = null
    private var reader: ImageReader? = null
    private var cameraId: String? = null
    private var previewTexture: TextureRegistry.SurfaceTextureEntry? = null
    private var previewSurface: Surface? = null
    private var previewSize: Size? = null

    private var captureInProgress = false
    private var pendingCapture: ((ByteArray?, String?) -> Unit)? = null

    private var aeLockAvailable = false
    private var awbLockAvailable = false
    private var lockApplied = false

    fun open(front: Boolean, result: MethodChannel.Result) {
        if (cameraDevice != null) {
            val size = previewSize
            result.success(
                mapOf(
                    "success" to true,
                    "textureId" to (previewTexture?.id() ?: -1L),
                    "width" to (size?.width ?: 0),
                    "height" to (size?.height ?: 0)
                )
            )
            return
        }

        startBackgroundThread()

        try {
            if (!openCloseLock.tryAcquire(2500, TimeUnit.MILLISECONDS)) {
                result.error("camera_timeout", "Camera lock timeout", null)
                return
            }
        } catch (e: InterruptedException) {
            result.error("camera_timeout", "Camera lock interrupted", null)
            return
        }

        try {
            cameraId = selectCameraId(front)
            if (cameraId == null) {
                openCloseLock.release()
                result.error("camera_not_found", "No suitable camera found", null)
                return
            }

            val characteristics = cameraManager.getCameraCharacteristics(cameraId!!)
            aeLockAvailable =
                characteristics.get(CameraCharacteristics.CONTROL_AE_LOCK_AVAILABLE) == true
            awbLockAvailable =
                characteristics.get(CameraCharacteristics.CONTROL_AWB_LOCK_AVAILABLE) == true

            val size = chooseJpegSize(characteristics)
            previewSize = size
            reader = ImageReader.newInstance(size.width, size.height, ImageFormat.JPEG, 2)
            reader?.setOnImageAvailableListener({ reader ->
                val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
                val bytes = imageToBytes(image)
                image.close()

                if (captureInProgress) {
                    captureInProgress = false
                    val callback = pendingCapture
                    pendingCapture = null
                    callback?.invoke(bytes, null)
                }
            }, backgroundHandler)

            previewTexture = textureRegistry.createSurfaceTexture()
            val surfaceTexture = previewTexture!!.surfaceTexture()
            surfaceTexture.setDefaultBufferSize(size.width, size.height)
            previewSurface = Surface(surfaceTexture)

            cameraManager.openCamera(cameraId!!, object : CameraDevice.StateCallback() {
                override fun onOpened(device: CameraDevice) {
                    openCloseLock.release()
                    cameraDevice = device
                    createSession(result)
                }

                override fun onDisconnected(device: CameraDevice) {
                    openCloseLock.release()
                    device.close()
                    cameraDevice = null
                    mainHandler.post {
                        result.error("camera_disconnected", "Camera disconnected", null)
                    }
                }

                override fun onError(device: CameraDevice, error: Int) {
                    openCloseLock.release()
                    device.close()
                    cameraDevice = null
                    mainHandler.post {
                        result.error("camera_error", "Camera error: $error", null)
                    }
                }
            }, backgroundHandler)
        } catch (e: Exception) {
            openCloseLock.release()
            result.error("camera_open_failed", e.message, null)
        }
    }

    fun captureFrame(result: MethodChannel.Result) {
        val device = cameraDevice
        val captureSession = session
        val imageReader = reader

        if (device == null || captureSession == null || imageReader == null) {
            result.error("camera_not_ready", "Camera session not ready", null)
            return
        }

        if (captureInProgress) {
            result.error("capture_in_progress", "Capture already in progress", null)
            return
        }

        captureInProgress = true
        pendingCapture = { bytes, error ->
            mainHandler.post {
                if (bytes != null) {
                    result.success(bytes)
                } else {
                    result.error("capture_failed", error ?: "Capture failed", null)
                }
            }
        }

        backgroundHandler?.postDelayed({
            if (captureInProgress) {
                captureInProgress = false
                val callback = pendingCapture
                pendingCapture = null
                callback?.invoke(null, "Capture timeout")
            }
        }, 1500)

        try {
            val requestBuilder = device.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE)
            requestBuilder.addTarget(imageReader.surface)
            requestBuilder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            requestBuilder.set(
                CaptureRequest.CONTROL_AF_MODE,
                CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE
            )
            requestBuilder.set(
                CaptureRequest.CONTROL_AE_MODE,
                CaptureRequest.CONTROL_AE_MODE_ON
            )
            if (aeLockAvailable) {
                requestBuilder.set(CaptureRequest.CONTROL_AE_LOCK, true)
            }
            requestBuilder.set(
                CaptureRequest.CONTROL_AWB_MODE,
                CaptureRequest.CONTROL_AWB_MODE_AUTO
            )
            if (awbLockAvailable) {
                requestBuilder.set(CaptureRequest.CONTROL_AWB_LOCK, true)
            }

            captureSession.capture(
                requestBuilder.build(),
                object : CameraCaptureSession.CaptureCallback() {
                    override fun onCaptureCompleted(
                        session: CameraCaptureSession,
                        request: CaptureRequest,
                        result: TotalCaptureResult
                    ) {
                        // ImageReader listener handles the bytes.
                    }
                },
                backgroundHandler
            )
        } catch (e: Exception) {
            captureInProgress = false
            pendingCapture = null
            result.error("capture_failed", e.message, null)
        }
    }

    fun close() {
        try {
            openCloseLock.acquire()
            session?.close()
            session = null
            cameraDevice?.close()
            cameraDevice = null
            reader?.close()
            reader = null
            previewSurface?.release()
            previewSurface = null
            previewTexture?.release()
            previewTexture = null
        } catch (e: InterruptedException) {
            // Ignore
        } finally {
            openCloseLock.release()
            stopBackgroundThread()
        }
    }

    private fun createSession(result: MethodChannel.Result) {
        val device = cameraDevice ?: run {
            result.error("camera_not_ready", "Camera device missing", null)
            return
        }
        val imageReader = reader ?: run {
            result.error("camera_not_ready", "ImageReader missing", null)
            return
        }
        val surface = previewSurface ?: run {
            result.error("camera_not_ready", "Preview surface missing", null)
            return
        }

        try {
            device.createCaptureSession(
                listOf(surface, imageReader.surface),
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        this@LightSyncCamera2Controller.session = session
                        try {
                            val requestBuilder =
                                device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
                            requestBuilder.addTarget(surface)
                            requestBuilder.set(
                                CaptureRequest.CONTROL_AF_MODE,
                                CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE
                            )
                            requestBuilder.set(
                                CaptureRequest.CONTROL_AE_MODE,
                                CaptureRequest.CONTROL_AE_MODE_ON
                            )
                            requestBuilder.set(
                                CaptureRequest.CONTROL_AWB_MODE,
                                CaptureRequest.CONTROL_AWB_MODE_AUTO
                            )
                            session.setRepeatingRequest(
                                requestBuilder.build(),
                                null,
                                backgroundHandler
                            )
                        } catch (e: Exception) {
                            mainHandler.post {
                                result.error("session_failed", e.message, null)
                            }
                            return
                        }

                        backgroundHandler?.postDelayed({
                            applyLocks()
                        }, 500)

                        val size = previewSize
                        mainHandler.post {
                            result.success(
                                mapOf(
                                    "success" to true,
                                    "textureId" to (previewTexture?.id() ?: -1L),
                                    "width" to (size?.width ?: 0),
                                    "height" to (size?.height ?: 0)
                                )
                            )
                        }
                    }

                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        mainHandler.post {
                            result.error("session_failed", "Capture session failed", null)
                        }
                    }
                },
                backgroundHandler
            )
        } catch (e: Exception) {
            result.error("session_failed", e.message, null)
        }
    }

    private fun applyLocks() {
        val device = cameraDevice ?: return
        val captureSession = session ?: return

        try {
            val requestBuilder = device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            requestBuilder.addTarget(reader!!.surface)
            requestBuilder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            requestBuilder.set(
                CaptureRequest.CONTROL_AF_MODE,
                CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE
            )
            requestBuilder.set(
                CaptureRequest.CONTROL_AE_MODE,
                CaptureRequest.CONTROL_AE_MODE_ON
            )
            if (aeLockAvailable) {
                requestBuilder.set(CaptureRequest.CONTROL_AE_LOCK, true)
            }
            requestBuilder.set(
                CaptureRequest.CONTROL_AWB_MODE,
                CaptureRequest.CONTROL_AWB_MODE_AUTO
            )
            if (awbLockAvailable) {
                requestBuilder.set(CaptureRequest.CONTROL_AWB_LOCK, true)
            }

            captureSession.setRepeatingRequest(
                requestBuilder.build(),
                null,
                backgroundHandler
            )
            lockApplied = true
        } catch (e: Exception) {
            lockApplied = false
        }
    }

    private fun selectCameraId(front: Boolean): String? {
        val cameraIds = cameraManager.cameraIdList
        for (id in cameraIds) {
            val characteristics = cameraManager.getCameraCharacteristics(id)
            val facing = characteristics.get(CameraCharacteristics.LENS_FACING)
            if (front && facing == CameraCharacteristics.LENS_FACING_FRONT) {
                return id
            }
            if (!front && facing == CameraCharacteristics.LENS_FACING_BACK) {
                return id
            }
        }
        return cameraIds.firstOrNull()
    }

    private fun chooseJpegSize(characteristics: CameraCharacteristics): Size {
        val map =
            characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)
        val sizes = map?.getOutputSizes(ImageFormat.JPEG)
        if (sizes == null || sizes.isEmpty()) {
            return Size(640, 480)
        }
        val sorted = sizes.sortedBy { it.width * it.height }
        return sorted.firstOrNull { it.width >= 640 && it.height >= 480 }
            ?: sorted.first()
    }

    private fun imageToBytes(image: Image): ByteArray {
        val buffer: ByteBuffer = image.planes[0].buffer
        val bytes = ByteArray(buffer.remaining())
        buffer.get(bytes)
        return bytes
    }

    private fun startBackgroundThread() {
        if (backgroundThread != null) return
        backgroundThread = HandlerThread("LightSyncCamera2")
        backgroundThread!!.start()
        backgroundHandler = Handler(backgroundThread!!.looper)
    }

    private fun stopBackgroundThread() {
        backgroundThread?.quitSafely()
        try {
            backgroundThread?.join()
        } catch (e: InterruptedException) {
            // Ignore
        } finally {
            backgroundThread = null
            backgroundHandler = null
        }
    }
}
