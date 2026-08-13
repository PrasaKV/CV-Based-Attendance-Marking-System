async function startWebcam(videoEl) {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  videoEl.srcObject = stream;
  await videoEl.play();
  return stream;
}

function captureFrame(videoEl, canvasEl) {
  canvasEl.width = videoEl.videoWidth;
  canvasEl.height = videoEl.videoHeight;

  const ctx = canvasEl.getContext("2d");
  ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

  return canvasEl.toDataURL("image/jpeg", 0.9);
}
